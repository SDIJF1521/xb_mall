import type { Router, RouteLocationNormalized } from 'vue-router';
import axios from 'axios';

// 需要验证登录状态的路由名称列表
const AUTH_REQUIRED_ROUTES = [
    'Management',
    'UserManagement',
    'AuditApplySeller',
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
      if (token && await verifyToken(token)) {
        // 已登录用户访问登录页，重定向到个人中心
        return next('/management');
      }
      return next();
    }
    
    // 需要认证的路由处理
    if (requiresAuth) {
      if (!token) {
        // 无令牌，重定向到登录页
        return next('/management_login');
      }
      
      const isTokenValid = await verifyToken(token);
      
      if (!isTokenValid) {
        // 令牌无效，清除并重定向到登录页
        localStorage.removeItem('admin_access_token');
        return next('/management_login');
      }
      
      // 认证通过，继续路由
      return next();
    }
    
    // 不需要认证的路由直接通过
    next();
  });
}  