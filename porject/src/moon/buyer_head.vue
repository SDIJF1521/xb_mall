<template>
    <div class="header-div">
    <div>
        欢迎回来:{{ data.userName }}
    </div>
    <el-input
        style="width: 240px;"
        v-model="input"
        placeholder="搜索"
        :prefix-icon="Search"
        clearable
    />

    <div class="header-content">
        <el-avatar size="large" :src="data.img" />
        <div>
            <div style="display: flex; gap: 15px;">
                <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="notification-badge">
                    <el-dropdown trigger="click" @visible-change="handleNotificationVisible" placement="bottom-end">
                        <el-button :icon="Bell" size="small" circle class="notification-btn" />
                        <template #dropdown>
                            <el-dropdown-menu class="notification-dropdown">
                                <div class="notification-header">
                                    <div class="header-title">
                                        <el-icon class="header-icon"><Bell /></el-icon>
                                        <span class="header-text">商品通知</span>
                                        <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="header-badge" />
                                    </div>
                                    <div class="header-actions">
                                        <el-button
                                            text
                                            type="primary"
                                            size="small"
                                            @click.stop="markAllAsRead"
                                            v-if="unreadCount > 0"
                                            class="mark-all-read-btn"
                                        >
                                            全部已读
                                        </el-button>
                                        <el-button
                                            text
                                            type="danger"
                                            size="small"
                                            @click.stop="deleteAllReadNotifications"
                                            class="delete-all-read-btn"
                                        >
                                            删除已读
                                        </el-button>
                                    </div>
                                </div>
                                <el-divider class="notification-divider" />
                                <div class="notification-list" v-if="inform.length > 0">
                                    <div
                                        v-for="(item, index) in inform"
                                        :key="index"
                                        class="notification-item"
                                        :class="{ 'unread': item.read === 0 }"
                                        @click="handleNotificationClick(item)"
                                    >
                                        <div class="notification-indicator" v-if="item.read === 0"></div>
                                        <div class="notification-content">
                                            <div class="notification-title-row">
                                                <div class="notification-title">
                                                    <el-icon class="title-icon" v-if="item.pass === 1"><CircleCheck /></el-icon>
                                                    <el-icon class="title-icon error-icon" v-else-if="item.pass === 0"><CircleClose /></el-icon>
                                                    <el-icon class="title-icon info-icon" v-else><Clock /></el-icon>
                                                    {{ item.name || '商品通知' }}
                                                </div>
                                                <div class="notification-actions">
                                                    <el-tag
                                                        :type="item.pass === 1 ? 'success' : item.pass === 0 ? 'danger' : 'info'"
                                                        size="small"
                                                        class="status-tag"
                                                        effect="plain"
                                                    >
                                                        {{ item.pass === 1 ? '已通过' : item.pass === 0 ? '已拒绝' : '审核中' }}
                                                    </el-tag>
                                                    <el-button
                                                        :icon="Delete"
                                                        size="small"
                                                        type="danger"
                                                        text
                                                        @click.stop="deleteNotification(item, index)"
                                                        class="delete-notification-btn"
                                                    />
                                                </div>
                                            </div>
                                            <div class="notification-message-wrapper">
                                                <div
                                                    class="notification-message"
                                                    :class="{ 'expanded': expandedItems[index] }"
                                                >
                                                    {{ item.msg || '您有新的商品审核通知' }}
                                                </div>
                                                <el-button
                                                    v-if="shouldShowExpandButton(item.msg)"
                                                    text
                                                    type="primary"
                                                    size="small"
                                                    class="expand-btn"
                                                    @click.stop="toggleExpand(index)"
                                                >
                                                    {{ expandedItems[index] ? '收起' : '展开' }}
                                                    <el-icon>
                                                        <ArrowDown v-if="!expandedItems[index]" />
                                                        <ArrowUp v-else />
                                                    </el-icon>
                                                </el-button>
                                            </div>
                                            <div class="notification-footer">
                                                <span class="notification-auditor" v-if="item.auditor">
                                                    <el-icon><User /></el-icon>
                                                    {{ item.auditor }}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="empty-notification">
                                    <el-empty description="暂无通知" :image-size="100">
                                        <template #image>
                                            <el-icon :size="100" class="empty-icon"><Bell /></el-icon>
                                        </template>
                                    </el-empty>
                                </div>
                            </el-dropdown-menu>
                        </template>
                    </el-dropdown>
                </el-badge>
                <el-badge :value="messageCount" :hidden="messageCount === 0" :max="99">
                    <el-button :icon="ChatDotRound" size="small" circle @click="openMessageDrawer" />
                </el-badge>

                <!-- 聊天侧边抽屉 -->
                <el-drawer
                    v-model="messageDrawerVisible"
                    title="聊天室"
                    direction="rtl"
                    size="450px"
                    :z-index="2000"
                >
                    <div class="chat-container">
                        <div class="chat-header">
                            <h3>对话</h3>
                            <el-tag type="success" size="small">在线</el-tag>
                        </div>

                        <div class="chat-messages" ref="chatMessagesRef">
                            <div
                                v-for="(msg, index) in chatMessages"
                                :key="index"
                                class="message-bubble"
                                :class="{ 'my-message': msg.sender === 'me', 'other-message': msg.sender !== 'me' }"
                            >
                                <div class="message-avatar">
                                    <el-avatar
                                        :size="30"
                                        :src="msg.sender === 'me' ? myAvatar : otherAvatar"
                                    />
                                </div>
                                <div class="message-content">
                                    <div class="message-text">{{ msg.text }}</div>
                                    <div class="message-time">{{ msg.time }}</div>
                                </div>
                            </div>
                        </div>

                        <div class="chat-input-area">
                            <el-input
                                v-model="chatInput"
                                placeholder="输入消息..."
                                @keyup.enter="sendMessage"
                                class="chat-input"
                            />
                            <el-button
                                type="primary"
                                @click="sendMessage"
                                :disabled="!chatInput.trim()"
                                class="send-button"
                            >
                                发送
                            </el-button>
                        </div>
                    </div>
                </el-drawer>
            </div>
            <el-text>昵称:{{ data.userName }}</el-text>
        </div>
    </div>
</div>
</template>
<script lang="ts" setup>
import {ref, onMounted, onUnmounted, computed, nextTick} from 'vue'
import axios from 'axios'
import {Bell, ChatDotRound, Search, CircleCheck, CircleClose, Clock, User, ArrowDown, ArrowUp, Delete} from '@element-plus/icons-vue'
import {ElMessage, ElMessageBox} from 'element-plus'

const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api'
})

const inform = ref<any[]>([])
const messageCount = ref(0)
const expandedItems = ref<Record<number, boolean>>({}) // 跟踪每个通知项的展开状态
const messageDrawerVisible = ref(false)
const chatMessages = ref<any[]>([])
const chatInput = ref('')
const chatMessagesRef = ref<HTMLElement>()
const myAvatar = ref(`data:image/png;base64,${localStorage.getItem('img')}` || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')
const otherAvatar = ref('https://cube.elemecdn.com/3/73/750154eb595ab21efae0d53a836c7.png') // 默认头像
const MAX_PREVIEW_LENGTH = 150 // 预览最大字符数

defineOptions({
    name: "BuyerHead"
})
const input = ref('')
const value = ref('')
const user = localStorage.getItem('buyer_user')
const data = ref({'img':`data:image/png;base64,${localStorage.getItem('img')}`||'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png','userName':user||'小白'})

// 计算未读通知数量
const unreadCount = computed(() => {
    return inform.value.filter(item => item.read === 0).length
})

// 获取商品通知
async function getCommodityInform() {
    try {
        const token = localStorage.getItem('buyer_access_token')
        if (!token) {
            console.warn('未找到访问令牌')
            return
        }
        const res = await Axios.get('/buyer_commodity_inform', {
            headers: {
                'access-token': token
            }
        })
        if (res.status == 200) {
            if (res.data.current && res.data.flag) {
                inform.value = res.data.data || []
            } else {
                inform.value = []
            }
        }
    } catch (error) {
        console.error('获取通知失败:', error)
        ElMessage.error('获取通知失败')
    }
}

// 处理通知下拉菜单显示/隐藏
function handleNotificationVisible(visible: boolean) {
    if (visible) {
        getCommodityInform()
    }
}

// 标记单个通知为已读
async function markNotificationAsRead(mall_id: number, shopping_id: number,_id:string) {
    try {
        const token = localStorage.getItem('buyer_access_token')
        if (!token) {
            console.warn('未找到访问令牌')
            return false
        }
        const formData = new FormData()
        formData.append('token', token)
        formData.append('info_id', _id.toString())
        formData.append('mall_id', mall_id.toString())
        formData.append('shopping_id', shopping_id.toString())
        const res = await Axios.post('/buyer_r_commodity_inform_read', formData)
        if (res.status === 200 && res.data.current) {
            return true
        } else {
            console.error('标记已读失败:', res.data.msg)
            return false
        }
    } catch (error) {
        console.error('标记已读失败:', error)
        return false
    }
}

// 处理通知点击
async function handleNotificationClick(item: any) {
    console.log('点击通知:', item)
    if (item.read === 0 && item.mall_id && item.shopping_id) {
        console.log(item);

        const success = await markNotificationAsRead(item.mall_id, item.shopping_id,item._id)
        if (success) {
            item.read = 1
            ElMessage.success('已标记为已读')
        } else {
            ElMessage.error('标记已读失败')
        }
    }
}

// 标记全部为已读
async function markAllAsRead() {
    try {
        const token = localStorage.getItem('buyer_access_token')
        if (!token) {
            ElMessage.error('未找到访问令牌')
            return
        }

        const formData = new FormData()
        formData.append('token', token)

        const res = await Axios.post('/buyer_r_commodity_inform_read', formData)
        if (res.status === 200 && res.data.current) {
            inform.value.forEach(item => {
                item.read = 1
            })
            ElMessage.success(`已标记全部为已读（共${res.data.updated_count || 0}条）`)
        } else {
            ElMessage.error(res.data.msg || '标记全部已读失败')
        }
    } catch (error) {
        console.error('标记全部已读失败:', error)
        ElMessage.error('标记全部已读失败')
    }
}

function shouldShowExpandButton(msg: string | undefined): boolean {
    if (!msg) return false
    return msg.length > MAX_PREVIEW_LENGTH
}

function toggleExpand(index: number) {
    expandedItems.value[index] = !expandedItems.value[index]
}

// 打开聊天抽屉
function openMessageDrawer() {
    messageDrawerVisible.value = true
    // 初始化聊天记录
    initChat()
}

// 初始化聊天
function initChat() {
    // 模拟初始聊天记录
    chatMessages.value = [
        {
            id: 1,
            sender: 'other',
            text: '您好，欢迎来到我们的商城！有什么可以帮助您的吗？',
            time: formatTime(new Date(Date.now() - 300000)) // 5分钟前
        },
        {
            id: 2,
            sender: 'me',
            text: '我想咨询一下最近的促销活动',
            time: formatTime(new Date(Date.now() - 240000)) // 4分钟前
        },
        {
            id: 3,
            sender: 'other',
            text: '我们最近有春季大促活动，全场商品8折起，还有满减优惠哦！',
            time: formatTime(new Date(Date.now() - 180000)) // 3分钟前
        }
    ]
    // 自动滚动到底部
    nextTick(() => {
        scrollToBottom()
    })
}

// 格式化时间
function formatTime(date: Date) {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
}

// 发送消息
function sendMessage() {
    if (!chatInput.value.trim()) return

    // 添加用户消息
    const userMessage = {
        id: Date.now(),
        sender: 'me',
        text: chatInput.value,
        time: formatTime(new Date())
    }

    chatMessages.value.push(userMessage)
    chatInput.value = ''

    // 自动滚动到底部
    nextTick(() => {
        scrollToBottom()
    })

    // 回复
    setTimeout(() => {
        const replyMessage = {
            id: Date.now() + 1,
            sender: 'other',
            text: '好的，我会尽快为您处理这个问题。',
            time: formatTime(new Date())
        }
        chatMessages.value.push(replyMessage)

        nextTick(() => {
            scrollToBottom()
        })
    }, 1000)
}

// 滚动到聊天底部
function scrollToBottom() {
    if (chatMessagesRef.value) {
        chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
}

// 删除单个通知
async function deleteNotification(item: any, index: number) {
    try {
        await ElMessageBox.confirm(
            '确定要删除这条通知吗？',
            '删除通知',
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }
        )

        const token = localStorage.getItem('buyer_access_token')
        if (!token) {
            ElMessage.error('未找到访问令牌')
            return
        }

        const formData = new FormData()
        formData.append('token', token)
        formData.append('info_id', item._id.toString())
         formData.append('token', token)
        formData.append('info_id', item._id.toString())
        formData.append('mall_id', item.mall_id.toString())
        formData.append('shopping_id', item.shopping_id.toString())


        const res = await Axios.post('/buyer_r_commodity_inform_delete', formData)
        if (res.status === 200 && res.data.current) {
            // 从本地数组中移除该通知
            inform.value.splice(index, 1)
            ElMessage.success('通知删除成功')
        } else {
            ElMessage.error(res.data.msg || '删除通知失败')
        }
    } catch (error) {
        if (error !== 'cancel') {
            console.error('删除通知失败:', error)
            ElMessage.error('删除通知失败')
        }
    }
}

// 删除所有已读通知
async function deleteAllReadNotifications() {
    try {
        await ElMessageBox.confirm(
            '确定要删除所有已读通知吗？',
            '删除通知',
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }
        )

        const token = localStorage.getItem('buyer_access_token')
        if (!token) {
            ElMessage.error('未找到访问令牌')
            return
        }

        const formData = new FormData()
        formData.append('token', token)

        const res = await Axios.post('/buyer_r_commodity_inform_delete', formData)
        if (res.status === 200 && res.data.current) {
            // 重新获取通知列表
            getCommodityInform()
            ElMessage.success(`已删除所有已读通知（共${res.data.deleted_count || 0}条）`)
        } else {
            ElMessage.error(res.data.msg || '删除已读通知失败')
        }
    } catch (error) {
        if (error !== 'cancel') {
            console.error('删除已读通知失败:', error)
            ElMessage.error('删除已读通知失败')
        }
    }
}


let intervalId: number | null = null


onMounted(() => {
    getCommodityInform()
    intervalId = setInterval(() => {
        getCommodityInform()
    }, 60000*5)
})

onUnmounted(() => {
    if (intervalId !== null) {
        clearInterval(intervalId)
        intervalId = null
    }
})

</script>
<style scoped>
    .header-content{
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 10px;
    }
    .header-div{
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }

    .notification-btn {
        transition: all 0.3s ease;
    }
    .notification-btn:hover {
        transform: scale(1.1);
        background-color: rgba(64, 158, 255, 0.1);
    }
    .notification-badge :deep(.el-badge__content) {
        background: linear-gradient(135deg, #46e2cb 0%, #742bd9 100%);
        border: 2px solid var(--el-bg-color);
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(70, 226, 203, 0.4);
    }

    /* 下拉菜单样式 */
    .notification-dropdown :deep(.el-dropdown-menu) {
        padding: 0;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        border: 1px solid var(--el-border-color);
        overflow: hidden;
        min-width: 380px;
        max-width: 420px;
        background-color: var(--el-bg-color);
    }

    /* 通知头部 */
    .notification-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        background: linear-gradient(135deg, #46e2cb 0%, #742bd9 100%);
        color: #fff;
    }
    .header-actions {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .delete-all-read-btn {
        color: #f56c6c !important;
        padding: 4px 12px;
        border-radius: 6px;
        transition: all 0.2s;
    }

    .delete-all-read-btn:hover {
        background-color: rgba(245, 108, 108, 0.1) !important;
    }
    .header-icon {
        font-size: 18px;
    }
    .header-text {
        font-weight: 600;
        font-size: 16px;
    }
    .header-badge :deep(.el-badge__content) {
        background: rgba(255, 255, 255, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.5);
        color: #fff;
        font-weight: 600;
    }
    .mark-all-read-btn {
        color: #fff !important;
        font-weight: 500;
        padding: 4px 12px;
        border-radius: 6px;
        transition: all 0.2s;
    }
    .mark-all-read-btn:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
    }

    .notification-divider {
        margin: 0;
        border-color: var(--el-border-color);
    }

    .notification-list {
        max-height: 450px;
        overflow-y: auto;
        overflow-x: hidden;
        background-color: var(--el-bg-color);
    }
    .notification-list::-webkit-scrollbar {
        width: 6px;
    }
    .notification-list::-webkit-scrollbar-track {
        background: var(--el-fill-color-lighter);
    }
    .notification-list::-webkit-scrollbar-thumb {
        background: var(--el-border-color-darker);
        border-radius: 3px;
    }
    .notification-list::-webkit-scrollbar-thumb:hover {
        background: var(--el-text-color-placeholder);
    }

    .notification-item {
        position: relative;
        padding: 16px 20px;
        cursor: pointer;
        border-bottom: 1px solid var(--el-border-color-lighter);
        transition: all 0.3s ease;
        background-color: var(--el-bg-color);
    }
    .notification-item:last-child {
        border-bottom: none;
    }
    .notification-item:hover {
        background-color: var(--el-fill-color-light);
        transform: translateX(2px);
    }
    .notification-item.unread {
        background: linear-gradient(to right, rgba(70, 226, 203, 0.15) 0%, var(--el-bg-color) 8%);
        border-left: 4px solid #46e2cb;
    }
    .notification-item.unread:hover {
        background: linear-gradient(to right, rgba(70, 226, 203, 0.25) 0%, var(--el-fill-color-light) 8%);
    }

    .notification-indicator {
        position: absolute;
        left: 8px;
        top: 50%;
        transform: translateY(-50%);
        width: 8px;
        height: 8px;
        background: #46e2cb;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(70, 226, 203, 0.8);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
            transform: translateY(-50%) scale(1);
        }
        50% {
            opacity: 0.7;
            transform: translateY(-50%) scale(1.2);
        }
    }

    .notification-content {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-left: 4px;
    }

    .notification-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
    }
    .notification-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        font-size: 15px;
        color: var(--el-text-color-primary);
        flex: 1;
        min-width: 0;
    }
    .title-icon {
        font-size: 18px;
        flex-shrink: 0;
    }
    .title-icon:not(.error-icon):not(.info-icon) {
        color: #46e2cb;
    }
    .error-icon {
        color: #f56c6c;
    }
    .info-icon {
        color: var(--el-text-color-placeholder);
    }
    .notification-actions {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .status-tag {
        flex-shrink: 0;
        font-weight: 500;
    }
    .delete-notification-btn {
        color: #f56c6c !important;
        opacity: 0.7;
        transition: all 0.2s;
    }

    .delete-notification-btn:hover {
        opacity: 1;
        transform: scale(1.1);
    }

    .notification-message-wrapper {
        padding-left: 26px;
    }

    .notification-message {
        font-size: 13px;
        color: var(--el-text-color-regular);
        line-height: 1.6;
        word-break: break-word;
        word-wrap: break-word;
        white-space: pre-wrap;
        max-height: 4.8em;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        line-clamp: 3;
        -webkit-box-orient: vertical;
        transition: max-height 0.3s ease, -webkit-line-clamp 0.3s ease;
    }
    .notification-message.expanded {
        max-height: 1000px;
        -webkit-line-clamp: unset;
        line-clamp: unset;
        display: block;
    }


    .expand-btn {
        margin-top: 6px;
        padding: 0;
        height: auto;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .expand-btn .el-icon {
        font-size: 12px;
        transition: transform 0.3s ease;
    }


    .notification-footer {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-top: 4px;
        padding-left: 26px;
    }
    .notification-auditor {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: var(--el-text-color-placeholder);
    }
    .notification-auditor .el-icon {
        font-size: 14px;
    }


    .empty-notification {
        padding: 40px 20px;
        text-align: center;
        background-color: var(--el-bg-color);
    }
    .empty-icon {
        color: var(--el-text-color-placeholder);
        opacity: 0.5;
    }


    .dark .notification-btn:hover {
        background-color: rgba(70, 226, 203, 0.15);
    }
    .dark .notification-dropdown :deep(.el-dropdown-menu) {
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        border-color: rgba(255, 255, 255, 0.1);
    }
    .dark .notification-item {
        border-bottom-color: rgba(255, 255, 255, 0.1);
    }
    .dark .notification-item:hover {
        background-color: rgba(255, 255, 255, 0.05);
    }
    .dark .notification-item.unread {
        background: linear-gradient(to right, rgba(70, 226, 203, 0.2) 0%, var(--el-bg-color) 8%);
    }
    .dark .notification-item.unread:hover {
        background: linear-gradient(to right, rgba(70, 226, 203, 0.3) 0%, rgba(255, 255, 255, 0.05) 8%);
    }

    /* 聊天界面样式 */
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    .chat-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--el-border-color);
        margin-bottom: 16px;
    }

    .chat-header h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
    }

    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 0 10px 16px;
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .chat-messages::-webkit-scrollbar {
        width: 6px;
    }
    .chat-messages::-webkit-scrollbar-track {
        background: var(--el-fill-color-lighter);
    }
    .chat-messages::-webkit-scrollbar-thumb {
        background: var(--el-border-color-darker);
        border-radius: 3px;
    }
    .chat-messages::-webkit-scrollbar-thumb:hover {
        background: var(--el-text-color-placeholder);
    }

    .message-bubble {
        display: flex;
        gap: 10px;
        align-items: flex-start;
    }

    .message-bubble.my-message {
        flex-direction: row-reverse;
        margin-left: auto;
    }

    .message-avatar {
        flex-shrink: 0;
    }

    .message-content {
        display: flex;
        flex-direction: column;
        max-width: 70%;
    }

    .message-bubble.my-message .message-content {
        align-items: flex-end;
    }

    .message-text {
        padding: 10px 14px;
        border-radius: 18px;
        font-size: 14px;
        line-height: 1.5;
        word-wrap: break-word;
        white-space: pre-wrap;
    }

    .message-bubble.my-message .message-text {
        background-color: #409eff;
        color: white;
        border-bottom-right-radius: 4px;
    }

    .message-bubble.other-message .message-text {
        background-color: var(--el-bg-color-overlay);
        border: 1px solid var(--el-border-color);
        border-bottom-left-radius: 4px;
    }

    .message-time {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin-top: 4px;
        text-align: right;
    }

    .chat-input-area {
        display: flex;
        gap: 8px;
        padding-top: 16px;
        border-top: 1px solid var(--el-border-color);
    }

    .chat-input {
        flex: 1;
    }

    .send-button {
        flex-shrink: 0;
    }
</style>
