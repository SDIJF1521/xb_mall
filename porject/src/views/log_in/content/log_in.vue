<template>
    <div class="login-form">
        <!-- 标题盒子 -->
        <div class="title-box">
            <h1>登录</h1>
        </div>
        <!-- 输入框盒子 -->
        <div class="input-box">
            <!-- 输入框 -->
            <el-input
                v-model="username"
                style="width: 320px"
                placeholder="用户名"
                clearable
            />
            
            <!-- 密码框 -->
            <el-input
            v-model="password"
            style="width: 320px"
            type="password"
            placeholder="密码"
            show-password
            />

        </div>

        <el-text class="mx-1" type="primary" @click = 'Password_reset' >忘记密码</el-text>


        <!-- 按钮盒子 -->
        <div class="btn-box">
            <button to="/password_reset" @click="log_in">登录</button>
        </div>
    </div>
</template>
<script>
import axios from 'axios';
import router from '../../../router';
import { ElMessage } from 'element-plus';
export default {
    name:'LogIn',
    data() {
        return{
        username:'',
        password:''
        }
    },
    methods: {
        log_in(){
            const url = 'http://127.0.0.1:8000/api';
            //后续学习可参考部分
            const formData = new URLSearchParams();
            formData.append('grant_type', 'password');
            formData.append('username', this.username);
            formData.append('password', this.password);
            axios({
                method: 'post',
                url: url + '/token',
                data: formData,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })
            .then(async response => {
                console.log('登录成功:', response.data);
                // 处理返回的token
                if (response.status == 200 && response.data.token != null){
                    localStorage.setItem('access_token', `Bearer ${response.data.token}`)
                    const formData = new FormData();
                    formData.append('token', `Bearer ${response.data.token}`); 

                    // 发送请求
                    await axios({
                        method: 'post',
                        url: url + '/user_sign_in',
                        data: formData
                    })
                    .then(res =>{
                        // console.log(res.data);
                        if (res.status == 200){
                            if (res.data['msg'] == '验证通过'){
                                ElMessage.success('登陆成功')
                                router.push('/personal_center')
                                
                            }else{
                                ElMessage.error(res.data.msg)
                            }
                        }else{
                            ElMessage.error('请求错误')
                        }
                        
                    })

                }else{
                    ElMessage.error(response.data.msg)
                }
            })
            .catch(error => {
                console.error('登录失败:', error.response?.data || error.message);
                // 处理错误情况
                if (error.response?.status === 401) {
                    ElMessage.error('用户名或密码错误');
                } else {
                    ElMessage.error('登录请求失败，请稍后重试');
                }
            });

        },
        Password_reset(){
            router.push('/password_reset')
        }

    }   
}
</script>
<style scoped>
.login-form {
    width: 320px;
    padding: 40px;
    border-radius: 8px;
}

.title-box {
    text-align: center;
    margin-bottom: 30px;
}

.title-box h1 {
    font-size: 24px;
    font-weight: 500;
}

.input-box {
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin-bottom: 30px;
}

.el-input {
    height: 40px;
}

.btn-box {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.btn-box button {
    height: 40px;
    background-color: #409eff;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.btn-box button:hover {
    background-color: #3a8ee6;
}

.btn-box p {
    text-align: center;
    color: #409eff;
    font-size: 14px;
    cursor: pointer;
    margin-top: 10px;
}

.btn-box p:hover {
    text-decoration: underline;
}
</style>
