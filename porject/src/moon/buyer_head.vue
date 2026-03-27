<template>
    <div class="header-div">
    <div>
        欢迎回来:{{ data.userName }}
    </div>

    <!-- 快捷导航搜索框 -->
    <el-autocomplete
        v-model="input"
        style="width: 260px;"
        placeholder="搜索功能页面..."
        :prefix-icon="Search"
        clearable
        :fetch-suggestions="querySearch"
        :trigger-on-focus="true"
        popper-class="nav-search-popper"
        @select="handleNavSelect"
        @keydown.enter.prevent="handleEnterNav"
    >
        <template #default="{ item }">
            <div class="nav-item">
                <el-icon class="nav-icon" :class="`nav-icon--${item.color}`">
                    <component :is="item.icon" />
                </el-icon>
                <div class="nav-text">
                    <span class="nav-label" v-html="item.highlight || item.label" />
                    <span class="nav-desc">{{ item.desc }}</span>
                </div>
                <el-tag :type="item.tagType" size="small" effect="plain" class="nav-tag">
                    {{ item.tag }}
                </el-tag>
            </div>
        </template>
    </el-autocomplete>

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

                <!-- 聊天按钮 -->
                <el-badge :value="messageCount" :hidden="messageCount === 0" :max="99">
                    <el-button :icon="ChatDotRound" size="small" circle @click="openMessageDrawer" />
                </el-badge>

                <!-- 员工聊天抽屉 -->
                <el-drawer
                    v-model="messageDrawerVisible"
                    title="员工聊天室"
                    direction="rtl"
                    size="460px"
                    :z-index="2000"
                    @open="onDrawerOpen"
                    @close="onDrawerClose"
                >
                    <div class="chat-container">
                        <!-- 主商户：店铺选择 -->
                        <div v-if="userStation === '1'" class="store-selector">
                            <el-select
                                v-model="selectedMallId"
                                placeholder="选择要加入的店铺聊天室"
                                style="width: 100%"
                                :loading="mallListLoading"
                                @change="connectToStore"
                            >
                                <el-option
                                    v-for="m in mallList"
                                    :key="m.id"
                                    :label="m.name"
                                    :value="m.id"
                                />
                            </el-select>
                        </div>

                        <!-- 连接状态栏 -->
                        <div class="ws-status-bar" :class="`ws-status-bar--${wsState}`">
                            <template v-if="wsState === 'open'">
                                <span class="status-dot status-dot--green" />
                                <span>已连接</span>
                                <span class="online-info">
                                    <el-icon><User /></el-icon>
                                    在线：{{ onlineUsers.join('、') || '仅你' }}
                                </span>
                            </template>
                            <template v-else-if="wsState === 'connecting'">
                                <el-icon class="is-loading"><Loading /></el-icon>
                                <span>连接中...</span>
                            </template>
                            <template v-else-if="wsState === 'idle'">
                                <span class="status-dot status-dot--gray" />
                                <span>{{ userStation === '1' ? '请选择店铺' : '等待连接' }}</span>
                            </template>
                            <template v-else>
                                <span class="status-dot status-dot--red" />
                                <span>已断开</span>
                                <el-button size="small" type="primary" text @click="reconnectWs">重连</el-button>
                            </template>
                        </div>

                        <!-- 消息列表 -->
                        <div class="chat-messages" ref="chatMessagesRef">
                            <template v-for="(msg, index) in chatMessages" :key="index">
                                <!-- 系统通知 -->
                                <div v-if="msg.type === 'system'" class="sys-message">
                                    <el-icon><InfoFilled /></el-icon>
                                    <span>{{ msg.content }}</span>
                                    <span class="sys-time">{{ formatMsgTime(msg.created_at) }}</span>
                                </div>

                                <!-- 他人消息 -->
                                <div
                                    v-else-if="msg.username !== currentUser"
                                    class="message-bubble other-message"
                                >
                                    <div class="message-avatar">
                                        <el-avatar :size="30" class="avatar-other">
                                            {{ (msg.username || '?').slice(0, 1).toUpperCase() }}
                                        </el-avatar>
                                    </div>
                                    <div class="message-content">
                                        <div class="message-sender">{{ msg.username }}</div>
                                        <div class="message-text other-text">{{ msg.content }}</div>
                                        <div class="message-time">{{ formatMsgTime(msg.created_at) }}</div>
                                    </div>
                                </div>

                                <!-- 自己消息 -->
                                <div v-else class="message-bubble my-message">
                                    <div class="message-content">
                                        <div class="message-text my-text">{{ msg.content }}</div>
                                        <div class="message-time" style="text-align:right">{{ formatMsgTime(msg.created_at) }}</div>
                                    </div>
                                    <div class="message-avatar">
                                        <el-avatar :size="30" class="avatar-self">
                                            {{ (msg.username || '?').slice(0, 1).toUpperCase() }}
                                        </el-avatar>
                                    </div>
                                </div>
                            </template>

                            <!-- 空状态 -->
                            <div v-if="chatMessages.length === 0 && wsState === 'open'" class="empty-chat">
                                <el-icon :size="36"><ChatRound /></el-icon>
                                <p>暂无消息，快来打个招呼吧！</p>
                            </div>
                        </div>

                        <!-- 输入区域 -->
                        <div class="chat-input-area">
                            <el-input
                                v-model="chatInput"
                                placeholder="输入消息，Enter 发送…"
                                @keydown.enter.exact.prevent="sendMessage"
                                :disabled="wsState !== 'open'"
                                class="chat-input"
                            />
                            <el-button
                                type="primary"
                                @click="sendMessage"
                                :disabled="!chatInput.trim() || wsState !== 'open'"
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
import { useRouter } from 'vue-router'
import axios from 'axios'
import {
    Bell, ChatDotRound, Search,
    CircleCheck, CircleClose, Clock, User,
    ArrowDown, ArrowUp, Delete,
    InfoFilled, Loading, ChatRound,
    House, Shop, Plus, UserFilled, Avatar,
    DataLine, Goods, List, Menu, Box, Setting,
    Document, SwitchButton, Headset, Service, Promotion,
} from '@element-plus/icons-vue'
import {ElMessage, ElMessageBox} from 'element-plus'

const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api'
})
const router = useRouter()

// ── 快捷导航搜索 ───────────────────────────────────────────────────────────

interface NavItem {
    value: string        // el-autocomplete 必须字段（显示在输入框中）
    label: string        // 页面名称
    desc: string         // 简短描述
    keywords: string[]   // 关键词列表，用于模糊匹配
    icon: any            // Element Plus 图标组件
    color: string        // 图标颜色 class
    tag: string          // 右侧标签文字
    tagType: string      // 标签类型
    to?: string          // 固定路由（无需 id）
    toFn?: (id: number) => string  // 需要 mall_id 的动态路由
    action?: string      // 特殊动作（如 openChat）
    highlight?: string   // 搜索关键词高亮（运行时填充）
}

const ALL_NAV_ITEMS: NavItem[] = [
    {
        value: '首页', label: '首页', desc: '买家端控制台首页',
        keywords: ['首页', '控制台', '主页', 'home', 'index', '仪表盘'],
        icon: House, color: 'blue', tag: '常用', tagType: 'primary',
        to: '/buyer_index',
    },
    {
        value: '店铺列表', label: '店铺列表', desc: '查看与管理你的所有店铺',
        keywords: ['店铺', '管理', '商店', 'store', '我的店铺'],
        icon: Shop, color: 'purple', tag: '店铺', tagType: 'warning',
        to: '/buyer_store_manage',
    },
    {
        value: '创建店铺', label: '创建店铺', desc: '新建一个店铺',
        keywords: ['创建', '新建', '添加', '开店', 'add', 'create', '开店'],
        icon: Plus, color: 'green', tag: '店铺', tagType: 'warning',
        to: '/buyer_add_mall',
    },
    {
        value: '删除店铺', label: '删除店铺', desc: '永久删除已有店铺',
        keywords: ['删除', '移除', '关闭', 'delete', '注销'],
        icon: Delete, color: 'red', tag: '店铺', tagType: 'warning',
        to: '/buyer_delete_mall',
    },
    {
        value: '用户管理', label: '用户管理', desc: '管理店铺员工账号',
        keywords: ['用户', '员工', '人员', '成员', 'user', '账号'],
        icon: User, color: 'blue', tag: '员工', tagType: 'info',
        to: '/buyer_user_manage',
    },
    {
        value: '用户列表', label: '用户列表', desc: '查看店铺全部用户',
        keywords: ['用户列表', '员工列表', '人员列表', '成员列表'],
        icon: UserFilled, color: 'blue', tag: '员工', tagType: 'info',
        toFn: (id) => `/buyer_user_list_id/${id}`,
    },
    {
        value: '角色管理', label: '角色管理', desc: '配置用户角色与操作权限',
        keywords: ['角色', '权限', '职位', 'role', '授权', '分配'],
        icon: Avatar, color: 'orange', tag: '权限', tagType: 'danger',
        toFn: (id) => `/buyer_role_list/${id}`,
    },
    {
        value: '用户统计', label: '用户统计', desc: '查看员工数据统计图表',
        keywords: ['统计', '数据', '分析', 'statistics', '报表', '图表'],
        icon: DataLine, color: 'cyan', tag: '统计', tagType: 'info',
        toFn: (id) => `/buyer_user_statistics/${id}`,
    },
    {
        value: '商品管理', label: '商品管理', desc: '上架、下架、编辑商品',
        keywords: ['商品', '货物', '产品', 'commodity', '上架', '下架', '商品管理'],
        icon: Goods, color: 'green', tag: '商品', tagType: 'success',
        to: '/buyer_commodity_management',
    },
    {
        value: '商品列表', label: '商品列表', desc: '浏览店铺全部商品',
        keywords: ['商品列表', '货品', '商品目录', '产品列表'],
        icon: List, color: 'green', tag: '商品', tagType: 'success',
        toFn: (id) => `/buyer_commodity_list/${id}`,
    },
    {
        value: '商品分类', label: '商品分类', desc: '管理商品分类目录',
        keywords: ['分类', '类别', '类目', 'classify', 'category', '目录'],
        icon: Menu, color: 'orange', tag: '商品', tagType: 'success',
        toFn: (id) => `/buyer_commodity_classify/${id}`,
    },
    {
        value: '库存管理', label: '库存管理', desc: '查看和调整商品库存数量',
        keywords: ['库存', '存货', '库存管理', 'inventory', 'repertory', '仓库'],
        icon: Box, color: 'purple', tag: '商品', tagType: 'success',
        toFn: (id) => `/buyer_commodity_repertory/${id}`,
    },
    {
        value: '店铺信息', label: '店铺信息', desc: '编辑店铺名称、地址、简介等',
        keywords: ['店铺信息', '编辑店铺', '修改店铺', '店铺设置', '基本信息'],
        icon: Setting, color: 'gray', tag: '店铺', tagType: 'warning',
        toFn: (id) => `/buyer_store_manage_index/${id}`,
    },
    {
        value: '员工聊天', label: '员工聊天', desc: '打开与店铺员工的聊天室',
        keywords: ['聊天', '通讯', '沟通', '消息', 'chat', '内部沟通'],
        icon: ChatDotRound, color: 'cyan', tag: '聊天', tagType: 'info',
        action: 'openChat',
    },
    {
        value: '商品通知', label: '商品通知', desc: '查看商品审核通知',
        keywords: ['通知', '消息', '审核', '通告', 'notify', '提醒'],
        icon: Bell, color: 'orange', tag: '通知', tagType: 'warning',
        action: 'openNotify',
    },
    {
        value: '客服管理', label: '客服管理', desc: '选择店铺进入客服管理中心',
        keywords: ['客服', '在线客服', '客服管理', 'service', '售后', '接待', '咨询'],
        icon: Headset, color: 'cyan', tag: '客服', tagType: 'info',
        to: '/buyer_cs_select',
    },
    {
        value: '客服中心', label: '客服中心', desc: '进入指定店铺的客服工作台',
        keywords: ['客服中心', '工作台', '接单', '客服会话', 'customer service'],
        icon: Service, color: 'blue', tag: '客服', tagType: 'info',
        toFn: (id) => `/buyer_customer_service/${id}`,
    },
    {
        value: '广告投放', label: '广告投放', desc: '申请轮播图广告位推广商品',
        keywords: ['广告', '投放', '推广', '轮播', '横幅', 'ad', 'banner', '曝光'],
        icon: Promotion, color: 'orange', tag: '营销', tagType: 'warning',
        toFn: (id) => `/buyer_ad_apply/${id}`,
    },
]

/** 解析当前用户的 mall_id（station='2' 直接返回；station='1' 取第一个） */
function resolveCurrentMallId(): number | null {
    if (userMallIdFromToken.value !== null) return userMallIdFromToken.value
    if (mallList.value.length > 0) return mallList.value[0].id
    // 尝试从 token 的 state_id_list 取第一个
    const raw = localStorage.getItem('buyer_access_token') || ''
    const payload = parseJwtPayload(raw)
    const list: number[] = payload?.state_id_list ?? []
    return list[0] ?? null
}

/** 关键词高亮（将匹配部分包裹 <em>） */
function highlight(text: string, kw: string): string {
    if (!kw) return text
    const escaped = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    return text.replace(new RegExp(escaped, 'gi'), m => `<em>${m}</em>`)
}

/** el-autocomplete 的数据源函数 */
function querySearch(queryStr: string, cb: (results: NavItem[]) => void) {
    const q = queryStr.trim().toLowerCase()
    const results = ALL_NAV_ITEMS
        .filter(item =>
            !q ||
            item.label.toLowerCase().includes(q) ||
            item.desc.toLowerCase().includes(q) ||
            item.keywords.some(k => k.toLowerCase().includes(q))
        )
        .map(item => ({
            ...item,
            highlight: q ? highlight(item.label, q) : item.label,
        }))
    cb(results)
}

/** 点击或回车选中条目时执行跳转 */
function handleNavSelect(item: NavItem) {
    input.value = ''
    execNav(item)
}

/** 回车时取第一条结果直接跳转 */
function handleEnterNav() {
    if (!input.value.trim()) return
    const q = input.value.trim().toLowerCase()
    const first = ALL_NAV_ITEMS.find(item =>
        item.label.toLowerCase().includes(q) ||
        item.keywords.some(k => k.toLowerCase().includes(q))
    )
    if (first) {
        input.value = ''
        execNav(first)
    }
}

function execNav(item: NavItem) {
    // 特殊动作
    if (item.action === 'openChat') {
        openMessageDrawer()
        return
    }
    if (item.action === 'openNotify') {
        ElMessage.info('请点击右上角铃铛图标查看通知')
        return
    }

    // 固定路由
    if (item.to) {
        router.push(item.to)
        return
    }

    // 需要 mall_id 的动态路由
    if (item.toFn) {
        const mallId = resolveCurrentMallId()
        if (mallId === null) {
            ElMessage.warning('请先选择或创建一个店铺')
            router.push('/buyer_store_manage')
            return
        }
        router.push(item.toFn(mallId))
    }
}

// ── 通知相关 ──────────────────────────────────────────────────────────────

const inform = ref<any[]>([])
const expandedItems = ref<Record<number, boolean>>({})
const MAX_PREVIEW_LENGTH = 150

defineOptions({ name: "BuyerHead" })

const input = ref('')
const user = localStorage.getItem('buyer_user')
const data = ref({
    img: `data:image/png;base64,${localStorage.getItem('img')}` || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
    userName: user || '小白'
})

const unreadCount = computed(() => inform.value.filter(item => item.read === 0).length)

async function getCommodityInform() {
    try {
        const token = localStorage.getItem('buyer_access_token')
        if (!token) return
        const res = await Axios.get('/buyer_commodity_inform', { headers: { 'access-token': token } })
        if (res.status == 200) {
            inform.value = res.data.current && res.data.flag ? (res.data.data || []) : []
        }
    } catch {
        ElMessage.error('获取通知失败')
    }
}

function handleNotificationVisible(visible: boolean) {
    if (visible) getCommodityInform()
}

async function markNotificationAsRead(mall_id: number, shopping_id: number, _id: string) {
    try {
        const token = localStorage.getItem('buyer_access_token')
        if (!token) return false
        const formData = new FormData()
        formData.append('token', token)
        formData.append('info_id', _id.toString())
        formData.append('mall_id', mall_id.toString())
        formData.append('shopping_id', shopping_id.toString())
        const res = await Axios.post('/buyer_r_commodity_inform_read', formData)
        return res.status === 200 && res.data.current
    } catch {
        return false
    }
}

async function handleNotificationClick(item: any) {
    if (item.read === 0 && item.mall_id && item.shopping_id) {
        const success = await markNotificationAsRead(item.mall_id, item.shopping_id, item._id)
        if (success) {
            item.read = 1
            ElMessage.success('已标记为已读')
        } else {
            ElMessage.error('标记已读失败')
        }
    }
}

async function markAllAsRead() {
    try {
        const token = localStorage.getItem('buyer_access_token')
        if (!token) { ElMessage.error('未找到访问令牌'); return }
        const formData = new FormData()
        formData.append('token', token)
        const res = await Axios.post('/buyer_r_commodity_inform_read', formData)
        if (res.status === 200 && res.data.current) {
            inform.value.forEach(item => { item.read = 1 })
            ElMessage.success(`已标记全部为已读（共${res.data.updated_count || 0}条）`)
        } else {
            ElMessage.error(res.data.msg || '标记全部已读失败')
        }
    } catch {
        ElMessage.error('标记全部已读失败')
    }
}

function shouldShowExpandButton(msg: string | undefined): boolean {
    return !!msg && msg.length > MAX_PREVIEW_LENGTH
}

function toggleExpand(index: number) {
    expandedItems.value[index] = !expandedItems.value[index]
}

async function deleteNotification(item: any, index: number) {
    try {
        await ElMessageBox.confirm('确定要删除这条通知吗？', '删除通知', {
            confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
        })
        const token = localStorage.getItem('buyer_access_token')
        if (!token) { ElMessage.error('未找到访问令牌'); return }
        const formData = new FormData()
        formData.append('token', token)
        formData.append('info_id', item._id.toString())
        formData.append('mall_id', item.mall_id.toString())
        formData.append('shopping_id', item.shopping_id.toString())
        const res = await Axios.post('/buyer_r_commodity_inform_delete', formData)
        if (res.status === 200 && res.data.current) {
            inform.value.splice(index, 1)
            ElMessage.success('通知删除成功')
        } else {
            ElMessage.error(res.data.msg || '删除通知失败')
        }
    } catch (error) {
        if (error !== 'cancel') ElMessage.error('删除通知失败')
    }
}

async function deleteAllReadNotifications() {
    try {
        await ElMessageBox.confirm('确定要删除所有已读通知吗？', '删除通知', {
            confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
        })
        const token = localStorage.getItem('buyer_access_token')
        if (!token) { ElMessage.error('未找到访问令牌'); return }
        const formData = new FormData()
        formData.append('token', token)
        const res = await Axios.post('/buyer_r_commodity_inform_delete', formData)
        if (res.status === 200 && res.data.current) {
            getCommodityInform()
            ElMessage.success(`已删除所有已读通知（共${res.data.deleted_count || 0}条）`)
        } else {
            ElMessage.error(res.data.msg || '删除已读通知失败')
        }
    } catch (error) {
        if (error !== 'cancel') ElMessage.error('删除已读通知失败')
    }
}

// ── WebSocket 员工聊天 ─────────────────────────────────────────────────────

interface ChatMsg {
    type: 'chat' | 'system'
    username?: string
    content: string
    created_at: string
}

const messageCount = ref(0)
const messageDrawerVisible = ref(false)
const chatMessages = ref<ChatMsg[]>([])
const chatInput = ref('')
const chatMessagesRef = ref<HTMLElement>()
const onlineUsers = ref<string[]>([])
const currentUser = ref('')

type WsState = 'idle' | 'connecting' | 'open' | 'closed'
const wsState = ref<WsState>('idle')

// 登录身份
const userStation = ref<'1' | '2' | ''>('')
const mallList = ref<{ id: number; name: string }[]>([])
const mallListLoading = ref(false)
const selectedMallId = ref<number | null>(null)
const userMallIdFromToken = ref<number | null>(null)   // station='2' 使用

let ws: WebSocket | null = null
let autoReconnect = true
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let activeMallId: number | null = null

/** 解析 JWT payload（仅用于读取 claims，无需验签） */
function parseJwtPayload(raw: string): Record<string, any> | null {
    try {
        const jwt = raw.trim().split(' ').pop()!
        const b64 = jwt.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
        return JSON.parse(atob(b64))
    } catch {
        return null
    }
}

function initTokenInfo() {
    const raw = localStorage.getItem('buyer_access_token') || ''
    const payload = parseJwtPayload(raw)
    if (!payload) return
    userStation.value = payload.station ?? ''
    if (payload.station === '2') {
        userMallIdFromToken.value = payload.mall_id ?? null
    }
    currentUser.value = payload.user ?? ''
}

/** 加载主商户的店铺列表（station='1'） */
async function loadMallList() {
    mallListLoading.value = true
    try {
        const token = localStorage.getItem('buyer_access_token') || ''
        const form = new FormData()
        form.append('token', token)
        const res = await Axios.post('/buyer_get_mall_info', form)
        if (res.status === 200 && res.data.current && res.data.data) {
            mallList.value = res.data.data.map((s: any) => ({ id: s.id, name: s.mall_name || `店铺 ${s.id}` }))
        }
    } catch {
        // ignore
    } finally {
        mallListLoading.value = false
    }
}

function connectWs(mallId: number) {
    if (ws) { ws.onclose = null; ws.close(); ws = null }
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }

    activeMallId = mallId
    wsState.value = 'connecting'
    autoReconnect = true

    const raw = localStorage.getItem('buyer_access_token') || ''
    const encoded = encodeURIComponent(raw)
    ws = new WebSocket(`ws://127.0.0.1:8000/api/ws/store_chat/${mallId}?token=${encoded}`)

    ws.onopen = () => {
        wsState.value = 'open'
    }

    ws.onmessage = (event) => {
        try { handleServerMsg(JSON.parse(event.data)) } catch { /* ignore */ }
    }

    ws.onerror = () => {
        wsState.value = 'closed'
    }

    ws.onclose = (e) => {
        wsState.value = 'closed'
        if (e.code === 4001) {
            ElMessage.error('Token 无效或已过期，请重新登录')
            autoReconnect = false
        } else if (e.code === 4003) {
            ElMessage.error('无权限访问该店铺聊天室')
            autoReconnect = false
        } else if (autoReconnect && activeMallId !== null) {
            reconnectTimer = setTimeout(() => connectWs(activeMallId!), 3000)
        }
    }
}

function handleServerMsg(data: any) {
    if (data.type === 'history') {
        chatMessages.value = data.data || []
        scrollToBottom()
        return
    }
    if (data.type === 'system') {
        if (Array.isArray(data.online_users)) onlineUsers.value = data.online_users
        chatMessages.value.push({ type: 'system', content: data.content, created_at: data.created_at })
        scrollToBottom()
        return
    }
    if (data.type === 'chat') {
        chatMessages.value.push({
            type: 'chat',
            username: data.username,
            content: data.content,
            created_at: data.created_at,
        })
        // 未打开抽屉时增加未读数
        if (!messageDrawerVisible.value) messageCount.value++
        scrollToBottom()
    }
}

function sendMessage() {
    const content = chatInput.value.trim()
    if (!content || wsState.value !== 'open') return
    if (content.length > 500) { ElMessage.warning('消息不能超过 500 个字符'); return }
    ws?.send(JSON.stringify({ type: 'chat', content }))
    chatInput.value = ''
}

function disconnectWs() {
    autoReconnect = false
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
    if (ws) { ws.onclose = null; ws.close(); ws = null }
    wsState.value = 'idle'
    activeMallId = null
}

function reconnectWs() {
    if (activeMallId !== null) {
        autoReconnect = true
        connectWs(activeMallId)
    }
}

function scrollToBottom() {
    nextTick(() => {
        if (chatMessagesRef.value) {
            chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
        }
    })
}

function formatMsgTime(ts: string): string {
    if (!ts) return ''
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ''
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function openMessageDrawer() {
    messageDrawerVisible.value = true
    messageCount.value = 0
}

function onDrawerOpen() {
    messageCount.value = 0
    if (userStation.value === '2' && userMallIdFromToken.value !== null && wsState.value === 'idle') {
        connectWs(userMallIdFromToken.value)
    } else if (userStation.value === '1' && mallList.value.length === 0) {
        loadMallList()
    }
}

function onDrawerClose() {
    // 保持 WS 连接以便后台收到消息后更新 messageCount
}

/** 主商户在下拉框选择店铺后触发 */
function connectToStore(mallId: number) {
    chatMessages.value = []
    onlineUsers.value = []
    connectWs(mallId)
}

// ── 生命周期 ──────────────────────────────────────────────────────────────

let intervalId: number | null = null

onMounted(() => {
    initTokenInfo()
    getCommodityInform()
    // station='2' 员工：静默后台连接，以便接收消息计数
    if (userStation.value === '2' && userMallIdFromToken.value !== null) {
        connectWs(userMallIdFromToken.value)
    }
    intervalId = setInterval(() => { getCommodityInform() }, 60000 * 5)
})

onUnmounted(() => {
    if (intervalId !== null) { clearInterval(intervalId); intervalId = null }
    disconnectWs()
})
</script>
<style scoped>
    /* ── 快捷导航搜索 ─────────────────────────────── */
    :global(.nav-search-popper) {
        min-width: 320px !important;
        max-width: 360px !important;
        border-radius: 12px !important;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18) !important;
    }
    :global(.nav-search-popper .el-autocomplete-suggestion__list) {
        padding: 4px 0;
    }
    :global(.nav-search-popper .el-autocomplete-suggestion__wrap) {
        max-height: 380px;
    }

    .nav-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 2px;
    }
    .nav-icon {
        font-size: 18px;
        flex-shrink: 0;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .nav-icon--blue   { background: rgba(64,158,255,.12);  color: #409eff; }
    .nav-icon--purple { background: rgba(118,75,162,.12);  color: #764ba2; }
    .nav-icon--green  { background: rgba(103,194,58,.12);  color: #67c23a; }
    .nav-icon--red    { background: rgba(245,108,108,.12); color: #f56c6c; }
    .nav-icon--orange { background: rgba(230,162,60,.12);  color: #e6a23c; }
    .nav-icon--cyan   { background: rgba(0,194,255,.12);   color: #00c2ff; }
    .nav-icon--gray   { background: rgba(144,147,153,.12); color: #909399; }

    .nav-text {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .nav-label {
        font-size: 13px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    :global(.nav-label em) {
        color: #409eff;
        font-style: normal;
        font-weight: 600;
    }
    .nav-desc {
        font-size: 11px;
        color: var(--el-text-color-placeholder);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .nav-tag {
        flex-shrink: 0;
        font-size: 10px;
    }

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
        0%, 100% { opacity: 1; transform: translateY(-50%) scale(1); }
        50%       { opacity: 0.7; transform: translateY(-50%) scale(1.2); }
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
    .title-icon:not(.error-icon):not(.info-icon) { color: #46e2cb; }
    .error-icon { color: #f56c6c; }
    .info-icon  { color: var(--el-text-color-placeholder); }
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
    .notification-auditor .el-icon { font-size: 14px; }

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
    .dark .notification-item { border-bottom-color: rgba(255, 255, 255, 0.1); }
    .dark .notification-item:hover { background-color: rgba(255, 255, 255, 0.05); }
    .dark .notification-item.unread {
        background: linear-gradient(to right, rgba(70, 226, 203, 0.2) 0%, var(--el-bg-color) 8%);
    }
    .dark .notification-item.unread:hover {
        background: linear-gradient(to right, rgba(70, 226, 203, 0.3) 0%, rgba(255, 255, 255, 0.05) 8%);
    }

    /* ── 聊天抽屉内部 ─────────────────────────────── */
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 100%;
        gap: 10px;
    }

    /* 店铺选择器 */
    .store-selector {
        flex-shrink: 0;
    }

    /* 连接状态栏 */
    .ws-status-bar {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        padding: 6px 10px;
        border-radius: 8px;
        flex-shrink: 0;
        color: var(--el-text-color-secondary);
        background: var(--el-fill-color-lighter);
    }
    .ws-status-bar--open   { background: rgba(103, 194, 58, 0.1); color: #67c23a; }
    .ws-status-bar--closed { background: rgba(245, 108, 108, 0.1); color: #f56c6c; }
    .ws-status-bar--connecting { color: #e6a23c; background: rgba(230, 162, 60, 0.1); }

    .status-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .status-dot--green { background: #67c23a; }
    .status-dot--red   { background: #f56c6c; }
    .status-dot--gray  { background: var(--el-border-color-darker); }

    .online-info {
        margin-left: auto;
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 11px;
        opacity: 0.8;
    }

    /* 消息列表 */
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 4px 4px 8px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        min-height: 0;
    }
    .chat-messages::-webkit-scrollbar { width: 6px; }
    .chat-messages::-webkit-scrollbar-track { background: var(--el-fill-color-lighter); }
    .chat-messages::-webkit-scrollbar-thumb { background: var(--el-border-color-darker); border-radius: 3px; }

    /* 系统消息 */
    .sys-message {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        font-size: 12px;
        color: var(--el-text-color-placeholder);
        background: var(--el-fill-color-light);
        padding: 3px 12px;
        border-radius: 20px;
        align-self: center;
    }
    .sys-time {
        margin-left: 4px;
        font-size: 11px;
        opacity: 0.7;
    }

    /* 气泡行 */
    .message-bubble {
        display: flex;
        align-items: flex-end;
        gap: 8px;
    }
    .message-bubble.my-message { flex-direction: row-reverse; }

    .message-avatar { flex-shrink: 0; }
    .avatar-other {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #fff;
        font-weight: 600;
    }
    .avatar-self {
        background: linear-gradient(135deg, #43e97b, #38f9d7);
        color: #fff;
        font-weight: 600;
    }

    .message-content {
        display: flex;
        flex-direction: column;
        max-width: 72%;
    }
    .my-message .message-content { align-items: flex-end; }

    .message-sender {
        font-size: 11px;
        color: var(--el-text-color-placeholder);
        margin-bottom: 3px;
        padding-left: 4px;
    }

    .message-text {
        padding: 9px 13px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.55;
        word-break: break-word;
        white-space: pre-wrap;
    }
    .other-text {
        background-color: var(--el-bg-color-overlay);
        border: 1px solid var(--el-border-color);
        border-bottom-left-radius: 4px;
        color: var(--el-text-color-primary);
    }
    .my-text {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #fff;
        border-bottom-right-radius: 4px;
    }

    .message-time {
        font-size: 11px;
        color: var(--el-text-color-secondary);
        margin-top: 3px;
        padding: 0 4px;
    }

    /* 空状态 */
    .empty-chat {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        padding: 40px 0;
        color: var(--el-text-color-placeholder);
        font-size: 13px;
        margin: auto;
    }
    .empty-chat .el-icon { opacity: 0.35; }
    .empty-chat p { margin: 0; }

    /* 输入区域 */
    .chat-input-area {
        display: flex;
        gap: 8px;
        padding-top: 8px;
        border-top: 1px solid var(--el-border-color);
        flex-shrink: 0;
    }
    .chat-input { flex: 1; }
    .send-button { flex-shrink: 0; }
</style>
