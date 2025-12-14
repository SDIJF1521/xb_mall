import type { Router, RouteLocationNormalized } from 'vue-router';
import axios from 'axios';
import {useBuyerJurisdictionStore} from '@/moon/buyer_jurisdiction_pinia';

const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
})

const AUTH_REQUIRED_ROUTES = ['BuyerIndex',
                              'BuyerStoreManagement',
                              'BuyerAddMall',
                              'BuyerStoreManagement',
                              'BuyerDeleteMall',
                              'BuyerStoreManage',
                              'BuyerUserManage',
                              'BuyerUserList',
                              'BuyerUserListId',
                              'BuyerRoleList',
                              'BuyerStoreManageIndex',
                              "BuyerUserListId",
                              "BuyerStoreManageIndex",
                              "BuyerUserStatistics",
                              "BuyerCommodityAdd",
                            ];

// 验证令牌有效性
async function verifyToken(token: string): Promise<boolean> {
    try {
      const buyerJurisdictionStore = useBuyerJurisdictionStore();

      const response = await Axios.post('/buyer_side_verify?token='+token);
      if (response.data.station === 'admin') {
          buyerJurisdictionStore.setJurisdiction('admin')

      } else {
          buyerJurisdictionStore.setJurisdiction('user')
      }
      return response.status === 200 && response.data.current;
    } catch (error) {
      console.error('Token verification failed:', error);
      return false;
    }
  }


// 导出路由守卫函数
export function setupBuyerAuthGuard(router: Router) {
  router.beforeEach(async (to: RouteLocationNormalized, from: RouteLocationNormalized, next) => {
    const token = localStorage.getItem('buyer_access_token');


    // 检查是否为需要认证的路由
    const requiresAuth = AUTH_REQUIRED_ROUTES.includes(String(to.name));

    // 登录页面的特殊处理
    if (to.name === 'BuyerSing') {
      if (token && await verifyToken(token)) {
        // 已登录用户访问登录页，重定向到个人中心
        return next('/buyer_index');

      }
      return next();
    }

    // 需要认证的路由处理
    if (requiresAuth) {
      if (!token) {
        // 无令牌，重定向到登录页
        return next('/buyer_sing');
      }

      const isTokenValid = await verifyToken(token);

      if (!isTokenValid) {
        // 令牌无效，清除并重定向到登录页
        localStorage.removeItem('buyer_access_token');

        return next('/buyer_sing');
      }

      // 认证通过，继续路由
      return next();
    }

    // 不需要认证的路由直接通过
    next();
  });
}
