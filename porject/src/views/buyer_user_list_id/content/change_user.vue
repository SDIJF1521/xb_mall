<template>
  <div class="add-user-container">

    <el-form ref="formRef" :model="formData" class="user-form" :rules="rules">
      <el-row :gutter="30">
        <el-col :span="12">
          <div class="form-section">
            <div class="section-title">
              <el-icon><Edit /></el-icon>
              <span>基本信息</span>
            </div>

            <el-form-item label="用户名" prop="name">
              <el-input v-model="formData.name" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="formData.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>
            <el-form-item label="权限" prop="authority">
              <el-radio-group v-model="formData.authority" class="authority-radio-group">
                <el-radio
                  v-for="role in roleOptions"
                  :key="role.id"
                  :value="role.id"
                  border
                >
                  {{ role.name[1] }}
                </el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="formData.email" type="email" placeholder="请输入邮箱地址" />
            </el-form-item>
          </div>
        </el-col>

          <!--图片上传-->
          <el-col :span="12">
            <div class="form-section">
              <div class="section-title">
                <el-icon><Picture /></el-icon>
                <span>用户头像</span>
              </div>

              <div class="upload-section">
                <el-upload
                  class="upload-area"
                  drag
                  action="#"
                  :limit="1"
                  :file-list="uploadFileList"
                  :on-change="handlePictureChange"
                  :auto-upload="false"
                  accept="image/*"
                >
                  <div v-if="!previewImage" class="upload-placeholder">
                    <el-icon class="upload-icon-large"><Plus /></el-icon>
                    <div class="upload-text-main">点击或拖拽上传图片</div>
                    <div class="upload-text-sub">支持 JPG、PNG、GIF 格式</div>
                  </div>
                  <div v-else class="uploaded-file">
                    <img :src="previewImage" class="uploaded-image" @click="showPreviewImage" />
                    <div class="uploaded-text">{{ uploadFileList[0]?.name }}</div>
                  </div>
                  <template #tip>
                    <div class="upload-tip">
                      <el-icon><InfoFilled /></el-icon>
                      <span>建议上传 200x200 像素的正方形图片，支持 JPG、PNG、GIF 格式，文件大小不超过 2MB</span>
                    </div>
                  </template>
                </el-upload>

                <!-- 图片预览区域 -->
                <div v-if="previewImage" class="preview-container">
                  <div class="preview-header">
                    <el-icon><Picture /></el-icon>
                    <span>图片预览</span>
                  </div>
                  <div class="preview-images">
                    <div class="preview-item" @click="showPreviewImage">
                      <img :src="previewImage" class="preview-image" />
                      <el-button
                        class="remove-btn"
                        type="danger"
                        size="small"
                        circle
                        @click.stop="removePreviewImage"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 图片预览对话框 -->
              <el-dialog
                v-model="previewDialogVisible"
                title="图片预览"
                width="600px"
                center
                append-to-body
                custom-class="preview-dialog"
              >
                <div class="preview-dialog-content">
                  <img :src="previewImage" class="preview-dialog-image" />
                </div>
                <template #footer>
                  <el-button @click="closePreview" type="primary">关闭</el-button>
                </template>
              </el-dialog>
            </div>
          </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-button type="primary" style="width: 100%;" @click="change_user_commit">提交</el-button>
        </el-col>
        <el-col :span="12">
          <el-button type="primary" style="width: 100%;" @click="closeDialog">关闭</el-button>
      </el-col>
    </el-row>
    </el-form>

  </div>
</template>
<script setup lang="ts">

import {ref,onMounted,reactive} from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'
import router from '@/router'
import axios from 'axios'

import { Delete, Picture, Plus, InfoFilled, User, Edit } from '@element-plus/icons-vue'

defineOptions({
    name: 'AddUser',
})

const id = ref(useRoute().params.id)

const Axios = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
})

const emit = defineEmits(['child-event'])
const token = localStorage.getItem('buyer_access_token')
const poops = defineProps<{
  name: string
  password: string
  authority:number
  img: UploadFile | string | null
  email:string

}>()

interface UploadFile {
  name: string
  raw: File
  url?: string
}

interface FormData{
  user:string
  name: string
  password: string
  authority:number
  img: UploadFile | string | null
  email:string
}

const formData = reactive<FormData>({
  user: '',
  name: '',
  password: '',
  authority: 0,
  img: null,
  email: ''
})

// 添加formRef定义
const formRef = ref<any>(null)


// 密码校验函数
function validatePassword(rule: any, value: any, callback: any) {
  if (!value) {
    callback(new Error('请输入密码'))
  } else if (value.length < 6) {
    callback(new Error('密码长度不能小于6位'))
  } else if (!/[a-zA-Z]/.test(value)) {
    callback(new Error('密码必须包含字母'))
  } else if (!/[0-9]/.test(value)) {
    callback(new Error('密码必须包含数字'))
  } else {
    callback()
  }

}

// 邮箱校验函数
function validateEmail(rule: any, value: any, callback: any) {
  if (!value) {
    callback(new Error('请输入邮箱'))
  } else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(value)) {
    callback(new Error('请输入正确的邮箱格式'))
  } else {
    callback()
  }
}

// 表单校验
const rules = reactive({
  name: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' },
             { validator: validatePassword, trigger: 'blur' }
            ],
  authority: [{ required: true, message: '请选择用户权限', trigger: 'change' },],
  img: [{ required: true, message: '请上传用户头像', trigger: 'change' },
        ],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' },
        { validator: validateEmail, trigger: 'blur' }
        ]
})

const closeDialog = () => {
  emit('child-event', false)
}

// 上传相关状态
const uploadFileList = ref<any[]>([])
const previewImage = ref<string>('')
const previewDialogVisible = ref<boolean>(false)
const roleOptions = ref<Array<{id: number,name: string}>>([])

const fetchRoleList = async () => {
  try {
    const role_formdata = new FormData()
    role_formdata.append('token', token || '')
    role_formdata.append('stroe_id', id.value?.toString() || '')

    const response = await Axios.post('/buyer_get_role', role_formdata)

    if (response.data.code === 200 && response.data.data) {
      // 将后端返回的权限数据转换为前端需要的格式
      roleOptions.value = response.data.data.map((role: any) => {
        const roleId = Object.keys(role)[0]
        const roleName = Object.values(role)[0]
        return {
          id: parseInt(roleId),
          name: roleName as string
        }
      })
    } else {
      console.warn('获取权限列表失败，使用默认权限选项')
      // 如果获取失败，使用默认权限选项
      roleOptions.value = [
        { id: 0, name: '普通用户' },
        { id: 1, name: '管理员' },
        { id: 2, name: '超级管理员' }
      ]
    }
  } catch (error) {
    console.error('获取权限列表失败:', error)
    // 错误时使用默认权限选项
    roleOptions.value = [
      { id: 0, name: '普通用户' },
      { id: 1, name: '管理员' },
      { id: 2, name: '超级管理员' }
    ]
  }
}


// 判断是否为图片文件
const isImageFile = (file: File): boolean => {
  const imageTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']
  return imageTypes.includes(file.type)
}

// 验证图片文件大小（最大2MB）
const validateImageSize = (file: File): boolean => {
  const maxSize = 2 * 1024 * 1024 // 2MB
  if (file.size > maxSize) {
    ElMessage.error('图片文件大小不能超过 2MB')
    return false
  }
  return true
}

// 图片处理函数
const handlePictureChange = async (file: UploadFile) => {
  try {
    // 检查是否为图片文件
    if (!isImageFile(file.raw)) {
      ElMessage.error('请上传图片文件（支持 JPG、PNG、GIF、WebP、BMP 格式）')
      return
    }

    // 验证图片大小（2MB限制）
    if (!validateImageSize(file.raw)) {
      return
    }

    const base64String = await fileToBase64(file.raw)
    previewImage.value = base64String
    formData.img = file

    // 更新上传文件列表
    uploadFileList.value = [{
      name: file.name,
      url: base64String,
      raw: file
    }]
  } catch (error) {
    console.error('文件转换失败:', error)
    ElMessage.error('图片处理失败')
  }
}

// 删除预览图片
const removePreviewImage = () => {
  previewImage.value = ''
  formData.img = null
  uploadFileList.value = []
}

// 预览图片
const showPreviewImage = () => {
  previewDialogVisible.value = true
}

// 关闭预览对话框
const closePreview = () => {
  previewDialogVisible.value = false
}

// 文件对象转B64字符串
const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = error => reject(error)
  })
}

// 清理base64字符串中的非法字符
const cleanBase64String = (base64String: string): string => {
  // 移除所有空白字符
  let cleaned = base64String.replace(/\s/g, '')

  // 移除base64字符串中的非法字符（保留字母、数字、+、/、=）
  cleaned = cleaned.replace(/[^A-Za-z0-9+/=]/g, '')

  // 确保base64字符串长度是4的倍数（必要时添加=）
  const padding = cleaned.length % 4
  if (padding) {
    cleaned += '='.repeat(4 - padding)
  }

  return cleaned
}

// B64字符串转文件对象
const base64ToFile = (base64String: string, fileName: string = 'avatar.png'): File => {
  try {
    let base64Data: string
    let mimeType: string = 'image/png'

    // 检查是否包含data URL前缀
    if (base64String.includes('data:')) {
      // 完整的data URL格式: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
      const arr = base64String.split(',')
      if (arr.length < 2) {
        throw new Error('无效的data URL格式')
      }
      mimeType = arr[0].match(/:(.*?);/)?.[1] || 'image/png'
      base64Data = arr[1]
    } else {
      // 纯base64数据，默认为PNG格式
      base64Data = base64String
    }

    // 检查base64数据是否有效
    if (!base64Data || base64Data.trim() === '') {
      throw new Error('Base64数据为空')
    }

    // 清理base64数据中的非法字符
    base64Data = cleanBase64String(base64Data)

    // 检查base64数据是否只包含有效字符
    const base64Regex = /^[A-Za-z0-9+/]*={0,2}$/
    if (!base64Regex.test(base64Data)) {
      throw new Error('Base64数据包含无效字符')
    }

    // 解码base64数据
    const bstr = atob(base64Data)
    let n = bstr.length
    const u8arr = new Uint8Array(n)

    while (n--) {
      u8arr[n] = bstr.charCodeAt(n)
    }

    // 创建File对象
    return new File([u8arr], fileName, { type: mimeType })
  } catch (error) {
    console.error('base64转文件失败:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    throw new Error(`base64字符串转换失败: ${errorMessage}`)
  }
}

onMounted(async () => {
  // 优先获取权限列表
  await fetchRoleList()

  formData.user = poops.name
  formData.name = poops.name
  formData.password = poops.password
  formData.authority = poops.authority
  formData.email = poops.email
  console.log(poops.authority);


  // 处理图片数据 - 如果提供的是base64字符串，转换为文件对象
  if (poops.img) {
    if (typeof poops.img === 'string') {
      // 如果是base64字符串，转换为文件对象
      try {
        console.log('收到图片数据:', typeof poops.img, '长度:', poops.img.length)
        console.log('图片数据前50字符:', poops.img.substring(0, 50))
        console.log('图片数据后50字符:', poops.img.substring(Math.max(0, poops.img.length - 50)))

        // 检查图片数据是否包含非法字符
        const hasInvalidChars = /[^A-Za-z0-9+/=]/.test(poops.img)
        if (hasInvalidChars) {
          console.warn('图片数据包含非base64字符，可能需要清理')
        }

        // 检查是否是有效的base64字符串
        if (poops.img.trim() === '') {
          console.warn('图片数据为空字符串')
          return
        }

        // 数据库中的图片数据通常是纯base64，需要添加前缀
        let imageUrl = poops.img
        if (!poops.img.includes('data:')) {
          // 纯base64数据，添加data URL前缀 (与el-avatar一致，使用PNG格式)
          imageUrl = `data:image/png;base64,${poops.img}`
        }

        try {
          const file = base64ToFile(imageUrl, 'user_avatar.png')
          const uploadFile: UploadFile = {
            name: 'user_avatar.png',
            raw: file,
            url: imageUrl
          }
          formData.img = uploadFile
          previewImage.value = imageUrl
          uploadFileList.value = [uploadFile]
          console.log('图片数据转换成功')
        } catch (convertError) {
          console.error('Base64转换失败，尝试备用方案:', convertError)
          // 如果转换失败，仍然显示图片但标记为需要重新上传
          formData.img = null
          previewImage.value = imageUrl
          uploadFileList.value = []
          ElMessage.warning('头像数据格式异常，请重新上传头像')
        }
      } catch (error) {
        console.error('图片数据转换失败:', error)
        const errorMessage = error instanceof Error ? error.message : String(error)
        ElMessage.error(`头像数据加载失败: ${errorMessage}`)
      }
    } else {
      // 如果已经是文件对象，直接使用
      formData.img = poops.img
      if (poops.img.url) {
        previewImage.value = poops.img.url
        uploadFileList.value = [poops.img]
      }
    }
  } else {
    console.log('没有接收到图片数据')
  }
})

async function change_user_commit(){
  // 添加表单验证
  if (!formRef.value) {
    console.error('表单引用未找到')
    return
  }

  try {
    // 执行表单验证
    await formRef.value.validate()
    console.log('表单验证通过')
  } catch (error) {
    console.log('表单验证失败')
    ElMessage.error('请检查表单输入是否正确')
    return
  }

  console.log(formData);
  const change_fromData = new FormData()
  change_fromData.append('token', token||'')
  change_fromData.append('stroe_id',id.value.toString()||'')
  change_fromData.append('user', formData.user||'')
  change_fromData.append('user_name', formData.name||'')
  change_fromData.append('user_password', formData.password||'')
  change_fromData.append('authority', formData.authority.toString()||'')
  change_fromData.append('email', formData.email||'')
  const res = await Axios.patch('/buyer_user_amend',change_fromData)
  try{
    if (res.status ==200){
      if (res.data.current){
        ElMessage.success('用户信息修改成功')
        if (formData.img) {
          // 检查formData.img是否为文件对象类型
          if (typeof formData.img !== 'string' && formData.img.raw) {
            const commit_buser_img = new FormData()
            commit_buser_img.append('token', token||'')
            commit_buser_img.append('stroe_id',id.value.toString()||'')
            commit_buser_img.append('name', formData.name||'')
            commit_buser_img.append('file', formData.img.raw)
            const res_img = await Axios.post('/buyer_user_picture_uploading',commit_buser_img)
            if (res_img.status ==200){
              if (res_img.data.current){
                ElMessage.success('用户头像修改成功')
              }else{
                ElMessage.error('用户头像修改失败')
              }
            }
            emit('child-event', false)

          }
        }
      }else{
        ElMessage.error('权限不足')
      }
    }
  }catch(error){
    console.error('用户信息修改失败:', error)
    ElMessage.error('用户信息修改失败')
  }
}

</script>
<style scoped>
/* 整体容器美化 */
.add-user-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}


@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}


/* 表单区域美化 */
.user-form {
  background: var(--el-fill-color-blank);
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
}

.form-section {
  padding: 30px 20px;
  height: 100%;
}

.section-title {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--el-color-primary-light-8);
  color: var(--el-text-color-primary);
  font-size: 18px;
  font-weight: 600;
}

.section-title .el-icon {
  font-size: 20px;
  color: var(--el-color-primary);
  margin-right: 8px;
}

/* 表单整体美化 */
.el-form {
  padding: 20px;
  background: var(--el-fill-color-blank);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 表单项美化 */
.el-form-item {
  margin-bottom: 20px;
}

.el-form-item__label {
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 14px;
}

/* 输入框美化 */
.el-input {
  border-radius: 8px;
}

.el-input__inner {
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  transition: all 0.3s ease;
}

.el-input__inner:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 权限单选框美化 */
.authority-radio-group {
  display: flex;
  gap: 12px;
}

.authority-radio-group .el-radio {
  margin-right: 0;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.authority-radio-group .el-radio.is-checked {
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

/* 上传区域样式 */
.upload-section {
  margin-top: 10px;
}

.upload-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-size: 16px;
}

.upload-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.upload-icon {
  font-size: 18px;
  color: var(--el-color-primary);
  margin-right: 8px;
}

.upload-text {
  font-size: 14px;
  font-weight: 500;
}

.upload-area {
  width: 100%;
  height: 180px;
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color);
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-icon-large {
  font-size: 48px;
  color: var(--el-color-primary);
  margin-bottom: 16px;
}

.upload-text-main {
  font-size: 16px;
  color: var(--el-text-color-primary);
  font-weight: 500;
  margin-bottom: 8px;
}

.upload-text-sub {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

/* 上传提示样式 */
.upload-tip {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--el-color-info-light-9);
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--el-color-info);
  line-height: 1.4;
}

.upload-tip .el-icon {
  font-size: 14px;
  color: var(--el-color-info);
}

/* 已上传文件显示样式 */
.uploaded-file {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}

.uploaded-image {
  max-width: 120px;
  max-height: 120px;
  object-fit: contain;
  border-radius: 8px;
  margin-bottom: 8px;
}

.uploaded-text {
  font-size: 14px;
  color: var(--el-text-color-regular);
  text-align: center;
  word-break: break-all;
}

/* 图片预览区域样式 */
.preview-container {
  margin-top: 20px;
  padding: 15px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.preview-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.preview-header el-icon {
  margin-right: 8px;
  color: var(--el-color-primary);
}

.preview-images {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.preview-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--el-border-color);
  cursor: pointer;
  transition: all 0.3s ease;
}

.preview-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.preview-item:hover .remove-btn {
  opacity: 1;
}

/* 预览对话框样式 */
.preview-dialog-content {
  text-align: center;
  padding: 20px;
}

.preview-dialog-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 对话框自定义样式 */
.preview-dialog {
  border-radius: 12px;
  overflow: hidden;
}

.preview-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
  color: white;
  padding: 16px 20px;
  margin: 0;
}

.preview-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.preview-dialog :deep(.el-dialog__headerbtn) {
  top: 16px;
  right: 20px;
}

.preview-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 18px;
}

.preview-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: var(--el-color-primary-light-7);
}

/* 按钮美化样式 */
.button-row {
  margin-top: 30px;
  padding: 20px;
  background: var(--el-fill-color-lighter);
  border-radius: 12px;
  display: flex;
  justify-content: center;
  gap: 20px;
}

.button-row .el-col {
  display: flex;
  justify-content: center;
}

.button-row .el-button {
  min-width: 120px;
  height: 44px;
  border-radius: 22px;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.button-row .el-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.button-row .el-button:hover::before {
  left: 100%;
}

.button-row .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.3);
}

.button-row .el-button:active {
  transform: translateY(0);
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.2);
}

/* 提交按钮特殊样式 */
.button-row .el-button[type="primary"]:first-child {
  background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
  border: none;
}

.button-row .el-button[type="primary"]:first-child:hover {
  background: linear-gradient(135deg, var(--el-color-primary-light-1) 0%, var(--el-color-primary-light-2) 100%);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.4);
}

/* 重置按钮特殊样式 */
.button-row .el-button[type="primary"]:nth-child(2) {
  background: linear-gradient(135deg, var(--el-color-success) 0%, var(--el-color-success-light-3) 100%);
  border: none;
}

.button-row .el-button[type="primary"]:nth-child(2):hover {
  background: linear-gradient(135deg, var(--el-color-success-light-1) 0%, var(--el-color-success-light-2) 100%);
  box-shadow: 0 8px 25px rgba(103, 194, 58, 0.4);
}

/* 关闭按钮特殊样式 */
.button-row .el-button[type="primary"]:last-child {
  background: linear-gradient(135deg, var(--el-color-warning) 0%, var(--el-color-warning-light-3) 100%);
  border: none;
}

.button-row .el-button[type="primary"]:last-child:hover {
  background: linear-gradient(135deg, var(--el-color-warning-light-1) 0%, var(--el-color-warning-light-2) 100%);
  box-shadow: 0 8px 25px rgba(230, 162, 60, 0.4);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .add-user-container {
    padding: 20px 10px;
  }


  .header-icon {
    font-size: 36px;
    margin-bottom: 12px;
  }

  .header-title {
    font-size: 24px;
  }

  .header-subtitle {
    font-size: 14px;
  }

  .form-section {
    padding: 20px 15px;
  }

  .section-title {
    font-size: 16px;
    margin-bottom: 20px;
  }

  .upload-area {
    height: 150px;
  }

  .upload-icon-large {
    font-size: 36px;
    margin-bottom: 12px;
  }

  .upload-text-main {
    font-size: 14px;
  }

  .upload-text-sub {
    font-size: 12px;
  }

  .preview-item {
    width: 80px;
    height: 80px;
  }

  .upload-tip {
    font-size: 11px;
    padding: 6px 10px;
  }

  .el-form {
    padding: 15px;
  }

  .authority-radio-group {
    flex-direction: column;
    gap: 8px;
  }

  .authority-radio-group .el-radio {
    width: 100%;
    text-align: center;
  }
}
</style>
