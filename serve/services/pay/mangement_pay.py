"""
公钥模式支付宝客户端（异步版）
基于 alipay-sdk-python 3.7.1018，扩展为异步 HTTP 通信。

典型用法（从 MongoDB 配置构建）：
    client = await AlipayClient.from_db(mongo)
    response = await client.execute(request)
    await client.close()
"""

import datetime
import json
import uuid
from urllib.parse import quote_plus

import httpx

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.constant.ParamConstants import *
from alipay.aop.api.constant.CommonConstants import (
    PYTHON_VERSION_3,
    ALIPAY_SDK_PYTHON_VERSION,
    PATTERN_RESPONSE_BEGIN,
    PATTERN_RESPONSE_SIGN_BEGIN,
    PATTERN_RESPONSE_ENCRYPT_BEGIN,
    PATTERN_RESPONSE_SIGN_ENCRYPT_BEGIN,
)
from alipay.aop.api.util.SignatureUtils import (
    get_sign_content,
    sign_with_rsa,
    sign_with_rsa2,
    verify_with_rsa,
)
from alipay.aop.api.util.CommonUtils import has_value
from alipay.aop.api.util.EncryptUtils import encrypt_content, decrypt_content
from alipay.aop.api.exception.Exception import RequestException, ResponseException

from .pay_certificate_management import clean_key_str


def _url_encode(params: dict, charset: str) -> str:
    parts: list[str] = []
    for k, v in params.items():
        value = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
        parts.append(f"{k}={quote_plus(value, encoding=charset)}")
    return "&".join(parts)


class AlipayClient:
    """
    公钥模式支付宝异步客户端

    基于原生 DefaultAlipayClient 的签名 / 验签逻辑，
    使用 httpx.AsyncClient 进行非阻塞 HTTP 通信。
    """

    def __init__(self, config: AlipayClientConfig, logger=None):
        self._config = config
        self._logger = logger
        self._http = httpx.AsyncClient(timeout=config.timeout)
        self._notify_url: str = ""
        self._return_url: str = ""

    # ──────────────────── 从 MongoDB 构建 ────────────────────

    @classmethod
    async def from_db(cls, mongo, logger=None) -> "AlipayClient":
        """
        从 MongoDB pay_config 集合读取配置并构建客户端。
        """
        doc = await mongo.find_one("pay_config", {"is_active": True})
        if not doc:
            raise RequestException("平台支付配置未录入或未启用")

        config = AlipayClientConfig()
        config.server_url = doc.get("server_url", "https://openapi.alipay.com/gateway.do")
        config.app_id = doc["app_id"]
        config.sign_type = doc.get("sign_type", "RSA2")
        config.app_private_key = clean_key_str(doc["app_private_key"])
        config.alipay_public_key = clean_key_str(doc["alipay_public_key"])

        instance = cls(config, logger=logger)
        instance._notify_url = doc.get("notify_url", "")
        instance._return_url = doc.get("return_url", "")
        return instance

    @classmethod
    def from_config(
        cls,
        app_id: str,
        app_private_key: str,
        alipay_public_key: str,
        server_url: str = "https://openapi.alipay.com/gateway.do",
        sign_type: str = "RSA2",
        notify_url: str = "",
        return_url: str = "",
        logger=None,
    ) -> "AlipayClient":
        """从参数直接构建客户端（验证场景）。"""
        config = AlipayClientConfig()
        config.server_url = server_url
        config.app_id = app_id
        config.sign_type = sign_type
        config.app_private_key = clean_key_str(app_private_key)
        config.alipay_public_key = clean_key_str(alipay_public_key)

        instance = cls(config, logger=logger)
        instance._notify_url = notify_url
        instance._return_url = return_url
        return instance

    # ──────────────────── 生命周期 ────────────────────

    async def close(self):
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()

    # ──────────────────── 公共参数 ────────────────────

    def _get_common_params(self, params: dict) -> dict:
        common = {
            P_TIMESTAMP: params[P_TIMESTAMP],
            P_APP_ID: self._config.app_id,
            P_METHOD: params[P_METHOD],
            P_CHARSET: self._config.charset,
            P_FORMAT: self._config.format,
            P_VERSION: params[P_VERSION],
            P_SIGN_TYPE: self._config.sign_type,
        }
        if self._config.encrypt_type:
            common[P_ENCRYPT_TYPE] = self._config.encrypt_type
        for key in (P_APP_AUTH_TOKEN, P_AUTH_TOKEN, P_NOTIFY_URL, P_RETURN_URL):
            if has_value(params, key):
                common[key] = params[key]
        return common

    @staticmethod
    def _remove_common_params(params: dict):
        for k in COMMON_PARAM_KEYS:
            params.pop(k, None)

    # ──────────────────── 请求准备 ────────────────────

    def _prepare_request_params(self, request, req_uuid: str):
        params = request.get_params()

        if P_BIZ_CONTENT in params:
            if self._config.encrypt_type and self._config.encrypt_key:
                params[P_BIZ_CONTENT] = encrypt_content(
                    params[P_BIZ_CONTENT],
                    self._config.encrypt_type,
                    self._config.encrypt_key,
                    self._config.charset,
                )
            elif request.need_encrypt:
                raise RequestException(
                    "接口" + params[P_METHOD] + "必须使用 encrypt_type、encrypt_key 加密"
                )

        params[P_TIMESTAMP] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        common_params = self._get_common_params(params)

        all_params = {**params, **common_params}
        sign_content = get_sign_content(all_params)

        sign = ""
        if not self._config.skip_sign:
            try:
                if self._config.sign_type == "RSA2":
                    sign = sign_with_rsa2(
                        self._config.app_private_key, sign_content, self._config.charset
                    )
                else:
                    sign = sign_with_rsa(
                        self._config.app_private_key, sign_content, self._config.charset
                    )
            except Exception as e:
                raise RequestException(f"[{req_uuid}]request sign failed. {e}")
            common_params[P_SIGN] = sign

        self._remove_common_params(params)

        if self._logger:
            log_url = self._config.server_url + "?" + sign_content + "&sign=" + sign
            self._logger.info(f"[{req_uuid}]request:{log_url}")

        return common_params, params

    def _prepare_request(self, request, req_uuid: str):
        common_params, params = self._prepare_request_params(request, req_uuid)
        query_string = _url_encode(common_params, self._config.charset)
        return query_string, params

    def _prepare_sdk_request(self, request, req_uuid: str):
        common_params, params = self._prepare_request_params(request, req_uuid)
        return _url_encode({**common_params, **params}, self._config.charset)

    # ──────────────────── 异步 HTTP 请求 ────────────────────

    async def _async_post(self, query_string: str, params: dict, req_uuid: str) -> bytes:
        url = f"{self._config.server_url}?{query_string}"
        headers = {
            "Content-Type": f"application/x-www-form-urlencoded;charset={self._config.charset}",
            "Cache-Control": "no-cache",
            "Connection": "Keep-Alive",
            "User-Agent": ALIPAY_SDK_PYTHON_VERSION,
            "log-uuid": req_uuid,
        }
        body = _url_encode(params, self._config.charset) if params else ""
        try:
            resp = await self._http.post(url, content=body, headers=headers)
            resp.raise_for_status()
            return resp.content
        except httpx.HTTPStatusError as e:
            raise ResponseException(
                f"[{req_uuid}]invalid http status {e.response.status_code}"
            )
        except Exception as e:
            raise RequestException(f"[{req_uuid}]post request failed. {e}")

    async def _async_multipart_post(
        self, query_string: str, params: dict, multipart_params: dict, req_uuid: str
    ) -> bytes:
        url = f"{self._config.server_url}?{query_string}"
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "Keep-Alive",
            "User-Agent": ALIPAY_SDK_PYTHON_VERSION,
            "log-uuid": req_uuid,
        }
        data = {}
        for k, v in params.items():
            data[k] = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)

        files = {}
        for key, file_item in multipart_params.items():
            if file_item:
                files[key] = (
                    file_item.get_file_name(),
                    file_item.get_file_content(),
                    getattr(file_item, "get_mime_type", lambda: "application/octet-stream")(),
                )

        try:
            resp = await self._http.post(url, data=data, files=files, headers=headers)
            resp.raise_for_status()
            return resp.content
        except httpx.HTTPStatusError as e:
            raise ResponseException(
                f"[{req_uuid}]invalid http status {e.response.status_code}"
            )
        except Exception as e:
            raise RequestException(f"[{req_uuid}]multipart post failed. {e}")

    # ──────────────────── 响应解析与验签 ────────────────────

    def _parse_response(self, raw: bytes, req_uuid: str) -> str:
        response_str = raw.decode(self._config.charset) if PYTHON_VERSION_3 else raw
        if self._logger:
            self._logger.info(f"[{req_uuid}]response:{response_str}")

        if self._config.skip_sign:
            return self._parse_unsigned_response(response_str, req_uuid)

        response_content = None
        sign = None
        has_encrypted = False

        if self._config.encrypt_type and self._config.encrypt_key:
            em1 = PATTERN_RESPONSE_ENCRYPT_BEGIN.search(response_str)
            em2 = PATTERN_RESPONSE_SIGN_ENCRYPT_BEGIN.search(response_str)
            if em1 and em2:
                has_encrypted = True
                sign_start, sign_end = em2.start(), em2.end()
                m = PATTERN_RESPONSE_SIGN_BEGIN.search(response_str, pos=em2.end())
                while m:
                    sign_start, sign_end = m.start(), m.end()
                    m = PATTERN_RESPONSE_SIGN_BEGIN.search(response_str, pos=m.end())
                response_content = response_str[em1.end() - 1 : sign_start + 1]
                if PYTHON_VERSION_3:
                    response_content = response_content.encode(self._config.charset)
                sign = response_str[sign_end : response_str.find('"', sign_end)]

        if not response_content:
            m1 = PATTERN_RESPONSE_BEGIN.search(response_str)
            m2 = PATTERN_RESPONSE_SIGN_BEGIN.search(response_str)
            if not m1 or not m2:
                raise ResponseException(
                    f"[{req_uuid}]response shape maybe illegal. {response_str}"
                )
            sign_start, sign_end = m2.start(), m2.end()
            m = PATTERN_RESPONSE_SIGN_BEGIN.search(response_str, pos=m2.end())
            while m:
                sign_start, sign_end = m.start(), m.end()
                m = PATTERN_RESPONSE_SIGN_BEGIN.search(response_str, pos=m.end())
            response_content = response_str[m1.end() - 1 : sign_start + 1]
            if PYTHON_VERSION_3:
                response_content = response_content.encode(self._config.charset)
            sign = response_str[sign_end : response_str.find('"', sign_end)]

        try:
            verify_res = verify_with_rsa(
                self._config.alipay_public_key, response_content, sign
            )
        except Exception as e:
            raise ResponseException(
                f"[{req_uuid}]response sign verify failed. {e} {response_str}"
            )
        if not verify_res:
            raise ResponseException(
                f"[{req_uuid}]response sign verify failed. {response_str}"
            )

        response_content = response_content.decode(self._config.charset)
        if has_encrypted:
            response_content = decrypt_content(
                response_content[1:-1],
                self._config.encrypt_type,
                self._config.encrypt_key,
                self._config.charset,
            )
        return response_content

    def _parse_unsigned_response(self, response_str: str, req_uuid: str) -> str:
        m1 = PATTERN_RESPONSE_BEGIN.search(response_str)
        em1 = PATTERN_RESPONSE_ENCRYPT_BEGIN.search(response_str)
        if not m1 and not em1:
            raise ResponseException(
                f"[{req_uuid}]response shape maybe illegal. {response_str}"
            )

        has_encrypted = False
        if m1:
            begin = m1.end() - 1
            end = self._extract_json_end(response_str, begin)
        else:
            begin = em1.end() - 1
            end = self._extract_base64_end(response_str, begin)
            has_encrypted = True

        if begin >= end:
            return response_str

        content = response_str[begin:end]
        if PYTHON_VERSION_3:
            content = content.encode(self._config.charset).decode(self._config.charset)
        if has_encrypted and self._config.encrypt_type and self._config.encrypt_key:
            content = decrypt_content(
                content[1:-1],
                self._config.encrypt_type,
                self._config.encrypt_key,
                self._config.charset,
            )
        return content

    # ──────────────────── JSON / Base64 边界提取 ────────────────────

    @staticmethod
    def _extract_json_end(s: str, begin: int) -> int:
        braces: list[str] = []
        in_quotes = False
        esc_count = 0
        for i in range(begin, len(s)):
            ch = s[i]
            if ch == '"' and esc_count % 2 == 0:
                in_quotes = not in_quotes
            elif ch == "{" and not in_quotes:
                braces.append("{")
            elif ch == "}" and not in_quotes:
                braces.pop()
                if not braces:
                    return i + 1
            esc_count = esc_count + 1 if ch == "\\" else 0
        return len(s)

    @staticmethod
    def _extract_base64_end(s: str, begin: int) -> int:
        for i in range(begin, len(s)):
            if s[i] == '"' and i != begin:
                return i + 1
        return len(s)

    # ──────────────────── Form 表单构建 ────────────────────

    @staticmethod
    def _build_form(url: str, params: dict) -> str:
        form = f'<form name="punchout_form" method="post" action="{url}">\n'
        for k, v in params.items():
            if not v:
                continue
            form += f'<input type="hidden" name="{k}" value="{v.replace(chr(34), "&quot;")}">\n'
        form += '<input type="submit" value="立即支付" style="display:none" >\n'
        form += "</form>\n"
        form += "<script>document.forms[0].submit();</script>"
        return form

    # ──────────────────── 公开异步接口 ────────────────────

    async def execute(self, request) -> str:
        req_uuid = str(uuid.uuid1())
        query_string, params = self._prepare_request(request, req_uuid)
        multipart_params = request.get_multipart_params()

        if multipart_params and len(multipart_params) > 0:
            raw = await self._async_multipart_post(
                query_string, params, multipart_params, req_uuid
            )
        else:
            raw = await self._async_post(query_string, params, req_uuid)

        return self._parse_response(raw, req_uuid)

    async def page_execute(self, request, http_method: str = "POST") -> str:
        req_uuid = str(uuid.uuid1())
        url = self._config.server_url
        pos = url.find("?")
        if pos >= 0:
            url = url[:pos]

        query_string, params = self._prepare_request(request, req_uuid)
        if http_method == "GET":
            return url + "?" + query_string + "&" + _url_encode(params, self._config.charset)
        return self._build_form(url + "?" + query_string, params)

    async def sdk_execute(self, request) -> str:
        req_uuid = str(uuid.uuid1())
        return self._prepare_sdk_request(request, req_uuid)

    async def connectivity_test(self) -> dict:
        """
        向支付宝网关发起一次轻量级 API 调用（查询不存在的交易），
        用于验证 APPID + 私钥 + 公钥 + 网关地址 整条链路是否畅通。
        """
        from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest

        request = AlipayTradeQueryRequest()
        request.biz_content = {"out_trade_no": "__connectivity_test__"}

        try:
            raw = await self.execute(request)
            result = json.loads(raw) if isinstance(raw, str) else raw
            code = result.get("code", "")
            sub_code = result.get("sub_code", "")
            sub_msg = result.get("sub_msg", "")

            if code == "40004" and sub_code == "ACQ.TRADE_NOT_EXIST":
                return {"ok": True, "msg": "网关连通性验证通过，签名认证正常"}
            if code == "10000":
                return {"ok": True, "msg": "网关连通性验证通过"}

            auth_errors = {
                "isv.invalid-signature", "isv.invalid-app-id",
                "isv.missing-signature", "isp.unknow-error",
            }
            if sub_code in auth_errors:
                return {"ok": False, "msg": f"认证失败: {sub_msg}", "detail": result}

            return {"ok": True, "msg": f"网关已响应（{sub_code}: {sub_msg}），签名认证正常"}

        except ResponseException as e:
            return {"ok": False, "msg": f"网关响应异常: {e}"}
        except RequestException as e:
            return {"ok": False, "msg": f"请求发送失败: {e}"}
        except Exception as e:
            return {"ok": False, "msg": f"连通性测试异常: {e}"}
