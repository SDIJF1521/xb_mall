import { defineStore } from 'pinia';

// 买家导航栏状态
export const useBuyerNavigationStore = defineStore('buyerNavigation', {
  state: () => ({
    // 当前状态
    isNavCollapsed: false,
    isNavExpanded: true,
    isNavVisible: true,
    
    // 保存初始状态用于重置
    initialState: {
      isNavCollapsed: false,
      isNavExpanded: true,
      isNavVisible: true
    },
    
    // 记录鼠标是否在导航栏内
    isMouseInside: true
  }),
  actions: {
    // 切换导航栏折叠状态
    toggleNavCollapse() {
      this.isNavCollapsed = !this.isNavCollapsed;
      this.isNavExpanded = !this.isNavCollapsed;
    },
    
    // 鼠标进入导航栏
    handleMouseEnter() {
      this.isMouseInside = true;
    },
    
    // 鼠标离开导航栏
    handleMouseLeave() {
      this.isMouseInside = false;
      // 离开后恢复到初始状态
      this.resetToInitialState();
    },
    
    // 重置到初始状态
    resetToInitialState() {
      this.isNavCollapsed = this.initialState.isNavCollapsed;
      this.isNavExpanded = this.initialState.isNavExpanded;
    }
  }
});
    