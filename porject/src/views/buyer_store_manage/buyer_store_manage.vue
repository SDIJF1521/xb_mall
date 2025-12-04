<template>
  <el-container>
    <el-header>
      <div class="management-navigation">
        <h2 class="title">小白的商城-店铺管理</h2>
      </div>
    </el-header>
    <el-main>
      <div v-if="store" class="content-info">
          <el-card v-for="item in store" style="width: 100%;" class="store-card">
            <template #header>
              <div class="card-header">
                <span class="mall-name">{{item.mall_name}}</span>
                <el-tag :type="item.state==1?'success':'danger'" size="small">{{item.state==1?'营业中':'已关闭'}}</el-tag>
              </div>
            </template>
              <el-row :gutter="10" style="width: 100%;">
                <el-col :span="12">
                  <el-image
                    :src="item.img ? 'data:image/png;base64,'+item.img : defaultStoreImg"
                    style="width: 100%; height: 200px; object-fit: cover;"
                    fit="cover">
                    <template #error>
                      <div class="image-slot">
                        <el-icon><Picture /></el-icon>
                      </div>
                    </template>
                  </el-image>
                </el-col>
                <el-col :span="12">
                  <div class="div_info">
                    <div class="info-item">
                      <el-icon><Document /></el-icon>
                      <span>{{item.info}}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><Location /></el-icon>
                      <span>{{item.site}}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><Phone /></el-icon>
                      <span>{{item.phone}}</span>
                    </div>
                    <el-button type="primary" size="default" @click="goToStoreDetail(item.id||0)" round class="manage-btn">
                      <el-icon><Setting /></el-icon>
                      进入管理
                    </el-button>
                  </div>
                </el-col>
              </el-row>
            <template #footer>
              <div class="card-footer">
                <el-icon><Clock /></el-icon>
                <span>创建时间：{{ item.time }}</span>
              </div>
            </template>
          </el-card>
      </div>
      <el-empty v-if="!store" description="暂无店铺信息" />
    </el-main>
    <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>

  </el-container>
</template>

<script setup lang="ts">
  import {ref,onMounted } from 'vue';
  import router from '@/router'
  import BuyerTheme from '@/moon/buyer_theme';
  import axios from 'axios';
  import { Document, Location, Phone, Clock, Setting, Picture } from '@element-plus/icons-vue';

  defineOptions({
    name:'BuyerStoreManage',
  })
  const defaultStoreImg = 'https://img2.baidu.com/it/u=3422222222,2822222222&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500'

  const Axios = axios.create({
    baseURL: "http://127.0.0.1:8000/api"
  })

  interface StoreInfoList {
    id?:number,
    img?:string,
    info?:string,
    mall_name?:string,
    phone?:string,
    site?:string,
    time?:string,
    state?:number
  }
  const store = ref<StoreInfoList[]>([])
  const token = localStorage.getItem('buyer_access_token')

  onMounted(async ()=>{
    new BuyerTheme().toggleTheme(true)
    const form = new FormData()
    form.append('token',token||'')
    const res = await Axios.post("/buyer_get_mall_info",form)
    if (res.status == 200){
      if (res.data.current){
        store.value = res.data.data
        console.log(store.value);


      }
    }
  })

  function goToStoreDetail(id:number){
    router.push({name:'BuyerStoreManageIndex',params:{id:id}})
  }
</script>

<style scoped>
.store-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 1px solid #e8e8e8;
  overflow: hidden;
}

.store-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.store-card :deep(.el-card__header) {
  color: white;
  padding: 16px 20px;
  border-bottom: none;
}

.store-card :deep(.el-card__body) {
  padding: 0;
}

.store-card :deep(.el-card__footer) {
  padding: 12px 20px;
  border-top: 1px solid #e8e8e8;
}
.footer-content {
    font-size: 14px;
    color: #999;
    text-align: center;
    padding: 20px 0;
}
.el-header {
    border-bottom: 1px solid #575859;
    padding-bottom: 10px;
    margin-bottom: 10px;
}
.title{
  background: linear-gradient(to right, #7ef0b3, #9c6edd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    color: transparent;
}
.management-navigation {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0 20px;
}
.content-info{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    grid-gap: 20px;
    padding: 0 20px;
    max-width: 1200px;
    margin: 0 auto;
}

@media (max-width: 768px) {
  .content-info {
    grid-template-columns: 1fr;
    padding: 0 10px;
  }

  .el-row {
    flex-direction: column;
  }

  .el-col {
    width: 100%;
  }

  .div_info {
    height: auto;
    padding: 15px 20px;
    gap: 15px;
  }

  .store-card :deep(.el-card__header) {
    padding: 12px 15px;
  }

  .mall-name {
    font-size: 16px;
  }
}
.div_info{
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 200px;
  padding: 0 20px;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.info-item .el-icon {
  color: #909399;
  margin-top: 2px;
  flex-shrink: 0;
}

.mall-name {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.manage-btn {
  margin-top: auto;
  padding: 8px 16px;
  font-weight: 500;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  font-size: 13px;
}
</style>
