"""
支付宝公钥模式 — 密钥工具

提供应用私钥 / 支付宝公钥的格式清洗与基本校验，
确保写入数据库前密钥内容合法可用。

重要：alipay-sdk-python 内部使用 rsa.PrivateKey.load_pkcs1()，
只接受 PKCS#1 格式私钥。本模块会自动将 PKCS#8 转为 PKCS#1。
"""

import base64
import textwrap

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def _strip_to_base64(raw: str) -> str:
    """去除 PEM 头尾、BOM、换行、空格，返回纯 Base64 字符串。"""
    s = raw.strip()
    if s.startswith("\ufeff"):
        s = s[1:]
    lines = s.splitlines()
    lines = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("-----")]
    return "".join(lines)


def _load_private_key(b64: str):
    """从纯 Base64 加载私钥对象，自动尝试 PKCS#8 和 PKCS#1 两种格式。"""
    wrapped = "\n".join(textwrap.wrap(b64, 64))
    for tag in ("RSA PRIVATE KEY", "PRIVATE KEY"):
        pem = f"-----BEGIN {tag}-----\n{wrapped}\n-----END {tag}-----\n".encode()
        try:
            return serialization.load_pem_private_key(pem, password=None, backend=default_backend())
        except Exception:
            continue
    raise ValueError("无法解析私钥，请检查格式")


def clean_key_str(raw: str) -> str:
    """
    清洗密钥字符串，返回纯 Base64。
    如果是私钥且为 PKCS#8 格式，自动转换为 PKCS#1（SDK 要求）。
    """
    b64 = _strip_to_base64(raw)
    if not b64:
        return b64

    try:
        der = base64.b64decode(b64)
    except Exception:
        return b64

    # 检测是否为 PKCS#8 私钥（ASN.1 开头特征：SEQUENCE > INTEGER(0) > SEQUENCE）
    # PKCS#1 私钥以 02 01 00（INTEGER version=0）开头
    # PKCS#8 私钥以 30（SEQUENCE）> 02 01 00 > 30（SEQUENCE AlgorithmIdentifier）开头
    is_private = False
    is_pkcs8 = False
    if len(der) > 4 and der[0] == 0x30:
        # 跳过外层 SEQUENCE 的 tag+length 找到第一个内容字节
        offset = 2
        if der[1] & 0x80:
            offset = 2 + (der[1] & 0x7F)
        if offset < len(der) and der[offset] == 0x02:
            is_private = True
            # PKCS#8: version(0) 后面紧跟 SEQUENCE (0x30)，PKCS#1: 后面紧跟 INTEGER (0x02)
            # 跳过 version INTEGER
            int_len_offset = offset + 1
            if int_len_offset < len(der):
                int_len = der[int_len_offset]
                next_tag_offset = int_len_offset + 1 + int_len
                if next_tag_offset < len(der) and der[next_tag_offset] == 0x30:
                    is_pkcs8 = True

    if is_private and is_pkcs8:
        try:
            key = _load_private_key(b64)
            pkcs1_der = key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
            return base64.b64encode(pkcs1_der).decode("ascii")
        except Exception:
            pass

    return b64


def validate_private_key(key_str: str) -> bool:
    """校验应用私钥是否为合法 RSA 密钥。"""
    b64 = _strip_to_base64(key_str)
    try:
        base64.b64decode(b64)
    except Exception:
        return False

    try:
        _load_private_key(b64)
        return True
    except Exception:
        return False


def validate_public_key(key_str: str) -> bool:
    """校验支付宝公钥是否为合法 RSA 公钥。"""
    b64 = _strip_to_base64(key_str)
    try:
        base64.b64decode(b64)
    except Exception:
        return False

    wrapped = "\n".join(textwrap.wrap(b64, 64))
    for tag in ("PUBLIC KEY", "RSA PUBLIC KEY"):
        pem = f"-----BEGIN {tag}-----\n{wrapped}\n-----END {tag}-----\n".encode()
        try:
            serialization.load_pem_public_key(pem, backend=default_backend())
            return True
        except Exception:
            continue
    return False
