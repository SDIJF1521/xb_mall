import type { Router, RouteLocationNormalized } from 'vue-router';
import axios from 'axios';

// 需要验证登录状态的路由名称列表
const AUTH_REQUIRED_ROUTES = [
  'PersonalCenter',,
  'PersonalDetailsChange',
  'ApplySeller'
];

// API基础URL
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// 验证令牌有效性
async function verifyToken(token: string): Promise<boolean> {
  try {
    const formData = new FormData();
    formData.append('token', token);
    
    const response = await axios.post(API_BASE_URL + '/user_sign_in', formData);
    
    return response.status === 200 && response.data.current;
  } catch (error) {
    console.error('Token verification failed:', error);
    return false;
  }
}

// 导出路由守卫函数
export function setupAuthGuard(router: Router) {
  router.beforeEach(async (to: RouteLocationNormalized, from: RouteLocationNormalized, next) => {
    const token = localStorage.getItem('access_token');
    
    // 检查是否为需要认证的路由
    const requiresAuth = AUTH_REQUIRED_ROUTES.includes(String(to.name));
    
    // 登录页面的特殊处理
    if (to.name === 'Register') {
      if (token && await verifyToken(token)) {
        // 已登录用户访问登录页，重定向到个人中心
        return next('/personal_center');
      }
      return next();
    }
    
    // 需要认证的路由处理
    if (requiresAuth) {
      if (!token) {
        // 无令牌，重定向到登录页
        return next('/register');
      }
      
      const isTokenValid = await verifyToken(token);
      
      if (!isTokenValid) {
        // 令牌无效，清除并重定向到登录页
        localStorage.removeItem('access_token');
        return next('/register');
      }
      
      // 认证通过，继续路由
      return next();
    }
    
    // 不需要认证的路由直接通过
    next();
  });
}  