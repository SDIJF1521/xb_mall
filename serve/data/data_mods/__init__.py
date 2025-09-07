from pydantic import BaseModel,EmailStr
from datetime import time

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

# 定义删除token时间戳路由数据模型
class DeleteToken(BaseModel):
    genre:str
    token:str

# 定义新增由数据模型
class AddMallData(BaseModel):
    token:str
    name:str
    mall:str
    info:str