import type { Router, RouteLocationNormalized } from 'vue-router';
import { UserStore } from '@/moon/on_line';

// 定义需要排除的路由名称
const EXCLUDED_ROUTES = [
  'NotFound',        // 404页面
  'ManagementLogin', // 管理员登录页
  'Management',      // 管理员管理页
  'UserManagement',    // 用户管理页
  "AuditApplySeller",  // 审核申请页
  "BusinessManagement",  // 卖家管理页
  "BuyerSideIndex",  // 买家管理页
  "BuyerSideSing",  // 买家登录页
  "BuyerSingIn",  //商家端登录页
  "BuyerIndex",  // 买家端首页
  "BuyerStoreManagement",  // 买家端店铺管理页
  "BuyerAddMall",  // 买家端创建店铺页
  "BuyerSing",   // 买家端登录页
  "BuyerAddMallSuccess",  // 买家端创建店铺页
  "BuyerDeleteMall", // 买家端删除店铺页
  "BuyerStoreManage", // 买家端店铺管理页
  "BuyerUserManage", // 买家端用户管理页
  "BuyerUserList", // 买家端用户列表页
  "BuyerUserListId", // 买家端用户列表页——用户详情页
];

export function setupHeartbeatGuard(router: Router) {
  router.beforeEach(async (to: RouteLocationNormalized, from: RouteLocationNormalized, next) => {
    // 检查目标路由是否在排除列表中
    if (EXCLUDED_ROUTES.includes(to.name as string)) {
      return next(); // 直接放行，不处理心跳
    }

    const userStore = UserStore();
    const token = localStorage.getItem('access_token');

    // 如果有token且心跳未启动，则启动心跳
    if (token && !userStore.heartbeatInterval) {
      await userStore.startHeartbeat();
    }

    // 如果没有token但心跳正在运行，则停止心跳
    if (!token && userStore.heartbeatInterval) {
      userStore.stopHeartbeat();
    }

    next();
  });

  // 监听路由错误
  router.onError((error) => {
    console.error('路由错误:', error);
    const userStore = UserStore();
    userStore.stopHeartbeat();
  });
}
