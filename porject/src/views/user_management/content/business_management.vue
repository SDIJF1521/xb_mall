<template>
    <el-empty v-if="management_list.length == 0" description="暂无数据" />
    <div v-else v-for="itrm in management_list">
        <el-card style="width: 100%; text-align: center" shadow="hover" @click="skip(itrm)"><span class="card-text">{{ itrm }}</span></el-card>
        <div style="display: flex; justify-content: center; margin-top: 20px;">
            <el-pagination
              :page-size="5"
              :pager-count="11"
              layout="prev, pager, next"
              :total="page"
            />
        </div>
    </div>
</template>
<script setup lang="ts">
import axios from 'axios';
import { ref,onMounted } from 'vue';
import { ElMessage } from 'element-plus';

const Axios = axios.create({
    baseURL:'http://127.0.0.1:8000/api'
})
const page = ref(1)
const management_list = ref<any[]>([])
defineOptions({
    name:'BusinessManagement'
    })
async function request() {
    const token = localStorage.getItem('admin_access_token')||''
    const fromdata = new FormData()
    fromdata.append('token',token)
    await Axios.post('/number_merchants',fromdata)
    .then((res)=>{
        management_list.value = Object.values(res.data.merchant_list)
        page.value = res.data.page
    })

}

function skip(name:string){

    window.location.href = `/business_management/${name}`
} 
onMounted(async ()=>{
    await request()

})
</script>

<style scoped>
.card-text {
  transition: color 0.3s ease;
}

.el-card:hover .card-text {
  background-image: linear-gradient(to right, #ec8e8c, #8556ab);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  -webkit-text-fill-color: transparent;
}
</style>