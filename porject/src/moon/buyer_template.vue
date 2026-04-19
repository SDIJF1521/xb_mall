<template>
  <el-container>
    <el-header>
      <div class="header-wrapper">
        <h3 class="title">{{title}}</h3>
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
          @select="handleNavSelect as any"
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
        <el-col :span="4">
          <el-button type="primary" size="small" @click="to_index">返回到首页</el-button>
        </el-col>
      </div>
    </el-header>
    <el-main>
      <div v-for="(component, index) in currentComponents" :key="index" class="component-container">
        <component :is='component'></component>
      </div>
    </el-main>
    <el-footer class="footer-content">版权所有 ©[xb商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script setup lang="ts">
import {ref, onMounted} from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
    Search,
    House, Shop, Plus, Delete, User, UserFilled, Avatar,
    DataLine, Goods, List, Menu, Box, Setting,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BuyerTheme from '@/moon/buyer_theme';
import axios from 'axios'

const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api'
})
import RoleRatio from '@/views/buyer_user_statistics/content/role_ratio.vue'
import UserListMain from '@/views/buyer_user_list_id/content/user_list_main.vue'
import RoleListMain from '@/views/buyer_role_list/content/role_list_main.vue'
import CommodityAdd from '@/views/buyer_commodity_add/content/commodity_add.vue'
import CommodityList from '@/views/buyer_commodity_list/content/commodity_list.vue'
import CommodityClassify from '@/views/buyer_commodity_classify/content/commodity_classify.vue'
import CommodityRepertory from '@/views/buyer_commodity_repertory/content/commodity_repertory.vue'

defineOptions({
    name: 'BuyerTemplate',
    components: {
        BuyerTheme,
        UserListMain,
        RoleRatio,
        RoleListMain,
        CommodityAdd,
        CommodityList,
        CommodityClassify,
        CommodityRepertory,
    }
})

const props = defineProps({
  currentComponents: {
    type: Array as () => string[], // 接收组件名列表
    default: () => ['Statistic'],
  }
})

const route = useRoute()
const router = useRouter()
const title = ref('')
const input = ref('')

const mallList = ref<{ id: number; name: string }[]>([])
const mallListLoading = ref(false)

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

const to_index = () => {
    router.push('/buyer_index')
}
async function showStoreSelector(item: NavItem) {
    if (mallList.value.length === 0) {
        await loadMallList()
    }

    if (mallList.value.length === 0) {
        ElMessage.warning('暂无可用店铺，请先创建店铺')
        router.push('/buyer_add_mall')
        return
    }

    if (mallList.value.length === 1) {
        localStorage.setItem('mall_id', mallList.value[0].id.toString())
        router.push(item.toFn!(mallList.value[0].id))
        return
    }

    const options = mallList.value.map(m => `<option value="${m.id}">${m.name}</option>`).join('')
    const { value } = await ElMessageBox.prompt(
        `<div style="text-align: left;">
            <p style="margin-bottom: 10px;">请选择要进入的店铺：</p>
            <select id="store-selector-select" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #dcdfe6;">
                ${options}
            </select>
        </div>`,
        '选择店铺',
        {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            dangerouslyUseHTMLString: true,
            inputValue: mallList.value[0].id.toString(),
        }
    )

    const selectedId = parseInt(value || mallList.value[0].id.toString(), 10)
    localStorage.setItem('mall_id', selectedId.toString())
    router.push(item.toFn!(selectedId))
}

interface NavItem {
    value: string
    label: string
    desc: string
    keywords: string[]
    icon: any
    color: string
    tag: string
    tagType: string
    to?: string
    toFn?: (id: number) => string
    highlight?: string
}

const ALL_NAV_ITEMS: NavItem[] = [
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
]

function parseJwtPayload(raw: string): Record<string, any> | null {
    try {
        const jwt = raw.trim().split(' ').pop()!
        const b64 = jwt.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
        return JSON.parse(atob(b64))
    } catch {
        return null
    }
}

function resolveCurrentMallId(): number | null {
    const routeId = route.params.id
    if (routeId) {
        const id = parseInt(routeId as string, 10)
        if (!isNaN(id)) {
            console.log('从路由参数获取 mall_id:', id)
            return id
        }
    }

    const raw = localStorage.getItem('buyer_access_token') || ''
    const payload = parseJwtPayload(raw)

    console.log('JWT payload:', payload)

    if (payload?.mall_id) {
        console.log('从 JWT 获取 mall_id:', payload.mall_id)
        return payload.mall_id
    }

    const mallIdStr = localStorage.getItem('mall_id')
    if (mallIdStr) {
        const id = parseInt(mallIdStr, 10)
        if (!isNaN(id)) {
            console.log('从 localStorage 获取 mall_id:', id)
            return id
        }
    }

    const mallListStr = localStorage.getItem('mall_list')
    if (mallListStr) {
        try {
            const mallList = JSON.parse(mallListStr)
            if (Array.isArray(mallList) && mallList.length > 0) {
                console.log('从 mall_list 获取 mall_id:', mallList[0].id)
                return mallList[0].id
            }
        } catch {}
    }

    if (payload?.state_id_list && Array.isArray(payload.state_id_list) && payload.state_id_list.length > 0) {
        console.log('从 state_id_list 获取 mall_id:', payload.state_id_list[0])
        return payload.state_id_list[0]
    }

    console.log('未找到 mall_id')
    return null
}

function highlight(text: string, kw: string) {
    if (!kw) return text
    const escaped = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    return text.replace(new RegExp(escaped, 'gi'), m => `<em>${m}</em>`)
}

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

function handleNavSelect(item: NavItem) {
    input.value = ''
    execNav(item)
}

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
    console.log('execNav 选中项:', item.label)
    if (item.to) {
        console.log('跳转到固定路由:', item.to)
        router.push(item.to)
        return
    }
    if (item.toFn) {
        const mallId = resolveCurrentMallId()
        console.log('当前 mallId:', mallId)
        if (mallId === null) {
            showStoreSelector(item)
            return
        }
        router.push(item.toFn(mallId))
    }
}

onMounted(() => {
  new BuyerTheme().initTheme()
  console.log('当前路由路径:', route.path);

  // 根据当前路由路径设置页面标题
  console.log('完整路由对象:', route);
  console.log('路由路径:', route.path);
  console.log('路由名称:', route.name);
  console.log('设置标题前的值:', title.value);

  if (route.path.startsWith('/buyer_user_list_id')) {
    title.value = 'xb商城-用户管理页';
    console.log('设置用户管理页标题，新值:', title.value);
  } else if (route.path.startsWith('/buyer_role_list')) {
    title.value = 'xb商城-角色管理页';
    console.log('设置角色管理页标题，新值:', title.value);
  } else if (route.path.startsWith('/buyer_user_statistics')) {
    title.value = 'xb商城-用户统计页';
    console.log('设置用户统计页标题，新值:', title.value);
  }else if (route.path.startsWith('/buyer_commodity_add')) {
    title.value = 'xb商城-商品添加页';
    console.log('设置商品添加页标题，新值:', title.value);
  }else if (route.path.startsWith('/buyer_commodity_list')) {
    title.value = 'xb商城-商品列表页';
    console.log('设置商品列表页标题，新值:', title.value);
  } else if (
    route.path.startsWith('/buyer_commodity_classify')) {
    title.value = 'xb商城-商品分类页';
    console.log('设置商品分类页标题，新值:', title.value);
  } else if (route.path.startsWith('/buyer_commodity_repertory')){
    title.value = 'xb商城-商品库存页';
    console.log('设置商品分类页标题，新值:', title.value);
  }else{
    title.value = 'xb商城';
    console.log('设置默认标题，新值:', title.value);
  }

  // 强制更新视图
  setTimeout(() => {
    console.log('延迟后标题值:', title.value);
  }, 100);
})
</script>

<style scoped>
/* 头部布局 */
.header-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 100%;
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

/* 导航搜索框样式 */
:global(.nav-search-popper) {
  min-width: 320px !important;
}

:global(.nav-search-popper .el-autocomplete-suggestion__list) {
  padding: 4px 0;
}

:global(.nav-search-popper .el-autocomplete-suggestion__wrap) {
  padding: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.nav-item:hover {
  background-color: #f5f7fa;
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  margin-right: 12px;
  flex-shrink: 0;
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
  margin-right: 8px;
}

.nav-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:global(.nav-label em) {
  color: #409eff;
  font-style: normal;
  font-weight: 600;
  background: rgba(64, 158, 255, 0.1);
  padding: 0 2px;
  border-radius: 2px;
}

.nav-desc {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-tag {
  flex-shrink: 0;
}

/* 组件容器样式 - 细线边框 + 悬浮效果 */
.component-container {
  margin-bottom: 24px;
  padding: 20px;
  border: 1px solid #656668;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

/* 悬浮效果 */
.component-container:hover {
  border-color: #409eff;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

/* 细线装饰效果 */
.component-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #409eff 0%, #67c23a 50%, #e6a23c 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.component-container:hover::before {
  opacity: 0.8;
}

.component-container:last-child {
  margin-bottom: 0;
}

/* 响应式间距调整 */
@media (max-width: 768px) {
  .component-container {
    margin-bottom: 16px;
    padding: 16px;
    border-radius: 6px;
  }

  .component-container:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 12px rgba(64, 158, 255, 0.12);
  }
}

@media (max-width: 480px) {
  .component-container {
    margin-bottom: 12px;
    padding: 12px;
    border-radius: 4px;
  }

  .component-container:hover {
    transform: translateY(-0.5px);
    box-shadow: 0 1px 8px rgba(64, 158, 255, 0.1);
  }

  .component-container::before {
    height: 2px;
  }
}

.footer-content {
    text-align: center;
    padding: 10px 0;
}

.el-header {
  border-bottom: 1px solid #e0e0e0;
  padding: 0 20px;
  display: flex;
  align-items: center; /* 垂直居中 */
  justify-content: space-between; /* 左右分布对齐 */
}

.title {
  background: linear-gradient(to right, #7ef0b3, #9c6edd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}
</style>
