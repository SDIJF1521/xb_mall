<template>
    <el-container>
        <el-header>
            <div class="management-navigation">
                <h2 class="title_night">小白的商城-店铺删除页</h2>
            </div>
        </el-header>
        <el-main>
          <el-dialog
            title="确认删除店铺"
            v-model="dialogVisible"
            width="30%"
            >
            <p>您确定要删除该店铺吗？此操作不可撤销。</p>
            <span slot="footer" class="dialog-footer">
              <el-button @click="dialogVisible = false">取消</el-button>
              <el-button type="primary" @click="confirmDelete">确认删除</el-button>
            </span>
          </el-dialog>
          <el-table :data="filterTableData" style="width: 100%">
            <!-- 关键修改：格式化创建时间列 -->
            <el-table-column label="创建时间">
                <template #default="scope">
                    <!-- 使用dayjs格式化时间，格式可自定义 -->
                    {{ dayjs(scope.row.creation_time).format('YYYY年MM月DD日') }}
                </template>
            </el-table-column>
            <el-table-column label="店铺名称" prop="mall_name" />
            <el-table-column label="店铺id" prop="id" />
            <el-table-column align="right">
              <template #header>
                <el-input v-model="name" size="small" placeholder="请输入店铺名称" @keyup.enter="require_list"/>
              </template>
              <template #default="scope">
                        <el-button size="small" @click="delete_mall(scope.row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-main>
        <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import BuyerTheme from '@/moon/buyer_theme';
import axios from 'axios';
import dayjs from 'dayjs'; // 已导入，直接使用
import { ElMessage } from 'element-plus'; // 引入 Element Plus 的消息提示组件

// 定义组件名称
defineOptions({
    name: 'BuyerDeleteMall'
})

const filterTableData = ref([]);
const search = ref('');
const name = ref('')
const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api'
})
const token = localStorage.getItem("buyer_access_token")
const mall_id =ref(-1);
// 初始化主题和数据
onMounted(async()=>{
    new BuyerTheme().toggleTheme(true)
    const formdata = new FormData()
    // 使用最新的token
    const currentToken = localStorage.getItem("buyer_access_token")
    formdata.append('token', currentToken || '')
    const response = await Axios.post('get_mall_name', formdata)
    filterTableData.value = response.data.current ? response.data.mall_name : []
})

const dialogVisible = ref(false);

// 搜索功能
async function require_list(){
    const formdata = new FormData()
    // 使用最新的token（可能已更新）
    const currentToken = localStorage.getItem("buyer_access_token")
    formdata.append('token', currentToken || '')
    // 如果搜索框为空，不传递mall_name参数（或根据后端需求调整）
    if (name.value) {
        formdata.append('mall_name', name.value)
    }
    const response = await Axios.post('get_mall_name', formdata)
    console.log(response.data.current ? response.data.mall_name : []);

    filterTableData.value = response.data.current ? response.data.mall_name : []
};

//删除按钮功能
async function delete_mall(mall_id_select: number){
    dialogVisible.value = true;
    mall_id.value = mall_id_select;
    console.log(dialogVisible.value);

}

// 确认删除函数
async function confirmDelete() {
    const formdata = new FormData()
    formdata.append("token",token || '')
    formdata.append("mall_id",mall_id.value.toString())
    
    try {
        const res = await Axios.delete('/buyer_delete_mall',{data:formdata})
        
        if(res.data.current){
            // 检查并更新新的token（如果后端返回了新token）
            let tokenUpdated = false
            if (res.data.token) {
                // 更新为新token，格式：Bearer {token}
                const tokenType = res.data.token_type || 'bearer'
                const newToken = `${tokenType.charAt(0).toUpperCase() + tokenType.slice(1)} ${res.data.token}`
                localStorage.setItem('buyer_access_token', newToken)
                
                tokenUpdated = true
                console.log('Token已更新，新token已移除删除的店铺信息')
            }
            
            ElMessage.success(tokenUpdated ? '删除成功，Token已自动更新' : '删除成功')
            dialogVisible.value = false;
            mall_id.value = -1;
            // 刷新列表（使用最新的token）
            await require_list()
        }else{
            ElMessage.error(res.data.msg || '删除失败')
            dialogVisible.value = false;
            mall_id.value = -1;
        }
    } catch (error) {
        console.error('删除店铺失败:', error)
        ElMessage.error('删除店铺失败，请稍后重试')
        dialogVisible.value = false;
        mall_id.value = -1;
    }
}
</script>

<style scoped>
/* 样式不变 */
.footer-content {
    font-size: 14px;
    color: #999;
    text-align: center;
    padding: 20px 0;
}

.management-navigation {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0 20px;
}
.title_night{
    background: linear-gradient(to right, #dc5127, #9c6edd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    color: transparent;
}
.title_daytime{
    color: #000;
}

.el-header {
    border-bottom: 1px solid #575859;
    padding-bottom: 10px;
    margin-bottom: 10px;
}
</style>
