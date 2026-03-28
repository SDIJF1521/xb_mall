from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.pay.pay_certificate_management import (
    clean_key_str, validate_private_key, validate_public_key,
)
from services.pay.mangement_pay import AlipayClient
from data.data_mods import SellerPayConfigSave
from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()

SELLER_PAY_CONFIG_COLLECTION = "seller_pay_config"


async def _verify_seller(token: str, redis: RedisClient, db):
    """校验卖家 Token 并返回 (ok, msg, station)。"""
    verify = VerifyDuterToken(token, redis)
    token_data = await verify.token_data()
    if not token_data:
        return False, "Token 无效", None

    sql_data = await execute_db_query(
        db, "SELECT user FROM seller_sing WHERE user = %s", (token_data.get("user"),)
    )
    result = await verify.verify_token(sql_data=sql_data)
    if not result[0]:
        return False, "身份验证失败", None

    return True, "ok", result[1]


# ────────────────── 保存 / 更新卖家支付配置 ──────────────────

@router.post("/buyer_pay_config")
async def save_seller_pay_config(
    data: SellerPayConfigSave,
    access_token: str = Header(..., alias="Access-Token"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongo: MongoDBClient = Depends(get_mongodb_client),
):
    """保存卖家端支付配置（公钥模式，按店铺隔离）。"""
    try:
        ok, msg, station = await _verify_seller(access_token, redis, db)
        if not ok:
            return {"current": False, "msg": msg}

        if not validate_private_key(data.app_private_key):
            return {"current": False, "msg": "应用私钥格式无效，请检查后重试"}
        if not validate_public_key(data.alipay_public_key):
            return {"current": False, "msg": "支付宝公钥格式无效，请检查后重试"}

        doc = {
            "mall_id": data.stroe_id,
            "app_id": data.app_id.strip(),
            "server_url": data.server_url,
            "sign_type": data.sign_type,
            "notify_url": data.notify_url,
            "return_url": data.return_url,
            "app_private_key": clean_key_str(data.app_private_key),
            "alipay_public_key": clean_key_str(data.alipay_public_key),
            "is_active": True,
            "updated_at": datetime.now(),
        }

        existing = await mongo.find_one(
            SELLER_PAY_CONFIG_COLLECTION, {"mall_id": data.stroe_id, "is_active": True}
        )
        if existing:
            await mongo.update_one(
                SELLER_PAY_CONFIG_COLLECTION,
                {"_id": ObjectId(existing["_id"])},
                {"$set": doc},
            )
        else:
            doc["created_at"] = datetime.now()
            await mongo.insert_one(SELLER_PAY_CONFIG_COLLECTION, doc)

        return {"current": True, "msg": "支付配置保存成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────── 查询卖家当前支付配置（脱敏） ──────────────────

@router.get("/buyer_pay_config")
async def get_seller_pay_config(
    stroe_id: int,
    access_token: str = Header(..., alias="Access-Token"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongo: MongoDBClient = Depends(get_mongodb_client),
):
    """获取卖家端支付配置，私钥脱敏。"""
    try:
        ok, msg, station = await _verify_seller(access_token, redis, db)
        if not ok:
            return {"current": False, "msg": msg}

        doc = await mongo.find_one(
            SELLER_PAY_CONFIG_COLLECTION, {"mall_id": stroe_id, "is_active": True}
        )
        if not doc:
            return {"current": True, "msg": "ok", "data": None}

        priv_key = doc.get("app_private_key", "")
        pub_key = doc.get("alipay_public_key", "")

        return {
            "current": True,
            "msg": "ok",
            "data": {
                "id": str(doc.get("_id")),
                "mall_id": doc.get("mall_id"),
                "app_id": doc.get("app_id", ""),
                "server_url": doc.get("server_url", ""),
                "sign_type": doc.get("sign_type", ""),
                "notify_url": doc.get("notify_url", ""),
                "return_url": doc.get("return_url", ""),
                "is_active": bool(doc.get("is_active")),
                "has_private_key": bool(priv_key),
                "has_public_key": bool(pub_key),
                "private_key_preview": priv_key[:16] + "******" if len(priv_key) > 16 else "******",
                "public_key_preview": pub_key[:32] + "..." if len(pub_key) > 32 else pub_key,
                "created_at": str(doc.get("created_at")) if doc.get("created_at") else None,
                "updated_at": str(doc.get("updated_at")) if doc.get("updated_at") else None,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────── 验证卖家支付配置有效性（连通性测试） ──────────────────

@router.post("/buyer_pay_config/verify")
async def verify_seller_pay_config(
    stroe_id: int,
    access_token: str = Header(..., alias="Access-Token"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongo: MongoDBClient = Depends(get_mongodb_client),
):
    """校验卖家端密钥格式并向支付宝网关发起连通性测试。"""
    try:
        ok, msg, station = await _verify_seller(access_token, redis, db)
        if not ok:
            return {"current": False, "msg": msg}

        doc = await mongo.find_one(
            SELLER_PAY_CONFIG_COLLECTION, {"mall_id": stroe_id, "is_active": True}
        )
        if not doc:
            return {"current": False, "msg": "暂无支付配置"}

        priv_key = doc.get("app_private_key", "")
        pub_key = doc.get("alipay_public_key", "")

        issues: list[str] = []
        if not validate_private_key(priv_key):
            issues.append("应用私钥格式无效")
        if not validate_public_key(pub_key):
            issues.append("支付宝公钥格式无效")

        if issues:
            return {"current": True, "valid": False, "msg": "；".join(issues)}

        try:
            client = AlipayClient.from_config(
                app_id=doc.get("app_id", ""),
                app_private_key=priv_key,
                alipay_public_key=pub_key,
                server_url=doc.get("server_url", "https://openapi.alipay.com/gateway.do"),
                sign_type=doc.get("sign_type", "RSA2"),
            )
            async with client:
                connectivity = await client.connectivity_test()
        except Exception as e:
            return {"current": True, "valid": False, "msg": f"连通性测试失败: {e}"}

        return {
            "current": True,
            "valid": connectivity["ok"],
            "msg": connectivity["msg"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
