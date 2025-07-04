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
                  default-active="1"
                  load:1
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
                    <!--设置-->
                    <el-menu-item index="4" @mouseenter="handleMouseEnter('4')">
                      <el-icon><setting /></el-icon>
                      <template #title>设置</template>
                    </el-menu-item>

                </el-menu>
              <!-- <div>内容</div> -->
               <transition name="el-zoom-in-top">
                <div class="main">
                  <component :is="currentComponent"></component>
                </div>
              </transition>
          </el-row>
      </el-main>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
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
    }
  },
  components: {
    AppNavigation,
    CenterIndex,
    CenterCollect,
    ConterComment,
    Set
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
  computed: {
    // 子组件动态选择
    currentComponent() {
      if (this.hoverType == '1'){
        return 'CenterIndex'
      }
      else if(this.hoverType == '2'){
        console.log('yes');
        return 'CenterCollect'
      }else if(this.hoverType == '3') {
        return 'ConterComment'
      }else if(this.hoverType == '4'){
        return 'Set'
      }
      
      if (this.hoverType == '' && this.selectedType == '1'){
        return 'CenterIndex'
      }else if(this.hoverType == '' && this.selectedType == '2'){
        return 'CenterCollect'
      }else if(this.hoverType == '' && this.selectedType == '3'){
        return 'ConterComment'
      }else if(this.hoverType == '' && this.selectedType == '4'){
        return 'Set'
      }
      return 'CenterIndex'

    }
  },

  methods: {
    // 菜单栏悬停选择
    handleMouseEnter(type){
      this.hoverType = type;
      // console.log('鼠标悬停在:', this.hoverType);
    },

    handleSelect(key, keyPath){
       this.selectedType = key;
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
</style>
