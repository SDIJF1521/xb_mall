<template>
    <div class="register-form">
        <!-- 标题盒子 -->
        <div class="title-box">
            <h1>注册</h1>
        </div>
        <!-- 输入框盒子 -->
        <div class="input-box">
            <!-- 用户名输入框 -->
            <el-input
                v-model="username"
                style="width: 240px; margin-bottom: 15px;"
                placeholder="用户名"
                clearable
                @blur="validateUsername"
                :class="{ 'is-invalid': usernameError }"
            />
            <!-- 用户名错误提示 -->
            <div v-if="usernameError" class="error-message">{{ usernameError }}</div>
            
            <!-- 密码框 -->
            <el-input
                v-model="password"
                style="width: 240px; margin-bottom: 15px;"
                type="password"
                placeholder="请输入密码"
                show-password
                @blur="validatePassword"
                :class="{ 'is-invalid': passwordError }"
            />
            <!-- 密码错误提示 -->
            <div v-if="passwordError" class="error-message">{{ passwordError }}</div>
            
            <!-- 重复密码框 -->
             <el-input
                v-model="repetition_password"
                style="width: 240px; margin-bottom: 15px;"
                type="password"
                placeholder="请再次输入密码"
                show-password
                @blur="validatePasswordMatch"
                :class="{ 'is-invalid': passwordMatchError }"
            />
            <!-- 重复密码错误提示 -->
            <div v-if="passwordMatchError" class="error-message">{{ passwordMatchError }}</div>
            
            <!-- 邮箱输入框 -->
            <el-input
                v-model="email"
                style="width: 240px; margin-bottom: 5px;"
                placeholder="邮箱"
                clearable
                :class="{ 'is-invalid': emailError }"
                @blur="validateEmail"
            />
            <!-- 邮箱错误提示 -->
            <div v-if="emailError" class="error-message">{{ emailError }}</div>
            
            <div class="verify-code-container">
                <el-input 
                    v-model="verification_code" 
                    style="width: 150px;" 
                    placeholder="验证码"
                    @blur="validateVerificationCode"
                    :class="{ 'is-invalid': verificationCodeError }"
                />
                <!-- 验证码错误提示 -->
                
                <el-button 
                    @click="send" 
                    :disabled="isSending || !!emailError || !email"
                    :class="{ 'is-disabled': isSending }"
                >
                    {{ button_text }}
                </el-button>
            </div>
            <div v-if="verificationCodeError" class="error-message">{{ verificationCodeError }}</div>
        </div>
        <!-- 按钮盒子 -->
        <div class="btn-box">
            <button @click="handleRegister" :disabled="hasErrors">注册</button>
        </div>
    </div>
</template>
<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
const url = 'http://127.0.0.1:8000/api'
const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
export default {
    name: 'SignIn',
    props:{
        showLogin:{
            type:Boolean,
            default: false
        }
    },
    data() {
        return {
            username: '',
            password: '',
            repetition_password: '',
            email: '',
            verification_code: '',
            button_text: '获取验证码',
            usernameError: '',
            passwordError: '',
            passwordMatchError: '',
            emailError: '',
            verificationCodeError: '',
            isSending: false,
            countdown: 0
        }
    },
    computed: {
        // 检查是否有任何验证错误
        hasErrors() {
            return !!(
                this.usernameError || 
                this.passwordError || 
                this.passwordMatchError || 
                this.emailError || 
                this.verificationCodeError
            );
        }
    },
    methods: {
        // 验证用户名
        validateUsername() {
            // 去除首尾空格
            this.username = this.username.trim();
            
            if (this.username === '') {
                this.usernameError = '用户名不能为空';
                return false;
            }
            
            if (this.username.includes(' ')) {
                this.usernameError = '用户名不能包含空格';
                return false;
            }
            this.usernameError = '';
            return true;
        },
        
        // 验证密码
        validatePassword() {
            // 去除首尾空格
            this.password = this.password.trim();
            
            if (this.password === '') {
                this.passwordError = '密码不能为空';
                return false;
            }
            
            if (this.password.includes(' ')) {
                this.passwordError = '密码不能包含空格';
                return false;
            }
            
            if (this.password.length < 8) {
                this.passwordError = '密码长度不能少于8个字符';
                return false;
            }
            
            // 验证密码必须包含数字和英文字母
            const hasNumber = /\d/.test(this.password);
            const hasLetter = /[a-zA-Z]/.test(this.password);
            
            if (!hasNumber) {
                this.passwordError = '密码必须包含数字';
                return false;
            }
            
            if (!hasLetter) {
                this.passwordError = '密码必须包含英文字母';
                return false;
            }
            
            // 验证密码匹配
            if (this.repetition_password) {
                this.validatePasswordMatch();
            }
            
            this.passwordError = '';
            return true;
        },
        
        // 验证重复密码
        validatePasswordMatch() {
            // 去除首尾空格
            this.repetition_password = this.repetition_password.trim();
            
            if (this.repetition_password === '') {
                this.passwordMatchError = '请再次输入密码';
                return false;
            }
            
            if (this.repetition_password !== this.password) {
                this.passwordMatchError = '两次输入的密码不一致';
                return false;
            }
            
            this.passwordMatchError = '';
            return true;
        },
        
        // 验证邮箱格式
        validateEmail() {
            // 去除首尾空格
            this.email = this.email.trim();
            
            if (this.email === '') {
                this.emailError = '请输入邮箱地址';
                return false;
            }
            
            if (!emailRegex.test(this.email)) {
                this.emailError = '邮箱格式不正确';
                return false;
            }
            
            this.emailError = '';
            return true;
        },
        
        // 验证验证码
        validateVerificationCode() {
            // 去除首尾空格
            this.verification_code = this.verification_code.trim();
            
            if (this.verification_code === '') {
                this.verificationCodeError = '请输入验证码';
                return false;
            }
            
            // 假设验证码是4-6位数字
            if (!/^\d{4,6}$/.test(this.verification_code)) {
                this.verificationCodeError = '验证码格式不正确';
                return false;
            }
            
            this.verificationCodeError = '';
            return true;
        },
        
        // 发送验证码
        async send() {
            // 先验证邮箱格式
            if (!this.validateEmail()) {
                return;
            }
            
            this.isSending = true;
            
            await axios({
                method: 'get',
                url: url + '/verification_code',
                params: {
                    email:this.email
                }
            })
            .then(res => {
                console.log(res.data);
                ElMessage.success('验证码发送成功请注意邮箱')
                // 开始倒计时
                this.countdown = 60;
                this.button_text = `重新发送(${this.countdown}s)`;
                if (res.data.message == '验证码已发送'){
                    this.startCountdown('验证码已发送请注意邮箱');
                }else{
                    this.startCountdown(res.data.message);
                }
            })
            .catch(err => {
                ElMessage.error('验证码发送失败')
                console.log('发送验证码失败:', err);
                this.emailError = '发送验证码失败，请稍后再试';
            })
            .finally(() => {
                this.isSending = false;
            });
        },
        
        // 开始倒计时
        startCountdown() {
            const timer = setInterval(() => {
                this.countdown--;
                this.button_text = `重新发送(${this.countdown}s)`;
                
                if (this.countdown <= 0) {
                    clearInterval(timer);
                    this.button_text = '获取验证码';
                }
            }, 1000);
        },
        
        // 验证所有字段
        validateAllFields() {
            let isValid = true;
            
            if (!this.validateUsername()) isValid = false;
            if (!this.validatePassword()) isValid = false;
            if (!this.validatePasswordMatch()) isValid = false;
            if (!this.validateEmail()) isValid = false;
            if (!this.validateVerificationCode()) isValid = false;
            
            return isValid;
        },
        
        // 注册逻辑 - 暂时保留空函数
        async handleRegister() {
            // 验证所有字段
            if (!this.validateAllFields()) {
                console.log('表单验证失败，阻止提交');
                return;
            }

            // 验证验证码
            await axios({
                method: 'post',
                url: url + '/verify_code',
                params: {
                email: this.email,
                code: this.verification_code
                }
            })
            .then(async res =>{
                if (res.data.message == '验证码错误或已过期'){
                    ElMessage.error(res.data.message)
                }
                console.log(res.data.message);
                if (res.data.code == 200) {
                    console.log(`Bearer ${res.data.data.access_token}`);
                    await axios({
                        method: 'post',
                        url: url + '/register',
                        data:{
                            email: this.email,
                            user_name: this.username,
                            user_password: this.password,
                            captcha: `Bearer ${res.data.data.access_token}`
                            },
                        headers: {
                                'Content-Type': 'application/x-www-form-urlencoded'  // 设置正确的 Content-Type
                                }
                    })
                    .then(res =>{
                        console.log(res.data);
                        if (res.status == 200){
                            if (res.data.current){
                                ElMessage.success(res.data.msg)
                                this.username=''
                                this.password=''
                                this.repetition_password=''
                                this.email=''
                                this.verification_code=''
                            }else{
                                ElMessage.error(res.data.msg)
                            }
                        }
                        
                        
                    })
                }
            })
            .catch(err => {
                console.log('请求异常', err);
                }
            )
            console.log('所有字段验证通过，可以提交注册表单');
            console.log('表单数据:', {
                email: this.email,
                username: this.username,
                password: this.password,
                verification_code: this.verification_code
            });

        }
    }
}
</script>
<style scoped>
/* 样式保持不变 */
.register-form {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 30px;
    border-radius: 8px;
    width: 320px;
    margin: 0 auto;
}

.title-box {
    margin-bottom: 25px;
}

.title-box h1 {
    font-size: 24px;
    margin: 0;
}

.input-box {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.el-input {
    height: 40px;
}

/* 添加错误样式 */
.is-invalid .el-input__inner {
    border-color: #f56c6c;
}

.error-message {
    color: #f56c6c;
    font-size: 12px;
    margin-bottom: 10px;
    width: 240px;
    text-align: left;
}

.verify-code-container {
    display: flex;
    gap: 10px;
    width: 240px;
}

.btn-box {
    width: 100%;
    margin-top: 25px;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.btn-box button {
    background-color: #409eff;
    border: none;
    border-radius: 4px;
    padding: 10px 16px;
    cursor: pointer;
    width: 100%;
    font-size: 16px;
    transition: background-color 0.2s;
}

.btn-box button:hover {
    background-color: #3a8ee6;
}

.btn-box p {
    margin-top: 15px;
    color: #409eff;
    cursor: pointer;
    font-size: 14px;
    text-decoration: underline;
}

.btn-box p:hover {
    color: #3a8ee6;
}
</style>
