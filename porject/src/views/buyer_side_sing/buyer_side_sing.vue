<template>
    <div class="login-wrapper">
        <div class="login-background">
            <div class="bg-circle circle-1"></div>
            <div class="bg-circle circle-2"></div>
            <div class="bg-circle circle-3"></div>
        </div>

        <div class="login-container">
            <div class="login-box">
                <div class="login-header">
                    <div class="icon-wrapper">
                        <el-icon class="login-icon"><User /></el-icon>
                    </div>

                    <h2>欢迎登录</h2>
                    <p class="login-subtitle">小白的商城管理系统</p>
                </div>

                <el-form :model="from_data" class="login-form" @submit.prevent="handleLogin">
                    <el-form-item>
                        <el-input
                            v-model="from_data.user_name"
                            placeholder="请输入用户名"
                            clearable
                            size="large"
                            :prefix-icon="User"
                            class="custom-input"
                        />
                    </el-form-item>
                    <el-form-item>
                        <el-input
                            v-model="from_data.password"
                            type="password"
                            placeholder="请输入密码"
                            show-password
                            size="large"
                            :prefix-icon="Lock"
                            @keyup.enter="handleLogin"
                            class="custom-input"
                        />
                    </el-form-item>
                    <el-form-item v-if = "from_data.type == '2'">
                      <el-input
                          v-model="from_data.mall_id"
                          placeholder="请输入店铺id"
                          clearable
                          size="large"
                          :prefix-icon="User"
                          class="custom-input"
                        />
                    </el-form-item>
                    <el-form-item>
                        <el-select
                            v-model="from_data.type"
                            placeholder="请选择身份"
                            size="large"
                            class="custom-select"
                            clearable
                        >
                            <el-option
                                v-for="item in options"
                                :key="item.value"
                                :label="item.label"
                                :value="item.value"
                            >
                                <el-icon><Star /></el-icon>
                                <span style="margin-left: 8px">{{ item.label }}</span>
                            </el-option>
                        </el-select>
                    </el-form-item>
                </el-form>
                <el-button
                        type="primary"
                        size="large"
                        class="login-button"
                        @click="handleLogin"
                        native-type="submit"
                    >
                        <el-icon><Right /></el-icon>
                        <span>立即登录</span>
                    </el-button>

            </div>
        </div>
        <div class="footer-content">版权所有 © [小白的商城]，保留所有权利。</div>
    </div>
</template>
<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { User, Lock, Star, Right } from '@element-plus/icons-vue'
import {ElMessage} from 'element-plus'
import axios from 'axios';
import router from '@/router'


const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
    timeout: 10000
})

const from_data = reactive({
    user_name: '',
    password: '',
    mall_id:'',
    type: ''

})

const options = [
    {
        value:'1',
        label: '店长',
    },
    {
        value:'2',
        label: '店员',
    }
]

const handleLogin = async () => {
    const url_from_data = new FormData()
    url_from_data.append('user',from_data.user_name)
    url_from_data.append('password',from_data.password)
    if (from_data.type == '2'){
        url_from_data.append('mall_id',from_data.mall_id)
    }
    url_from_data.append('station',from_data.type)
    Axios.post('/buyer_side_token',url_from_data)
    .then(async res=>{
        if (res.status ==200){
            if (res.data.current){
                localStorage.setItem('buyer_access_token',`Bearer ${res.data.token}`)
                Axios.post('/buyer_side_verify?token='+localStorage.getItem('buyer_access_token'))

                .then(res=>{
                    if (res.status ==200){
                        if (res.data.current){
                            ElMessage.success('登录成功')

                            router.push('/buyer_index')
                        }else{
                            ElMessage.error('登录失败')
                        }
                    }else{
                        ElMessage.error('登录失败')
                    }

                })


            }else{
                ElMessage.error('登录失败')
            }

        }
    })

}

onMounted(() => {
    document.documentElement.classList.add('dark')
})
const token = ref(async ()=>{
    const url_from_data = new FormData()
    url_from_data.append('user',from_data.user_name)
    url_from_data.append('password',from_data.password)
    url_from_data.append('station ',from_data.type)


    Axios.post('/buyer_side_token',url_from_data)


})
defineOptions({ name: 'BuyerSideSing' })
</script>
<style scoped>
    .login-wrapper {
        min-height: 94vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 20px;
    }

    .login-container {
        width: 100%;
        max-width: 400px;
    }

    .login-box {
        background: white;
        padding: 60px 40px;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        animation: fadeInUp 0.6s ease-out;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .login-header {
        text-align: center;
        margin-bottom: 40px;
    }

    .login-icon {
        font-size: 48px;
        color: #667eea;
        margin-bottom: 20px;
        animation: bounce 1s ease-in-out;
    }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }

    .login-header h2 {
        color: #333;
        font-size: 28px;
        font-weight: 600;
        margin: 0 0 10px 0;
    }

    .login-subtitle {
        color: #666;
        font-size: 14px;
        margin: 0;
    }

    .login-form {
        margin-bottom: 30px;
    }

    .login-form .el-form-item {
        margin-bottom: 25px;
    }

    .login-button {
        width: 100%;
        height: 48px;
        font-size: 16px;
        font-weight: 500;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        transition: all 0.3s ease;
    }

    .login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }

    .login-button:active {
        transform: translateY(0);
    }


    .footer-content {
        color: rgba(255, 255, 255, 0.8);
        font-size: 14px;
        margin-top: 50px;
        text-align: center;
        transform: translateY(-5%);


    }

    /* 响应式设计 */
    @media (max-width: 480px) {
        .login-box {
            padding: 40px 30px;
            margin: 10px;
        }

        .login-header h2 {
            font-size: 24px;
        }
    }
</style>
