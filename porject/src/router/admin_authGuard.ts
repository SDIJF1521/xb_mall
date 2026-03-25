import type { Router, RouteLocationNormalized } from 'vue-router';
import axios from 'axios';
import { tryRefreshAdminTokens, clearAdminSession, fetchAdminSession } from '@/utils/adminToken';
import { hasAdminPermission, hasAnyAdminPermission } from '@/utils/adminPermission';

// 需要验证登录状态的路由名称列表
const AUTH_REQUIRED_ROUTES = [
    'Management',
    'UserManagement',
    'AuditApplySeller',
    'BusinessManagement',
    'ManagementCommodity',
    'ManagementCommodityApply',
    'ManagementSystemSettings',
];

// API基础URL
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// 验证令牌有效性
async function verifyToken(token: string): Promise<boolean> {
  try {
    const formData = new FormData();
    formData.append('token', token);

    const response = await axios.post(API_BASE_URL + '/management_verify', formData);
    console.log(response.data);


    return response.status === 200 && response.data.current;
  } catch (error) {
    console.error('Token verification failed:', error);
    return false;
  }
}

// 导出路由守卫函数
export function setupAdminAuthGuard(router: Router) {
  router.beforeEach(async (to: RouteLocationNormalized, from: RouteLocationNormalized, next) => {
    const token = localStorage.getItem('admin_access_token');

    // 检查是否为需要认证的路由
    const requiresAuth = AUTH_REQUIRED_ROUTES.includes(String(to.name));

    // 登录页面的特殊处理
    if (to.name === 'ManagementLogin') {
      let ok = !!(token && (await verifyToken(token)));
      if (!ok && token) {
        ok = await tryRefreshAdminTokens();
        if (ok) {
          const t2 = localStorage.getItem('admin_access_token');
          if (t2) ok = await verifyToken(t2);
        }
      }
      if (ok) return next('/management');
      return next();
    }

    // 需要认证的路由处理
    if (requiresAuth) {
      if (!token) {
        const refreshed = await tryRefreshAdminTokens();
        if (refreshed) {
          const t2 = localStorage.getItem('admin_access_token');
          if (t2 && (await verifyToken(t2))) return next();
        }
        return next('/management_login');
      }

      let isTokenValid = await verifyToken(token);
      if (!isTokenValid) {
        isTokenValid = await tryRefreshAdminTokens();
        if (isTokenValid) {
          const t2 = localStorage.getItem('admin_access_token');
          if (t2) isTokenValid = await verifyToken(t2);
        }
      }
      if (!isTokenValid) {
        clearAdminSession();
        return next('/management_login');
      }

      await fetchAdminSession();
      const perm = to.meta.adminPermission;
      const permAny = to.meta.adminPermissionAny;
      if (typeof perm === 'string' && !hasAdminPermission(perm)) {
        return next({ path: '/management', query: { denied: '1' } });
      }
      if (Array.isArray(permAny) && permAny.length && !hasAnyAdminPermission(permAny)) {
        return next({ path: '/management', query: { denied: '1' } });
      }

      return next();
    }

    // 不需要认证的路由直接通过
    next();
  });
}
