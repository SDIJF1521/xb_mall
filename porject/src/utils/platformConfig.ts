import { ref } from 'vue'
import axios from 'axios'

export interface PlatformInfo {
  platform_name: string
  copyright_text: string
  icp_number: string
  contact_email: string
  contact_phone: string
}

const CACHE_KEY = 'platform_info'
const CACHE_TTL = 10 * 60 * 1000 // 10 分钟

const _info = ref<PlatformInfo>({
  platform_name: 'xb商城',
  copyright_text: '版权所有 © xb商城，保留所有权利。',
  icp_number: '',
  contact_email: '',
  contact_phone: '',
})

let _loaded = false

function _readCache(): PlatformInfo | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const cached = JSON.parse(raw)
    if (Date.now() - (cached._ts || 0) > CACHE_TTL) return null
    return cached.data as PlatformInfo
  } catch {
    return null
  }
}

function _writeCache(data: PlatformInfo) {
  localStorage.setItem(CACHE_KEY, JSON.stringify({ data, _ts: Date.now() }))
}

export function updatePlatformCache(data: Partial<PlatformInfo>) {
  Object.assign(_info.value, data)
  _writeCache(_info.value)
}

async function _fetch() {
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/platform_info')
    if (data?.success && data.data) {
      Object.assign(_info.value, data.data)
      _writeCache(_info.value)
    }
  } catch {
    // 网络失败时保持缓存或默认值
  }
}

export function usePlatformConfig() {
  if (!_loaded) {
    _loaded = true
    const cached = _readCache()
    if (cached) Object.assign(_info.value, cached)
    _fetch()
  }
  return { platformInfo: _info }
}
