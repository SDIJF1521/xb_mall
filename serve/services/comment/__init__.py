"""
商品评论服务层
- 发布评论：校验买家是否购买过该商品且已确认收货，每个订单只能评论一次
- 评论支持文字 + 图片
- 用户管理自己的评论（查看、删除）
- 卖家回复评论
- 按好评/中评/差评筛选
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId

from data.sql_client_pool import DatabasePool
from data.redis_client import RedisClient
from data.mongodb_client import MongoDBClient
from data.file_client import read_file_base64_with_cache
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

COMMENT_IMG_DIR = "./comment_img"
COMMENT_COLLECTION = "commodity_comment"

RATING_FILTER = {
    "good": {"$gte": 4},
    "average": {"$eq": 3},
    "bad": {"$lte": 2},
}


class CommentService:

    def __init__(self, db: DatabasePool, redis: RedisClient, mongo: MongoDBClient):
        self.db = db
        self.redis = redis
        self.mongo = mongo
        self.cache = CacheService(redis)

    # ════════════════════ 批量获取用户头像 ════════════════════

    async def _batch_fetch_avatars(self, usernames: list[str]) -> dict[str, str]:
        """
        批量查询用户头像，返回 {username: base64_str} 映射。
        头像来源于 personal_details 表的 HeadPortrait 字段（文件路径），
        读取后转为 base64 返回，保持与 userinfo 接口一致。
        """
        if not usernames:
            return {}
        unique_names = list(set(usernames))
        placeholders = ",".join(["%s"] * len(unique_names))
        rows = await self.db.execute_query(
            f"SELECT user, HeadPortrait FROM personal_details WHERE user IN ({placeholders})",
            tuple(unique_names),
        )
        avatar_map: dict[str, str] = {}
        if not rows:
            return avatar_map
        for user, head_portrait in rows:
            if head_portrait:
                try:
                    b64 = await read_file_base64_with_cache(head_portrait, self.redis)
                    avatar_map[user] = b64
                except Exception as e:
                    logger.warning("读取用户 %s 头像失败: %s", user, e)
        return avatar_map

    # ════════════════════ 购买与收货校验 ════════════════════

    async def _check_purchase_and_received(
        self, username: str, shopping_id: int, mall_id: int
    ) -> dict:
        """
        校验用户是否购买过该商品且已确认收货。
        返回 {"ok": True, "order_no": "...", ...} 或 {"ok": False, "msg": "..."}
        """
        rows = await self.db.execute_query(
            """SELECT o.order_no, o.status
               FROM orders o
               JOIN order_items oi ON oi.order_no = o.order_no
               WHERE o.user = %s
                 AND oi.shopping_id = %s
                 AND oi.mall_id = %s
               ORDER BY o.created_at DESC""",
            (username, shopping_id, mall_id),
        )
        if not rows:
            return {"ok": False, "msg": "您尚未购买过该商品，无法评论"}

        received_order = None
        for order_no, status in rows:
            if status == "received":
                already = await self.mongo.find_one(
                    COMMENT_COLLECTION,
                    {"order_no": order_no, "username": username},
                )
                if not already:
                    received_order = order_no
                    break

        if not received_order:
            has_any_received = any(s == "received" for _, s in rows)
            if not has_any_received:
                return {"ok": False, "msg": "请先确认收货后再评论"}
            return {"ok": False, "msg": "您已对所有已收货订单评论过了"}

        return {"ok": True, "order_no": received_order}

    # ════════════════════ 发布评论 ════════════════════

    async def create_comment(
        self,
        username: str,
        shopping_id: int,
        mall_id: int,
        rating: int,
        content: str,
        images: list[bytes] | None = None,
    ) -> dict:
        check = await self._check_purchase_and_received(username, shopping_id, mall_id)
        if not check["ok"]:
            return {"success": False, "msg": check["msg"]}

        order_no = check["order_no"]

        image_paths: list[str] = []
        if images:
            os.makedirs(COMMENT_IMG_DIR, exist_ok=True)
            for img_bytes in images:
                filename = f"{uuid.uuid4().hex}.jpg"
                filepath = os.path.join(COMMENT_IMG_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                image_paths.append(filepath)

        now = datetime.now().isoformat()
        doc = {
            "shopping_id": shopping_id,
            "mall_id": mall_id,
            "order_no": order_no,
            "username": username,
            "rating": rating,
            "content": content.strip(),
            "images": image_paths,
            "seller_reply": None,
            "created_at": now,
            "updated_at": now,
        }

        await self.mongo.insert_one(COMMENT_COLLECTION, doc)
        await self._invalidate_comment_cache(mall_id, shopping_id)

        return {"success": True, "msg": "评论发布成功"}

    # ════════════════════ 获取商品评论列表（公开） ════════════════════

    async def get_comment_list(
        self,
        shopping_id: int,
        mall_id: int,
        page: int = 1,
        page_size: int = 10,
        rating_type: str | None = None,
    ) -> dict:
        cache_key = self.cache._make_key(
            "comment:list", mall_id, shopping_id, page, rating_type or "all"
        )
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        query_filter: dict = {"mall_id": mall_id, "shopping_id": shopping_id}
        if rating_type and rating_type in RATING_FILTER:
            query_filter["rating"] = RATING_FILTER[rating_type]

        total = await self.mongo.count_documents(COMMENT_COLLECTION, query_filter)
        skip = (page - 1) * page_size

        comments_raw = await self.mongo.find_many(
            COMMENT_COLLECTION,
            query_filter,
            limit=page_size,
            skip=skip,
            sort=[("created_at", -1)],
        )

        all_filter = {"mall_id": mall_id, "shopping_id": shopping_id}
        good_count = await self.mongo.count_documents(
            COMMENT_COLLECTION, {**all_filter, "rating": RATING_FILTER["good"]}
        )
        average_count = await self.mongo.count_documents(
            COMMENT_COLLECTION, {**all_filter, "rating": RATING_FILTER["average"]}
        )
        bad_count = await self.mongo.count_documents(
            COMMENT_COLLECTION, {**all_filter, "rating": RATING_FILTER["bad"]}
        )

        usernames = [c.get("username", "") for c in (comments_raw or []) if c.get("username")]
        avatar_map = await self._batch_fetch_avatars(usernames)

        data = []
        for c in comments_raw or []:
            uname = c.get("username", "匿名用户")
            item = {
                "id": str(c.get("_id", "")),
                "username": uname,
                "avatar": avatar_map.get(uname, ""),
                "rating": c.get("rating", 5),
                "content": c.get("content", ""),
                "images": c.get("images", []),
                "created_at": c.get("created_at", ""),
                "seller_reply": c.get("seller_reply"),
            }
            data.append(item)

        result = {
            "code": 200,
            "success": True,
            "msg": "成功",
            "total": total,
            "page": page,
            "page_size": page_size,
            "statistics": {
                "good": good_count,
                "average": average_count,
                "bad": bad_count,
                "total": good_count + average_count + bad_count,
            },
            "data": data,
        }

        await self.cache.set(cache_key, result, expire=60)
        return result

    # ════════════════════ 用户评论管理 ════════════════════

    async def get_user_comments(
        self, username: str, page: int = 1, page_size: int = 10
    ) -> dict:
        query_filter = {"username": username}
        total = await self.mongo.count_documents(COMMENT_COLLECTION, query_filter)
        skip = (page - 1) * page_size

        comments_raw = await self.mongo.find_many(
            COMMENT_COLLECTION,
            query_filter,
            limit=page_size,
            skip=skip,
            sort=[("created_at", -1)],
        )

        avatar_map = await self._batch_fetch_avatars([username])

        data = []
        for c in comments_raw or []:
            data.append({
                "id": str(c.get("_id", "")),
                "shopping_id": c.get("shopping_id"),
                "mall_id": c.get("mall_id"),
                "order_no": c.get("order_no", ""),
                "avatar": avatar_map.get(username, ""),
                "rating": c.get("rating", 5),
                "content": c.get("content", ""),
                "images": c.get("images", []),
                "created_at": c.get("created_at", ""),
                "updated_at": c.get("updated_at", ""),
                "seller_reply": c.get("seller_reply"),
            })

        return {
            "code": 200,
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": data,
        }

    async def delete_comment(self, username: str, comment_id: str) -> dict:
        try:
            obj_id = ObjectId(comment_id)
        except Exception:
            return {"success": False, "msg": "评论ID格式无效"}

        doc = await self.mongo.find_one(
            COMMENT_COLLECTION, {"_id": obj_id}
        )
        if not doc:
            return {"success": False, "msg": "评论不存在"}
        if doc.get("username") != username:
            return {"success": False, "msg": "无权删除他人的评论"}

        for img_path in doc.get("images", []):
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except Exception as e:
                logger.warning("删除评论图片失败: %s -> %s", img_path, e)

        await self.mongo.delete_one(COMMENT_COLLECTION, {"_id": obj_id})
        await self._invalidate_comment_cache(doc.get("mall_id"), doc.get("shopping_id"))

        return {"success": True, "msg": "评论已删除"}

    # ════════════════════ 卖家评论管理 ════════════════════

    async def get_seller_comments(
        self,
        mall_id: int,
        page: int = 1,
        page_size: int = 10,
        rating_type: str | None = None,
        reply_status: str | None = None,
    ) -> dict:
        """
        获取卖家店铺下的所有评论。
        reply_status: 'replied' / 'unreplied' 过滤已回复/未回复
        """
        query_filter: dict = {"mall_id": mall_id}

        if rating_type and rating_type in RATING_FILTER:
            query_filter["rating"] = RATING_FILTER[rating_type]

        if reply_status == "replied":
            query_filter["seller_reply"] = {"$ne": None}
        elif reply_status == "unreplied":
            query_filter["seller_reply"] = None

        total = await self.mongo.count_documents(COMMENT_COLLECTION, query_filter)
        skip = (page - 1) * page_size

        comments_raw = await self.mongo.find_many(
            COMMENT_COLLECTION,
            query_filter,
            limit=page_size,
            skip=skip,
            sort=[("created_at", -1)],
        )

        usernames = [c.get("username", "") for c in (comments_raw or []) if c.get("username")]
        avatar_map = await self._batch_fetch_avatars(usernames)

        data = []
        for c in comments_raw or []:
            uname = c.get("username", "匿名用户")
            data.append({
                "id": str(c.get("_id", "")),
                "shopping_id": c.get("shopping_id"),
                "order_no": c.get("order_no", ""),
                "username": uname,
                "avatar": avatar_map.get(uname, ""),
                "rating": c.get("rating", 5),
                "content": c.get("content", ""),
                "images": c.get("images", []),
                "created_at": c.get("created_at", ""),
                "seller_reply": c.get("seller_reply"),
            })

        return {
            "code": 200,
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": data,
        }

    #卖家回复评论
    async def seller_reply(
        self,
        mall_id: int,
        comment_id: str,
        reply_content: str,
        replied_by: str,
    ) -> dict:
        try:
            obj_id = ObjectId(comment_id)
        except Exception:
            return {"success": False, "msg": "评论ID格式无效"}

        doc = await self.mongo.find_one(
            COMMENT_COLLECTION, {"_id": obj_id}
        )
        if not doc:
            return {"success": False, "msg": "评论不存在"}
        if doc.get("mall_id") != mall_id:
            return {"success": False, "msg": "无权回复其他店铺的评论"}

        reply_data = {
            "content": reply_content.strip(),
            "replied_at": datetime.now().isoformat(),
            "replied_by": replied_by,
        }

        await self.mongo.update_one(
            COMMENT_COLLECTION,
            {"_id": obj_id},
            {"$set": {"seller_reply": reply_data, "updated_at": datetime.now().isoformat()}},
        )

        await self._invalidate_comment_cache(mall_id, doc.get("shopping_id"))
        return {"success": True, "msg": "回复成功"}

    # ════════════════════ 按订单号获取评论（卖家快捷回复用） ════════════════════

    async def get_comments_by_order(self, order_no: str, mall_id: int) -> dict:
        query_filter: dict = {"order_no": order_no, "mall_id": mall_id}
        comments_raw = await self.mongo.find_many(
            COMMENT_COLLECTION,
            query_filter,
            sort=[("created_at", -1)],
        )

        usernames = [c.get("username", "") for c in (comments_raw or []) if c.get("username")]
        avatar_map = await self._batch_fetch_avatars(usernames)

        data = []
        for c in comments_raw or []:
            uname = c.get("username", "匿名用户")
            data.append({
                "id": str(c.get("_id", "")),
                "shopping_id": c.get("shopping_id"),
                "order_no": c.get("order_no", ""),
                "username": uname,
                "avatar": avatar_map.get(uname, ""),
                "rating": c.get("rating", 5),
                "content": c.get("content", ""),
                "images": c.get("images", []),
                "created_at": c.get("created_at", ""),
                "seller_reply": c.get("seller_reply"),
            })

        return {
            "code": 200,
            "success": True,
            "total": len(data),
            "data": data,
        }

    # ════════════════════ 检查是否可以评论（供前端按钮状态使用） ════════════════════


    async def check_commentable(
        self, username: str, shopping_id: int, mall_id: int
    ) -> dict:
        check = await self._check_purchase_and_received(username, shopping_id, mall_id)
        return {
            "success": True,
            "commentable": check["ok"],
            "msg": check.get("msg", "可以评论"),
        }

    # ════════════════════ 缓存失效 ════════════════════

    async def _invalidate_comment_cache(
        self, mall_id: int | None, shopping_id: int | None
    ):
        if mall_id is not None and shopping_id is not None:
            await self.cache.delete_pattern(
                f"comment:list:{mall_id}:{shopping_id}:*"
            )
