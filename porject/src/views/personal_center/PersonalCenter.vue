<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <AppNavigation/>
      </el-header>
      <el-main>

          <el-row>
              <!-- 菜单 -->
                <el-menu
                  :default-active="menuActiveIndex"
                  class="el-menu-vertical-demo"
                  :collapse="isCollapse"
                  @mouseenter="unfold"
                  @mouseleave="shrink"
                  @select="handleSelect"
                >
                    <!--个人-->
                    <el-menu-item index="1" @mouseenter="handleMouseEnter('1')">
                      <el-icon><UserFilled /></el-icon>
                      <template #title>个人</template>
                    </el-menu-item>
                    <!--收藏-->
                    <el-menu-item index="2" @mouseenter="handleMouseEnter('2')"
                    >
                      <el-icon><Collection /></el-icon>
                      <template #title>收藏</template>
                    </el-menu-item>
                    <!--收藏-->
                    <el-menu-item index="3" @mouseenter="handleMouseEnter('3')">
                      <el-icon><Edit /></el-icon>
                      <template #title>评论管理</template>
                    </el-menu-item>
                    <!--浏览历史-->
                    <el-menu-item index="5" @mouseenter="handleMouseEnter('5')">
                      <el-icon><Clock /></el-icon>
                      <template #title>浏览历史</template>
                    </el-menu-item>
                    <!--客服消息-->
                    <el-menu-item index="6" @mouseenter="handleMouseEnter('6')">
                      <el-badge :value="csUnreadCount" :hidden="csUnreadCount === 0" :max="99" class="cs-menu-badge">
                        <el-icon><Service /></el-icon>
                      </el-badge>
                      <template #title>客服消息</template>
                    </el-menu-item>
                    <!--设置-->
                    <el-menu-item index="4" @mouseenter="handleMouseEnter('4')">
                      <el-icon><setting /></el-icon>
                      <template #title>设置</template>
                    </el-menu-item>

                </el-menu>
              <!-- <div>内容</div> -->
               <transition name="el-zoom-in-top">
                <div class="main">
                  <component :is="currentComponent" @read="fetchCsUnread"></component>
                </div>
              </transition>
          </el-row>
      </el-main>
      <el-footer class="footer-content">版权所有 © [xb商城]，保留所有权利。</el-footer>
    </el-container>
  </div>
</template>

<script>
import AppNavigation from '@/moon/navigation.vue';
import router from '@/router';
import axios from 'axios';
import CenterIndex from './content/center_index.vue'
import CenterCollect from './content/center_collect.vue'
import ConterComment from './content/conter_comment.vue'
import Set from './content/set.vue'
import BrowsingHistory from './content/browsing_history.vue'
import CenterCsMessages from './content/center_cs_messages.vue'

export default {
  name: 'Center',
  data() {
    return {
      isCollapse: true,
      count: 20, // 初始数据数量
      page: 1,   // 当前页码
      hasMore: true, // 是否还有更多数据
      pageSize: 20, // 每页数据量
      selectedType: '',   // 选中的菜单分类
      hoverType: '',       // 鼠标悬停的分类
      csUnreadCount: 0,   // 客服消息未读数
    }
  },
  components: {
    AppNavigation,
    CenterIndex,
    CenterCollect,
    ConterComment,
    Set,
    BrowsingHistory,
    CenterCsMessages
  },
  setup() {
    const url = 'http://127.0.0.1:8000/api';
    const token = async() => {
      const token = localStorage.getItem('access_token');
      console.log(token);

      if (token == null) {
        router.push('/register');
      } else {
        const fromdata = new FormData();
        fromdata.append('token', token);
        await axios({
          method: 'Post',
          url: url + '/user_sign_in',
          data: fromdata
        })
        .then(res => {
          console.log(res.data);
          if (res.status == 200) {
            if (!res.data.current) {
              router.push('/register');
            }
          }
        });
      }
    };
    token();
  },
  mounted() {
    this.fetchCsUnread();
    // 支持通过 URL 参数 ?tab=cs 直接打开客服消息
    if (this.$route.query.tab === 'cs') {
      this.selectedType = '6';
    }
  },
  computed: {
    // 当前高亮的菜单项（用于 default-active）
    menuActiveIndex() {
      return this.selectedType || '1';
    },
    // 子组件动态选择
    currentComponent() {
      const map = {
        '1': 'CenterIndex',
        '2': 'CenterCollect',
        '3': 'ConterComment',
        '4': 'Set',
        '5': 'BrowsingHistory',
        '6': 'CenterCsMessages',
      }
      if (this.hoverType && map[this.hoverType]) return map[this.hoverType]
      if (!this.hoverType && this.selectedType && map[this.selectedType]) return map[this.selectedType]
      return 'CenterIndex'

    }
  },

  methods: {
    async fetchCsUnread() {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      try {
        const res = await axios.get('http://127.0.0.1:8000/api/cs_unread_count', {
          params: { role: 'user' },
          headers: { 'access-token': token },
        });
        if (res.data?.current && typeof res.data.unread_count === 'number') {
          this.csUnreadCount = res.data.unread_count;
        }
      } catch (e) {
        // ignore
      }
    },
    // 菜单栏悬停选择
    handleMouseEnter(type){
      this.hoverType = type;
      // console.log('鼠标悬停在:', this.hoverType);
    },

    handleSelect(key, keyPath){
       this.selectedType = key;
       if (key === '6') this.fetchCsUnread(); // 进入客服消息时刷新未读
      //  console.log('菜单选中项:', key, keyPath);
    },

    // 菜单伸缩
    unfold(){
      this.isCollapse = false
    },
    shrink(){
      this.isCollapse = true
      this.hoverType = ''
    }
  }
}
</script>

<style scoped>
/*菜单基础样式 */
.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 200px;
}

/* 页脚样式 */
.footer-content {
  text-align: center;
  color: darkgray;
}

.main{
  flex: 1;
  display: flex;
  flex-direction: column;    /* 垂直布局 */
  justify-content: center;
  align-items: center;
  border: 1px solid #424141; /* 这里设置边框 */
  box-sizing: border-box; /* 防止内边距撑大盒子 */
}

.infinite-list {
  height: 300px;
  padding: 0;
  margin: 0;
  list-style: none;
}
.infinite-list .infinite-list-item {
   flex: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50px;
  background: var(--el-color-primary-light-9);
  margin: 10px;
  color: var(--el-color-primary);
}
.infinite-list .infinite-list-item + .list-item {
  margin-top: 10px;
}

.cs-menu-badge :deep(.el-badge__content) {
  background: #f56c6c;
}
</style>
