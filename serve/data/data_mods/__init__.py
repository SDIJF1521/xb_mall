from typing import Optional,List,Tuple
from fastapi import File, UploadFile, Query
from pydantic import BaseModel,EmailStr
from datetime import time

from pydantic import Field
# 定义商品添加数据模型
class AddMall(BaseModel):
    Name: str
    Info: str
    Type: list
    Money:int
    token:str


# 定义商品删除数据模型
class DeleteMall(BaseModel):
    Name:str
    type:list
    token:str

# 定义用户注册数据模型
class UserRegister(BaseModel):
    email:EmailStr
    user_name:str
    user_password:str
    captcha:str

# 定义用户信息修改数据模型
class UserInformation(BaseModel):
    nickname:str
    age:int
    sex:str
    token:str

# 定义用户地址数据模型
class UserAddress(BaseModel):
    token:str
    save:str
    city:str
    county:str
    address:str
    name:str
    phone:str

# 定义用户地址修改数据模型
class UserAddressModify(BaseModel):
    token:str
    id:int
    save:str
    city:str
    county:str
    address:str
    name:str
    phone:str

# 定义用户地址删除数据模型
class UserDeleteAddress(BaseModel):
    token:str
    id:int

# 定义地址应用路由数据模型
class UserAddressApply(BaseModel):
    token:str
    id:int

# 定义用户注册数据模型
class Password_reset(BaseModel):
    email:EmailStr
    user_password:str
    captcha:str

# 定义商家申请路由数据模型
class ApplyBusiness(BaseModel):
    token:str
    name:str
    phone:str
    mall_name:str
    mall_describe:str

# 定义在线用户上传数据模型
class UserOnLineUploading(BaseModel):
    token:str

# 定义商家端登录路由数据模型
class SellerSignIn(BaseModel):
    user:str
    password:str
    station:str
    mall_id:Optional[int] = None


# 定义管理员登录路由数据模型
class ManageSignIn(BaseModel):
    user:str
    password:str

# 定义管理员获取商家申请资料路由模型
class GetApplySellerUser(BaseModel):
    token:str
    name:str

# 定义管理员同意商家申请路由数据模型
class ApplySellerConsent(BaseModel):
    token:str
    name:str

# 定义管理员驳回商家申请路由数据模型
class ApplySellerReject(BaseModel):
    token:str
    name:str
    reason:str

# 定义管理员获取商家信息路由数据模型
class ManagementGetMall(BaseModel):
    token:str
    name:str

# 定义冻结商家路由数据模型
class FreezeMerchant(BaseModel):
    token:str
    name:str

# 定义删除商家路由数据模型
class DeleteMerchant(BaseModel):
    token:str
    name:str

# 定义删除token时间戳路由数据模型
class DeleteToken(BaseModel):
    genre:str
    token:str

# 定义新增店铺/查询创建重复店铺路由数据模型
class AddMallData(BaseModel):
    token:str
    mall_name:str
    user:str
    mall_site:str
    mall_phone:str
    info:str

# 定义买家获取店铺名称路由数据模型
class GetMallName(BaseModel):
    token:str
    mall_name:Optional[str] = None

# 定义卖家上传店铺图片路由数据模型
class AddMallImg(BaseModel):
    token:str
    id:str

# 定义买家删除店铺路由数据模型
class DeleteMall(BaseModel):
    token:str
    mall_id:int

# 定义买家获取店铺信息路由数据模型
class GetMallInfo(BaseModel):
    token:str
    id:int=None

class UpdateMall(BaseModel):
    token:str
    id:int
    mall_name:str
    mall_site:str
    mall_phone:str
    info:str
    state:int

# 定义买家获取店铺用户列表路由数据模型
class GetMallUserList(BaseModel):
    token:str
    id:int
    page:Optional[int] = 1

# 定义买家添加店铺用户路由数据模型
class AddMallUser(BaseModel):
    token:str
    strore_id:int
    user_name:str
    user_password:str
    authority:int
    email:EmailStr

# 定义卖家端用户查询路由数据模型
class SelectMallUser(BaseModel):
    token:str
    strore_id:int
    user_name:str

# 定义卖家端用户删除路由数据模型
class DeleteMallUser(BaseModel):
    token:str
    strore_id:int
    user_name: List[str] = Field(..., min_items=1, description="要删除的用户名列表，至少一个")

# 定义卖家端用户修改路由数据模型
class UpdateMallUser(BaseModel):
    token:str
    stroe_id:int
    user:str
    user_name:str
    user_password:str
    authority:int
    email:EmailStr

# 定义卖家端角色获取路由数据模型
class BuyerGetRole(BaseModel):
    token:str
    stroe_id:int
    select_data :Optional[str] = None

# 定义操作码查询路由数据模型
class BuyerRoleCodeGet(BaseModel):
    token:str

# 定义角色添加路由数据模型
class BuyerRoleAdd(BaseModel):
    token:str
    stroe_id:int
    role_name:str
    role:str
    role_authority:int

# 定义角色删除路由数据模型
class BuyerRoleDelete(BaseModel):
    token:str
    stroe_id:int
    role_id:List[str] = Field(..., min_items=1, description="要删除的角色id列表，至少一个")

# 定义角色信息路由数据模型
class BuyerRoleInfo(BaseModel):
    stroe_id:int
    role_id:str

# 定义角色更新路由数据模型
class BuyerRoleUpdate(BaseModel):
    token:str
    stroe_id:int
    role_id:str
    role_name:str
    role:str
    role_authority:int

# 定义角色比例路由数据模型
class RoleRatio(BaseModel):
    stroe_id:int

# 定义商品添加路由数据模型
class CommodityAdd(BaseModel):
    token:str
    stroe_id:int
    name:str
    type:Optional[List[str]] = Field(None, description="商品类型，可选参数") 
    img_list:List[UploadFile] = Field(..., min_items=1, description="商品图片列表，至少一个")
    classify_categorize:int
    info:str
    sku_list:Optional[str] = Field(None, description="SKU列表，JSON字符串格式，包含规格组合、价格和库存")

# 定义商品列表路由数据模型
class CommodityList(BaseModel):
    stroe_id:int
    page:Optional[int] = 1
    select:Optional[str] = None

# 定义管理员获取商品上架申请列表路由数据模型
class ManageGetCommodityApplyList(BaseModel):
    select_data:Optional[str] = None
    page:Optional[int] = 1

# 定义管理员获取商品上架申请详情路由数据模型
class ManageGetCommodityApplyDetail(BaseModel):
    mall_id:int
    shopping_id:int

# 定义管理员拒绝商品上架申请路由数据模型
class ManageRejectCommodityApply(BaseModel):
    token:str
    mall_id:int
    shopping_id:int
    reason:str


# 定义买家获取商品信息路由数据模型
class BuyerGetCommodityInfo(BaseModel):
    token:str
    shopping_id:int

# 定义已读商品通知路由数据模型
class BuyerReadCommodityInform(BaseModel):
    token:str
    info_id:Optional[str] = None
    mall_id:Optional[int] = None
    shopping_id:Optional[int] = None


# 定义删除商品通知路由数据模型
class BuyerReadCommodityInfoDelete(BaseModel):
    token:str
    info_id:Optional[str] = None
    mall_id:Optional[int] = None
    shopping_id:Optional[int] = None


# 定义管理员通过商品上架申请路由数据模型
class ManageCommodityPassAudit(BaseModel):
    token:str
    mall_id:int
    shopping_id:int
    remark:Optional[str] = None

# 定义卖家端商品编辑路由
class SellerCommodityEdit(BaseModel):
    token:str
    stroe_id:int
    shopping_id:int
    name:str
    type:Optional[List[str]] = Field(None, description="商品类型，可选参数") 
    img_list:Optional[List[UploadFile]] = Field(None, description="商品图片列表，可选，编辑时不上传则保留原图片")
    classify_categorize:int
    info:str
    sku_list:Optional[str] = Field(None, description="SKU列表，JSON字符串格式，包含规格组合、价格和库存")

# 定义买家删除商品路由数据模型
class BuyerDeleteCommodity(BaseModel):
    token:str
    stroe_id:int
    shopping_id:int

# 定义买家下架商品路由数据模型
class BuyerDelistingCommodity(BaseModel):
    token:str
    stroe_id:int
    shopping_id:int

# 定义买家上架商品路由数据模型
class BuyerPutawayCommodity(BaseModel):
    token:str
    stroe_id:int
    shopping_id:int

# 定义买家添加商品分类路由数据模型
class BuyerCommodityClassifyAdd(BaseModel):
    token:str
    stroe_id:int
    name:str

# 定义买家删除商品分类路由数据模型
class BuyerCommodityClassifyDelete(BaseModel):
    token:str
    stroe_id:int
    classify_id:int

# 定义买家编辑商品分类路由数据模型
class BuyerCommodityClassifyEdit(BaseModel):
    token:str
    stroe_id:int
    classify_id:int
    name:str

# 定义卖家商品库存查询路由数据模型
class BuyerCommodityRepertoryList(BaseModel):
    token: str
    stroe_id: int
    select: Optional[str] = None
    stock_status: Optional[str] = None  # 新增库存状态筛选字段
    page: Optional[int] = 1
    page_size: Optional[int] = 20

# 定义卖家商品库存统计路由数据模型
class BuyerCommodityRepertoryStatistics(BaseModel):
    token: str
    stroe_id: int
    stock_status: Optional[str] = None  # 新增库存状态筛选字段

# 定义买家商品库存变更路由数据模型
class BuyerCommodityRepertoryChange(BaseModel):
    token: str
    stroe_id: int
    shopping_id: int
    sku_id: int
    change_type: Optional[int] = None  # 变更类型：1（增加）或 2（减少）
    change_num: int 
    maximum_inventory: Optional[int] = 99  # 新增最大库存字段
    minimum_balance: Optional[int] = 5  # 新增最小库存字段
    info: Optional[str] = None

# 定义卖家商品库存变更记录查询路由数据模型
class CommodityRepertoryRecord(BaseModel):
    token: str
    stroe_id: int
    shopping_id: int
    sku_id: int
    page: Optional[int] = 1
    page_size: Optional[int] = 20
    start_time: Optional[str] = None  # 开始时间，格式：YYYY-MM-DD HH:MM:SS
    end_time: Optional[str] = None    # 结束时间，格式：YYYY-MM-DD HH:MM:SS
    change_type: Optional[str] = None  # 变更类型：'设置', '增加', '减少'

# 定义卖家商品库存查询路由数据模型
class CommodityRepertoryAllModel(BaseModel):
    token: str
    stroe_id: int

# 定义购物车添加路由数据模型（前端 JSON 请求体，token 从 Header 获取）
class ShoppingCartAddBody(BaseModel):
    mall_id: int
    shopping_id: int
    spec_index: int = Field(..., ge=0, description="规格在 specification_list 中的索引")
    quantity: int = Field(..., ge=1, description="购买数量，至少为 1")

# 定义购物车添加路由数据模型（Form 格式，兼容旧版）
class ShoppingCartAdd(BaseModel):
    token: str
    stroe_id: int
    shopping_id: int
    sku_id: int
    quantity: int

# 定义购物车更改路由数据模型（修改数量）
class ShoppingCartUpdateBody(BaseModel):
    id: int = Field(..., description="购物车项 ID")
    quantity: int = Field(..., ge=1, description="新数量，至少为 1")

# 定义店铺商品列表查询路由参数模型
class StoreCommodityListQuery:
    def __init__(
        self,
        mall_id: int = Query(..., ge=1, description="店铺ID"),
        page: int = Query(1, ge=1, description="页码，从 1 开始"),
        page_size: int = Query(12, ge=1, le=50, description="每页条数，最大 50"),
        search: Optional[str] = Query(None, description="商品名称模糊搜索关键词"),
    ):
        self.mall_id = mall_id
        self.page = page
        self.page_size = page_size
        self.search = search


# 定义商城商品搜索路由参数模型（模糊匹配：名称、描述、标签、店铺名称，任一符合即可）
class MallCommoditySearchQuery:
    def __init__(
        self,
        keyword: Optional[str] = Query(None, description="搜索关键词，模糊匹配商品名称、描述、标签、店铺名称"),
        page: int = Query(1, ge=1, description="页码，从 1 开始"),
        page_size: int = Query(50, ge=1, le=100, description="每页条数，默认 50"),
    ):
        self.keyword = keyword
        self.page = page
        self.page_size = page_size


# ── 客服消息相关数据模型 ──────────────────────────────────────────────────────

# 用户端获取客服会话列表（按店铺分组）
class CsUserSessionListBody(BaseModel):
    token: str = Field(..., description="用户 JWT Token")


# 用户端获取某店铺客服消息历史
class CsUserHistoryQuery:
    def __init__(
        self,
        mall_id: int = Query(..., ge=1, description="店铺ID"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(50, ge=1, le=100, description="每页条数"),
    ):
        self.mall_id = mall_id
        self.page = page
        self.page_size = page_size


# 获取客服未读消息数
class CsUnreadCountQuery:
    def __init__(
        self,
        role: str = Query(..., description="角色：user（用户端）或 seller（卖家端）"),
        mall_id: Optional[int] = Query(None, ge=1, description="卖家端必传：店铺ID；用户端不传则返回所有店铺未读总和"),
    ):
        self.role = role
        self.mall_id = mall_id


# 标记客服消息已读（token 从 Header access-token 获取）
class CsMarkReadBody(BaseModel):
    mall_id: int = Field(..., ge=1, description="店铺ID")
    role: str = Field(..., description="角色：user 或 seller")
    session_id: Optional[str] = Field(None, description="卖家端必传：会话用户名；用户端不传")
