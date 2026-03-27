"""平台端权限码：角色 JSON 中可勾选下列 code，亦可自定义任意字符串（自定义码仅前端展示为「自定义」）。"""

PERMISSION_CATALOG = [
    {"code": "admin.dashboard", "name": "仪表盘", "category": "概览"},
    {"code": "admin.commodity", "name": "商品管理", "category": "商品"},
    {"code": "admin.commodity_apply", "name": "商品审核（申请页）", "category": "商品"},
    {"code": "admin.user.merchant", "name": "商家与申请", "category": "用户"},
    {"code": "admin.user.mall", "name": "商城用户列表", "category": "用户"},
    {"code": "admin.user.platform", "name": "后台账号管理", "category": "用户"},
    {"code": "admin.user.role", "name": "角色与权限配置", "category": "用户"},
    {"code": "admin.audit_seller", "name": "商家申请审核页", "category": "审核"},
    {"code": "admin.business", "name": "商家详情", "category": "商家"},
    {"code": "admin.system_settings", "name": "系统设置", "category": "设置"},
]
