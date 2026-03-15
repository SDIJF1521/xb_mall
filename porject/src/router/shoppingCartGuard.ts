import type { Router, RouteLocationNormalized } from 'vue-router';

/**
 * 购物车路由守卫：未登录时跳转登录页
 * 支持 C 端 access_token 与商家端 buyer_access_token
 */
export function setupShoppingCartGuard(router: Router) {
  router.beforeEach((to: RouteLocationNormalized, _from, next) => {
    if (to.name !== 'ShoppingTrolley') {
      return next();
    }
    const token = localStorage.getItem('access_token') || localStorage.getItem('buyer_access_token');
    if (!token) {
      return next('/register');
    }
    next();
  });
}
