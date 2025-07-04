import { defineStore } from 'pinia';
import axios, { AxiosError } from 'axios';

const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api'
});

export const UserStore = defineStore('user', {
    state: () => ({
        isOnline: false,
        heartbeatInterval: null as ReturnType<typeof setInterval> | null,
        lastHeartbeatTime: 0,
        connectionStatus: 'disconnected' as 'connected' | 'disconnected' | 'connecting' | 'error',
        errorMessage: ''
    }),
    actions: {
        // 获取用户当前在线状态
        async fetchUserStatus() {
            try {
                const token = localStorage.getItem('access_token') || '';
                if (!token) throw new Error('No authentication token found');
                const formData = new FormData();
                formData.append('token', token);
                const response = await Axios.post('/user_online_state', formData);
                return response.data.current;
            } catch (error) {
                this.handleHeartbeatError(error);
                throw error;
            }
        },
        
        // 设置用户为在线状态
        async setUserOnline() {
            try {
                const token = localStorage.getItem('access_token') || '';
                if (!token) throw new Error('No authentication token found');
                
                const formData = new FormData();
                formData.append('token', token);
                
                const response = await Axios.post('/online_user', formData);
                return response.data.current;
            } catch (error) {
                this.handleHeartbeatError(error);
                throw error;
            }
        },
        
        // 发送心跳请求
        async sendHeartbeat() {
            try {
                const token = localStorage.getItem('access_token') || '';
                if (!token) throw new Error('No authentication token found');
                
                const formData = new FormData();
                formData.append('token', token);
                
                const response = await Axios.patch('/online_heartbeat', formData);
                this.lastHeartbeatTime = Date.now();
                this.connectionStatus = 'connected';
                this.isOnline = true;
                return response;
            } catch (error) {
                this.handleHeartbeatError(error);
                throw error;
            }
        },
        
        // 处理心跳错误
        handleHeartbeatError(error: unknown) {
            this.connectionStatus = 'error';
            this.isOnline = false;
            
            if (axios.isAxiosError(error)) {
                const axiosError = error as AxiosError;
                this.errorMessage = `Heartbeat failed: ${axiosError.message}`;
                console.error('Heartbeat error:', axiosError.response?.data || axiosError.message);
            } else {
                this.errorMessage = `Heartbeat failed: ${(error as Error).message}`;
                console.error('Heartbeat error:', (error as Error).message);
            }
        },
        
        // 启动心跳请求
        async startHeartbeat() {
            // 如果已经在运行，则不重复启动
            if (this.heartbeatInterval) return;
            
            this.connectionStatus = 'connecting';
            
            try {
                // 检查用户当前状态
                const isUserOnline = await this.fetchUserStatus();
                
                if (!isUserOnline) {
                    // 用户状态为离线，发起上线请求
                    const onlineResult = await this.setUserOnline();
                    
                    if (!onlineResult) {
                        throw new Error('Failed to set user onlin');
                    }
                }
                
                // 用户状态为在线，启动心跳
                this.sendHeartbeat(); // 立即发送一次心跳
                
                this.heartbeatInterval = setInterval(async () => {
                    try {
                        await this.sendHeartbeat();
                    } catch (error) {
                        // 心跳失败时不需要停止定时器，让重试机制处理
                    }
                }, 30000);
                
                this.connectionStatus = 'connected';
                this.isOnline = true;
            } catch (error) {
                this.handleHeartbeatError(error);
                // 启动失败时清理
                this.stopHeartbeat();
            }
        },
        
        // 停止心跳请求
        stopHeartbeat() {
            if (this.heartbeatInterval) {
                clearInterval(this.heartbeatInterval);
                this.heartbeatInterval = null;
            }
            
            this.connectionStatus = 'disconnected';
            this.isOnline = false;
        }
    }
});    