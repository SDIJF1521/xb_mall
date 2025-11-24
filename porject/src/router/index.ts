import { createRouter, createWebHistory } from 'vue-router';
import type { RouteRecordRaw } from 'vue-router';
import HomeView from '@/views/index/HomeView.vue';

import Center from '@/views/personal_center/PersonalCenter.vue';
import Mall from '@/views/mall/Mall.vue'
import ShoppingTrolley  from '@/views/shopping_trolley/ShoppingTrolley.vue'
import Register from '@/views/log_in/register.vue'
import PersonalDetailsChange from '@/views/personal_details_change/personal_details_change.vue'
import ApplySeller from '@/views/apply_seller/apply_seller.vue'
import PasswordReset from '@/views/password_reset/password_reset.vue'
import Management from '@/views/management/management.vue'
import NotFound from '@/views/errors/NotFound.vue'
import BuyerSideIdex from '@/views/buyer_side_index/BuyerSideIdex.vue'
import ManagementLogin from '@/views/management_login/management_login.vue'
import UserManagement from '@/views/user_management/user_management.vue'
import AuditApplySeller from '@/views/audit_apply_seller/audit_apply_seller.vue'
import AddreSet from '@/views/addre_set/addre_set.vue'
import BusinessManagement from '@/views/business_management/business_management.vue'
import BuyerSideSing from '@/views/buyer_side_sing/buyer_side_sing.vue'
import BuyerSideStoreManagement from '@/views/buyer_side_store_management/buyer_side_store_management.vue'
import BuyerSideAddMall from '@/views/buyer_side_add_mall/buyer_side_add_mall.vue'
import BuyerDeleteMall from '@/views/buyer_delete_mall/buye_delete_mall.vue'
import BuyerStoreManage from '@/views/buyer_store_manage/buyer_store_manage.vue'
import BuyerStoreManageIndex from '@/views/buyer_store_manage_id/buyer_store_manage_index.vue'
import BuyerUserManage from '@/views/buyer_store_user_manage/buyer_user_manage.vue'
import BuyerUserList from '@/views/buyer_select/buyer_select.vue';
import BuyerUserListId from '@/views/buyer_user_list_id/buyer_user_list_id.vue'
import BuyerRoleList from '@/views/buyer_role_list/buter_role_list.vue'



import { setupHeartbeatGuard } from './heartbeatGuard'
import { setupAuthGuard } from './authGuard';
import { setupAdminAuthGuard } from './admin_authGuard'
import {setupBuyerAuthGuard} from './buyer_authGuard'


const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: HomeView
  },
  {
    //商城页
    path: '/mall',
    name: 'Mall',
    component: Mall
  },
  {
    // 个人页
    path: '/personal_center',
    name: 'PersonalCenter',
    component: Center
  },
  {
    // 购物车
    path:'/shopping_trolley',
    name: 'ShoppingTrolley',
    component:ShoppingTrolley
  },
  {
    //登录注册页
    path:'/register',
    name:'Register',
    component:Register
  },
    //个人信息修改页
    {
    path:'/personal_details_change',
    name:'RPersonalDetailsChange',
    component: PersonalDetailsChange
  },
  {
    // 商家申请页
    path:'/apply_seller',
    name:'ApplySeller',
    component:ApplySeller
  },
  {
    // 密码重置页
    path:'/password_reset',
    name:'PasswordReset',
    component:PasswordReset
  },{
    // 地址设置页
    path:'/addre_set',
    name:'AddreSet',
    component:AddreSet
  },
  {
    // 买家端首页
    path:'/buyer_index',
    name:'BuyerIndex',

    component:BuyerSideIdex

  },
  {
    // 买家端店铺管理页
    path:'/buyer_store_management',
    name:'BuyerStoreManagement',
    component:BuyerSideStoreManagement
  },
  {
    // 买家端创建店铺页
    path:'/buyer_add_mall',
    name:'BuyerAddMall',
    component:BuyerSideAddMall
  },
  {
    // 买家端删除店铺页
    path:'/buyer_delete_mall',
    name:'BuyerDeleteMall',
    component:BuyerDeleteMall
  },
  // 买家端店铺管理页
  {
    path:'/buyer_store_manage',
    name:'BuyerStoreManage',
    component:BuyerStoreManage
  },
  // 买家端店铺管理页——店铺详情页
  {
    path:'/buyer_store_manage_index/:id',
    name:'BuyerStoreManageIndex',
    component:BuyerStoreManageIndex
  },
  {
    // 买家端登录页
    path:'/buyer_sing',
    name:'BuyerSing',
    component:BuyerSideSing
  },
  {
    // 管理员登录页
    path:'/management_login',
    name:'ManagementLogin',
    component:ManagementLogin
  },
  {
    // 管理员管理页
    path:'/management',
    name:'Management',
    component:Management
  },
  // 管理员管理页——用户管理
  {
    path:'/user_management',
    name:'UserManagement',
    component:UserManagement
  },
  {
    // 用户管理页
    path:'/business_management/:id',
    name:'BusinessManagement',
    component:BusinessManagement
  },
  // 买家端用户管理页
  {
    path:'/buyer_user_manage',
    name:'BuyerUserManage',
    component:BuyerUserManage
  },
  // 买家端用户列表页
  {
    path:'/buyer_select',
    name:'BuyerSelect',
    component:BuyerUserList
  },
  // 买家端用户列表页——用户详情页
  {
    path:'/buyer_user_list_id/:id',
    name:'BuyerUserListId',
    component:BuyerUserListId
  },
  // 买家端角色列表页
  {
    path:'/buyer_role_list/:id',
    name:'BuyerRoleList',
    component:BuyerRoleList
  },
  // 管理员管理页——商家审核
  {
    path:'/audit_apply_seller/:id',
    name:'AuditApplySeller',
    component:AuditApplySeller
  },
    {
    // 404 页面 - 匹配所有未定义的路由
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});


// 认证守卫应放在最前面
setupAuthGuard(router);
// 后台管理认证守卫
setupAdminAuthGuard(router)
// 应用心跳守卫
setupHeartbeatGuard(router);

// 买家端认证守卫
setupBuyerAuthGuard(router)

export default router;
