<template>
    <el-container>
        <el-main>
            <div class="box">
                
                <!-- 注册表单 -->
                <div class="register-container">
                    <SignIn @toggleForm="toggleForm" />
                </div>
                
                <!-- 登录表单 -->
                <div class="login-container">
                    <LogIn @toggleForm="toggleForm" />
                </div>
                
                <!-- 覆盖层，初始显示在注册表单上 -->
                <div 
                    class="pre-box" 
                    :class="{ 'slide-right': showLogin }"
                    @click="toggleForm"
                >
                    <div class="pre-content">
                        <h1>WELCOME</h1>
                        <p>JOIN US!</p>
                        <button class="pre-btn" @click.stop="toggleForm">
                            {{ showLogin ? '已有账号' : '创建账号' }}
                        </button>
                    </div>
                </div>
            </div>
        </el-main>
        <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
    
</template>
<script>
import LogIn from './content/log_in.vue'
import SignIn from './content/sign_in.vue'
import { ref, computed } from 'vue';
export default{
    name:'Register',
    components:{
        LogIn,
        SignIn
    },
    data() {
        return {
            showLogin: false
        }
    },

    setup() {
        const darkMode = ref(false);
        const initTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme === 'dark') {
            darkMode.value = true;
            document.documentElement.classList.add('dark');
        }
        };
    
    // 初始化
    initTheme();
    },
    methods: {
        // 统一的表单切换方法
        toggleForm() {
            this.showLogin = !this.showLogin;
        },
        
        // 兼容旧的事件处理
        showLoginForm() {
            this.showLogin = true;
        },
        
        showRegisterForm() {
            this.showLogin = false;
        }
    }
}
</script>
<style scoped>
.box {
    display: flex;
    width: 1000px;
    height: 600px;
    margin: 50px auto;
    border-radius: 12px;
    overflow: hidden;
    position: relative;
    
    /* 增强盒子轮廓 */
    border: 2px solid rgba(64, 158, 255, 0.2);
    box-shadow: 0 20px 50px rgba(64, 158, 255, 0.15), 
                0 10px 30px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
}

.box:hover {
    box-shadow: 0 25px 55px rgba(64, 158, 255, 0.2), 
                0 15px 35px rgba(0, 0, 0, 0.08);
    transform: translateY(-5px);
}

.register-container, .login-container {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
}

/* 表单容器轮廓增强 */
.register-container::before, .login-container::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: calc(100% - 40px);
    height: calc(100% - 40px);
    border-radius: 8px;
    border: 1px solid rgba(224, 230, 237, 0.5);
    pointer-events: none;
    z-index: 1;
}

.pre-box {
    position: absolute;
    top: 0;
    left: 0;
    width: 50%;
    height: 100%;
    background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    transition: transform 0.6s ease-in-out;
    z-index: 10;
    
    /* 增强覆盖层轮廓 */
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.pre-box.slide-right {
    transform: translateX(100%);
}

.pre-content {
    text-align: center;
    padding: 40px;
    z-index: 20;
}

.pre-content h1 {
    font-size: 32px;
    margin-bottom: 20px;
    letter-spacing: 2px;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.pre-content p {
    font-size: 18px;
    margin-bottom: 40px;
    opacity: 0.9;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.pre-btn {
    background-color: white; /* 添加背景色为白色 */
    color: #409eff;
    border: none;
    border-radius: 25px;
    padding: 12px 30px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.pre-btn:hover {
    background-color: #f0f0f0; /* 悬停时背景色变浅 */
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
}

.footer-content {
  text-align: center; /* 文字内容水平居中 */
  color: darkgray;
}
</style>
