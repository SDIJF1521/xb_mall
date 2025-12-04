<template>
  <ul>
    <li>用户： <el-text class="mx-1" type="primary" size="large">{{ user_name }}</el-text></li>
    <li v-for = '(item,index) in data_list'> {{ item['name'] }}
      <el-text class="mx-1" size="large">{{ item['text'] }}</el-text>
      <el-button :type ="item['type']" v-if="item['text'] == `${item['select_val']}`" @click="item['fun']" round>{{ item['button_text'] }}</el-button>
    </li>
  </ul>
  <div class="button_style">
      <el-button type="info" @click="logout" style="width: 200px;" round>登出</el-button>
      <el-button  v-if = 'select' @click="buyer_sing" type="warning" style="width: 200px;" round>进入卖家端</el-button>

  </div>

</template>
<script lang="ts" setup>
import { ref,onMounted } from 'vue'
import router from '@/router'
import { ElMessage } from 'element-plus';
import axios from 'axios';

// 基础数据
const user_name = ref('***')
const token = localStorage.getItem('access_token')||''

const Axios = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',

});
// 登出功能函数
const logout = ref(()=>{
  console.log(token);
  const formdata = new FormData()
  formdata.append('token',token)
  Axios.delete('online_off',{ data: formdata })
  localStorage.removeItem('access_token')
  router.push('/register')
  const exit_user = new FormData()
  exit_user.append('token',token)
  exit_user.append('genre',"1")
  Axios.delete('/delete_token_time',{ data: exit_user })
  ElMessage.success('已登出')

})


// 跳转到申请页函数
const apply_seller = ref(()=>{
  router.push('/apply_seller')
})

// 跳转地址设置页
const addre_set = ref(()=>{
  router.push('/addre_set')
})

// 基础数据
const data_list  = ref([
  {name:'身份：',text:'买家',button_text:'申请为卖家',type:'danger',fun:apply_seller,select_val : '买家'},
  {name:'地址',text:'***',button_text:'修改地址',type:'primary',fun:addre_set,select_val : '***'}
])

const select = ref(false)

onMounted(async ()=>{
  const formdata = new FormData
  formdata.append('token',token)

  const res = await Axios.post('/user_data',formdata)
  const apply_address = await Axios.post('/get_address_apply',formdata)
  if (res.status == 200){
    if (res.data.current){
      console.log(res.data);
      user_name.value = res.data.data[0]||'***'
      data_list.value[0]['text'] = (res.data.data[1] == 1)?'卖家':'买家'
      select.value = data_list.value[0]['text'] == '卖家'
    }
  }
  if (apply_address.status == 200){
    if (apply_address.data.current){
      console.log(12);

      // oxlint-disable-next-line no-constant-binary-expression
      data_list.value[1]['text'] = `${apply_address.data.data[2]}-${apply_address.data.data[3]}-${apply_address.data.data[4]}` || '***'
      // oxlint-disable-next-line no-constant-binary-expression
      data_list.value[1]['select_val'] = `${apply_address.data.data[2]}-${apply_address.data.data[3]}-${apply_address.data.data[4]}`||'***'
    }
  }

})

// 进入卖家端登录页
function buyer_sing (){
  router.push('/buyer_sing')
}



// 设置组件名称
defineOptions({
  name:'Set'
})


</script>
<style scoped>
*{
  margin-left: 10px;
  margin-top: 5px;
}
.button_style{
  display: flex;
}
</style>
