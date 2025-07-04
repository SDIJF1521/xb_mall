<template>
  <el-container class="login-container">
    <el-header class="header-content">
      <div class="logo-container">
        <span class="logo-text">小白的个人商城</span>
        <span class="admin-text">管理后台</span>
      </div>
    </el-header>
    <el-main class="login-main">
      <el-card class="login-card" shadow="hover">
        <div class="login-title">管理员登录</div>
        <el-form 
          ref="loginFormRef" 
          :model="loginForm" 
          :rules="loginRules" 
          label-width="0"
          class="login-form"
        >
          <el-form-item prop="username">
            <el-input 
              v-model="loginForm.username" 
              prefix-icon="User" 
              placeholder="请输入用户名"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input 
              v-model="loginForm.password" 
              prefix-icon="Lock" 
              type="password" 
              placeholder="请输入密码"
              @keyup.enter.native="handleLogin"
              show-password
            />
          </el-form-item>
          <el-form-item prop="verifyCode">
            <el-input 
              v-model="loginForm.verifyCode" 
              prefix-icon="VerificationCode" 
              placeholder="请输入验证码"
              style="width: 60%; margin-right: 10px"
            />
            <VerifyCode 
              ref="verifyCodeRef"
              @update:verifyCode="handleVerifyCodeUpdate"
            />
          </el-form-item>
          <el-form-item>
            <el-button 
              type="primary" 
              :loading="loading"
              @click="handleLogin"
              class="login-button"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-main>
    <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted} from 'vue';
import VerifyCode from './content/VerifyCode.vue';
import { ElMessage } from 'element-plus';
import axios, { Axios } from 'axios';
import router from '@/router';

defineOptions({
  name: 'ManagementLogin',
})

const loginFormRef = ref();
const loginForm = reactive({
  username: '',
  password: '',
  verifyCode: '',
});
const verifyCodeText = ref('');
const verifyCodeRef = ref();
const loading = ref(false);
const AxiosInstance = axios.create({
  baseURL: 'http://localhost:8000/api'
});
const loginRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在6-20个字符', trigger: 'blur' }
  ],
  verifyCode: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { min: 4, max: 4, message: '验证码长度为4位', trigger: 'blur' }
  ]
});

onMounted(() => {
  document.documentElement.classList.add('dark');
});

const handleVerifyCodeUpdate = (code: string) => {
  verifyCodeText.value = code;
};

const handleLogin = () => {
  if (!loginFormRef.value) return;
  loginFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      // 验证验证码
      if (loginForm.verifyCode.toLowerCase() !== verifyCodeText.value.toLowerCase()) {
        ElMessage.error('验证码错误');
        return;
      }

      loading.value = true;
      try {
        const formData = new URLSearchParams();
        formData.append('grant_type', 'password');
        formData.append('username', loginForm.username);
        formData.append('password', loginForm.password);
        AxiosInstance.post('/manage_sign_in',formData)
        .then(ref=>{
          if (ref.status === 200 && ref.data.current){
            localStorage.setItem('admin_access_token', `Bearer ${ref.data.token}`)
            ElMessage.success(ref.data.msg);
            router.push('/management')
          }else{
            ElMessage.error(ref.data.msg)
            
          }
        })
       
        // 登录成功后通常会重定向到管理后台首页
        // router.push('/management/dashboard');
      } catch (error) {
        ElMessage.error('登录失败，请检查用户名和密码');
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.login-container {
  height: 100vh;
}

.header-content {
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 80px;

}

.logo-container {
  display: flex;
  align-items: center;
}

.logo-text {
  font-size: 24px;
  font-weight: bold;
  margin-right: 10px;
}

.admin-text {
  font-size: 18px;
  color: #909399;
}

.login-main {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.login-card {
  width: 400px;
  max-width: 90%;
}

.login-title {
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 20px;
}

.login-form {
  padding: 20px;
}

.verify-code-image {
  height: 40px;
  cursor: pointer;
  vertical-align: middle;
}

.login-button {
  width: 100%;
}

.footer-content {
  text-align: center;
  color: darkgray;
  padding: 10px;
}
</style>