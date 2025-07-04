<template>
    <el-container>
      <el-header>
        <AppNavigation/>
      </el-header>
      <el-main class="main">
          <div>
              <el-input
                      v-model="Email"
                      style="width: 500px"
                      size="large"
                      placeholder="请输入邮箱"
                      @blur="Email_verification"
                      clearable
                  />
              <div v-if="emailError" class="error-message">{{ emailError }}</div>
          </div>
          
          <div>
              <el-input
                  v-model="password"
                  style="width: 500px"
                  size="large"
                  type="password"
                  placeholder="请输入密码"
                  @blur="password_verification"
                  show-password
              />
              <div v-if="passwordError" class="error-message">{{ passwordError }}</div>
          </div>

          <div>
              <el-input
                  v-model="repeat_password"
                  style="width: 500px"
                  size="large"
                  type="password"
                  placeholder="重复密码"
                  @blur="repeat_password_verification"
                  show-password
              />
              <div v-if="repeat_passwordError" class="error-message">{{ repeat_passwordError }}</div>
          </div>
          <div>
              <div class="code">
                  <el-input
                      v-model="code"
                      style="width: 380px"
                      size="large"
                      placeholder="请输入验证码"
                      @blur="code_regex"
                      show-password
                  />
                  <el-button 
                      type="primary" 
                      @click="sendVerificationCode" 
                      plain
                      :disabled="countdown > 0"
                  >
                      {{ countdown > 0 ? `重新发送(${countdown}s)` : '发送验证码' }}
                  </el-button>
              </div>
              <div v-if="codeError" class="error-message">{{ codeError }}</div>
          </div>
          <el-button type="info" style="width: 400px;" @click="reset" round>提交</el-button>
      </el-main>
      <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script>
import AppNavigation from '@/moon/navigation.vue'
import { ElMessage } from 'element-plus';
import axios from 'axios';
export default{
    name:'PasswordReset',
    data(){
        return{
            Email:'',
            code:'',
            password:'',
            repeat_password:'',
            emailError: '',
            passwordError:'',
            repeat_passwordError:'',
            codeError: '',
            countdown: 0,
            timer: null,
            Axios : axios.create({baseURL: 'http://127.0.0.1:8000/api'})
        }
    },
    components:{
        AppNavigation
    },
    beforeDestroy() {
        // 组件销毁前清除定时器
        if (this.timer) {
            clearInterval(this.timer);
        }
    },
    methods:{
        // 验证邮箱格式
        Email_verification(){
            const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            this.Email = this.Email.trim();
            
            if (this.Email === '') {
                this.emailError = '请输入邮箱地址';
                return false;
            }
            
            if (!emailRegex.test(this.Email)) {
                this.emailError = '邮箱格式不正确';
                return false;
            }
            
            this.emailError = '';
            return true;
        },

        // 验证密码格式
        password_verification(){
            const hasNumber = /\d/.test(this.password);
            const hasLetter = /[a-zA-Z]/.test(this.password);
            this.password = this.password.trim();
            console.log(this.password.length);
            if (this.password.length === 0){
                this.passwordError = '密码不能为空';
                return false;
            }else if (this.password.length < 8 ){
                this.passwordError = '密码长度不能小于8位';
                return false;
            }else if (!hasLetter){
                this.passwordError = '密码必须包含至少一个英文';
                return false;
            }else if(!hasNumber){
                this.passwordError = '密码必须包含数字';
                return false;
            }
            this.passwordError = '';
            return true;
        },

        //验证重复密码
        repeat_password_verification(){
            this.repeat_password = this.repeat_password.trim();
            if (this.repeat_password.length === 0){
                this.repeat_passwordError = '请再次输入密码';
                return false;
            }else if(this.repeat_password !== this.password){
                this.repeat_passwordError = '两次输入的密码不一致';
                return false;
            }
            this.repeat_passwordError = '';
            return true;
        },

        //验证码格式验证
        code_regex(){
            const codeRegex = /^\d{4,6}$/;
            console.log(codeRegex.test(this.code));
            if (!codeRegex.test(this.code)){
                this.codeError = '验证码格式不对（4-6位数字）';
                return false;
            }
            this.codeError = '';
            return true;
        },

        // 发送验证码并启动倒计时
        async sendVerificationCode() {
            // 先验证邮箱
            if (!this.Email_verification()) {
                return;
            }
            
            // 已发送则不重复发送
            if (this.countdown > 0) {
                ElMessage.info('请等待倒计时结束');
                return;
            }
            
            // 发送验证码请求
            try {
                const response = await this.Axios.get('/verification_code', {
                    params: {
                        email: this.Email
                    }
                });
                
                ElMessage.success('验证码发送成功，请查收邮箱');
                console.log('验证码发送成功:', response.data);
                
                // 启动倒计时
                this.countdown = 60;
                this.timer = setInterval(() => {
                    this.countdown--;
                    if (this.countdown <= 0) {
                        clearInterval(this.timer);
                        this.timer = null;
                    }
                }, 1000);
            } catch (error) {
                ElMessage.error('验证码发送失败，请稍后再试');
                console.error('验证码发送失败:', error);
                this.codeError = '验证码发送失败，请稍后再试';
            }
        },

        // 重置密码
        async reset(){
            console.log('开始密码重置流程');
            console.log('Email:', this.Email);
            console.log('Code:', this.code);
            console.log('Password:', this.password);
            
            // 全面验证所有参数
            if (!this.Email_verification()) {
                return;
            }
            
            if (!this.password_verification()) {
                return;
            }
            
            if (!this.repeat_password_verification()) {
                return;
            }
            
            if (!this.code_regex()) {
                return;
            }
            
            try {
                // 验证验证码
                const verifyResponse = await this.Axios({
                    method: 'post',
                    url: '/verify_code',
                    params: {
                        email: this.Email,
                        code: this.code
                    }
                });
                
                console.log('验证码验证成功:', verifyResponse.data);
                
                if (verifyResponse.status === 200 && verifyResponse.data.data.access_token) {
                    const formdata = new FormData();
                    formdata.append('email', this.Email);
                    formdata.append('user_password', this.password);
                    formdata.append('captcha', `Bearer ${verifyResponse.data.data.access_token}`);
                    
                    try {
                        // 提交密码重置请求
                        const passwordResponse = await this.Axios.patch('/password_reset', formdata);
                        
                        if (passwordResponse.status === 200 && passwordResponse.data.current) {
                            ElMessage.success('密码修改成功');
                            this.$router.push('/register');
                        } else {
                            ElMessage.error('密码重置失败，请稍后再试');
                            console.error('密码重置失败:', passwordResponse.data);
                        }
                    } catch (patchError) {
                        ElMessage.error('密码重置请求失败');
                        console.error('密码重置请求错误:', patchError);
                        
                        if (patchError.response) {
                            console.error('服务器返回错误:', patchError.response.data);
                            const errorMsg = patchError.response.data.errors 
                                ? Object.values(patchError.response.data.errors).join('，') 
                                : '请检查输入信息';
                            ElMessage.error(`密码重置失败：${errorMsg}`);
                        }
                    }
                } else {
                    ElMessage.error('验证码验证失败，请检查邮箱和验证码');
                    console.error('验证码验证失败，状态码:', verifyResponse.status);
                }
            } catch (error) {
                ElMessage.error('验证码验证失败，请检查邮箱和验证码');
                console.error('验证码验证错误:', error);
                
                if (error.response) {
                    console.error('错误状态码:', error.response.status);
                    console.error('错误信息:', error.response.data);
                    
                    const errorMsg = error.response.data.errors 
                        ? Object.values(error.response.data.errors).join('，') 
                        : '请检查邮箱和验证码是否正确';
                    ElMessage.error(`验证失败：${errorMsg}`);
                }
            }
        }
    }
}
</script>
<style scoped>
.footer-content {
  text-align: center; /* 文字内容水平居中 */
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
  padding: 30px;
}
.main >* {
    margin-top: 15px;
    width: 100%;
    max-width: 500px;
}

.code{
    display: flex;
    width: 100%;
    max-width: 500px;
}
.code >* {
    margin-left: 10px;
    flex: 1;
}
.code > el-input {
    max-width: 380px;
}

.error-message {
    color: #f56c6c;
    font-size: 14px;
    margin-top: 5px;
    width: 100%;
    text-align: left;
}
</style>