<template>
    <el-container>
      <el-header><management-navigation/></el-header>
      <el-main>
          <el-descriptions
            title="申请内容"
            direction="vertical"
            border
            :column="2"
            style="margin-top: 20px"
          >
            <el-descriptions-item  label="用户名" >{{ apply_seller_data[0] }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ apply_seller_data[1] }}</el-descriptions-item>
          </el-descriptions>

          <el-descriptions
            direction="vertical"
            border

            style="margin-top: 20px"
          >
            <el-descriptions-item label="店铺名称">{{ apply_seller_data[3] }}</el-descriptions-item>
            <el-descriptions-item label="电话号码">{{ apply_seller_data[2] }}</el-descriptions-item>
            <el-descriptions-item label="日期">{{ apply_seller_data[6] }}</el-descriptions-item>
          </el-descriptions>

        <el-descriptions
            direction="vertical"
            border
            :column="1"
            style="margin-top: 20px"
        >
          <el-descriptions-item label="店铺描述">
                {{ apply_seller_data[4] }}
          </el-descriptions-item>
        </el-descriptions >
        <div v-if="!reject_select" class="button">
          <el-button type="primary" size="large" @click="constent" plain>通过</el-button>
          <el-button type="danger" size="large" @click="reject" plain>驳回</el-button>
        </div>
        <!--驳回窗口-->
        <div style="margin-top: 15px;" v-if="reject_select">
          <el-input v-model="reject_reason" type="textarea" placeholder="请输入驳回理由" :autosize="{ minRows: 2, maxRows: 25}" />
          <div class="button">
            <el-button type="success" size="large" @click="send" plain>发送</el-button>
            <el-button type="danger" size="large" @click="cancel" plain>取消</el-button>
          </div>
        </div>
      </el-main>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>

</template>
<script setup lang="ts">
import ManagementNavigation from "@/moon/management_navigation.vue"
import { useRoute } from 'vue-router';
import { ref, onMounted } from 'vue'
import axios from "axios";
import { ElMessage } from 'element-plus';
import router  from "@/router";
import { asc } from "echarts/types/src/util/number.js";

const Axios = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
})

defineOptions({name:'AuditApplySeller',
  components:{
    ManagementNavigation
  } 
})
const apply_seller_data = ref(['***','***','***','123456','***'])
const route = useRoute();
  const userId = route.params.id||'';
onMounted(async ()=>{
    const fromdata = new FormData()
    fromdata.append('token',localStorage.getItem('admin_access_token') || '')
    fromdata.append('name',String(userId))
    Axios.post('/get_apply_seller_user',fromdata)
    .then(async ref=>{
      if (ref.status ==200){
        if (ref.data.current){
          apply_seller_data.value = ref.data.apply_list[0]
        }else{
          ElMessage.warning(ref.data.msg || '获取数据失败');
        }

      }
    })


})

const reject_select = ref(false)
const reject_reason = ref('')

const pass = ref(async ()=>{})

// 同意
const constent = ref(async ()=>{
  const fromdata = new FormData()
  fromdata.append('token',localStorage.getItem('admin_access_token') || '')
  fromdata.append('name',String(userId))
  Axios.post('/apply_seller_consent',fromdata)
  .then(async ref=>{
    if (ref.status ==200){
      if (ref.data.current){
        ElMessage.success('同意成功');
        router.push('/user_management')
      }else{
        ElMessage.warning(ref.data.msg || '同意失败');
      }

    }
  })
})
// 驳回
const reject = ref(async () =>{
  reject_select.value=true
})

//取消
const cancel = ref(async ()=>{
  reject_select.value=false
})

// 发送
const send = ref(async ()=>{
  const fromdata = new FormData()
  fromdata.append('token',localStorage.getItem('admin_access_token') || '')
  fromdata.append('name',String(userId))
  fromdata.append('reason',reject_reason.value)
  Axios.post('/apply_seller_reject',fromdata)
  .then(async ref=>{
    if (ref.status ==200){
      if (ref.data.current){
        ElMessage.success('拒绝成功');
        router.push('/user_management')
      }else{
        ElMessage.warning(ref.data.msg || '拒绝失败');
      }

    }
  })
})
</script>

<style scoped>
.el-header {
  padding: 0 20px;
  height: auto;
  min-height: 60px;
}

.el-main {
  padding: 20px;
  flex: 1;
}
.footer-content {
  text-align: center;
  color: darkgray;
}

.button {
  margin-top: 15px;
  display: flex;
  width: 100%;
  justify-content: center;
  gap: 30px;
}
.button>*{
  width: 100%;
}

</style>