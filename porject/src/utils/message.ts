import { ElMessage } from 'element-plus'
import type { MessageOptions } from 'element-plus'

const DURATION = 1500

type Param = string | MessageOptions

const wrap =
  (type: 'success' | 'warning' | 'error' | 'info') =>
  (param: Param) => {
    const opts: MessageOptions =
      typeof param === 'string' ? { message: param } : param
    return ElMessage[type]({ duration: DURATION, ...opts })
  }

const message = Object.assign(
  (param: Param) => {
    const opts: MessageOptions =
      typeof param === 'string' ? { message: param } : param
    return ElMessage({ duration: DURATION, ...opts })
  },
  {
    success: wrap('success'),
    warning: wrap('warning'),
    error: wrap('error'),
    info: wrap('info'),
  },
)

export default message
