<template>
  <el-container class="store-edit-container">
    <el-header>
      <div class="management-navigation">
        <h2 class="title">店铺管理-信息修改页</h2>
      </div>
    </el-header>
    <el-main>
      <div class="form-container">
        <el-card class="edit-card">
          <template #header>
            <div class="card-header">
              <el-icon class="header-icon"><Shop /></el-icon>
              <span class="header-text">店铺基本信息</span>
            </div>
          </template>

          <el-form
            ref="ruleFormRef"
            :model="ruleForm"
            :rules="rules"
            label-width="100px"
            class="store-form"
            size="large"
          >
            <el-row :gutter="30">
              <el-col :span="12">
                <el-form-item label="店铺名称" prop="storeName">
                  <el-input
                    v-model="ruleForm.storeName"
                    placeholder="请输入店铺名称"
                    clearable
                    prefix-icon="Shop"
                  >
                  </el-input>
                </el-form-item>

                <el-form-item label="联系电话" prop="phone">
                  <el-input
                    v-model="ruleForm.phone"
                    placeholder="请输入店铺电话"
                    clearable
                    prefix-icon="Phone"
                  >
                  </el-input>
                </el-form-item>

                <el-form-item label="店铺状态" prop="state">
                  <el-select
                    v-model="ruleForm.state"
                    placeholder="请选择店铺状态"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="item in options"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    >
                      {{ item.label }}
                    </el-option>
                  </el-select>
                </el-form-item>

                <el-form-item label="店铺地址" prop="site">
                  <el-input
                    v-model="ruleForm.site"
                    placeholder="请输入店铺地址"
                    clearable
                    prefix-icon="Location"
                  >
                  </el-input>
                </el-form-item>
              </el-col>

              <el-col :span="12">
                <div class="upload-section">
                  <div class="upload-header">
                    <el-icon class="upload-icon"><Picture /></el-icon>
                    <span class="upload-text">店铺图片</span>
                  </div>

                  <!-- 上传区域 -->
                  <el-upload
                    class="upload-area"
                    drag
                    :limit="1"
                    :on-change="handlePictureChange"
                    :auto-upload="false"
                    :show-file-list="false"
                    :file-list="uploadFileList"
                    accept="image/*"
                  >
                    <div v-if="uploadFileList.length === 0">
                      <el-icon class="upload-icon-large"><Plus /></el-icon>
                      <div class="upload-text-main">点击或拖拽上传图片</div>
                      <div class="upload-text-sub">支持 JPG、PNG 格式</div>
                    </div>
                    <div v-else class="uploaded-file">
                      <img :src="uploadFileList[0].url" alt="已上传图片" class="uploaded-image" />
                      <div class="uploaded-text">{{ uploadFileList[0].name }}</div>
                    </div>
                  </el-upload>

                  <!-- 图片预览区域 -->
                  <div v-if="previewImages.length > 0" class="preview-container">
                    <div class="preview-header">
                      <el-icon><Picture /></el-icon>
                      <span>已上传图片</span>
                    </div>
                    <div class="preview-images">
                      <div
                        v-for="(image, index) in previewImages"
                        :key="index"
                        class="preview-item"
                      >
                        <img
                          :src="image"
                          :alt="`店铺图片`"
                          @click="showPreviewImage(index)"
                          class="preview-image"
                        />
                        <el-button
                          type="danger"
                          circle
                          size="small"
                          class="remove-btn"
                          @click.stop="removePreviewImage(index)"
                        >
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </el-col>
            </el-row>

            <el-form-item label="店铺描述" prop="describe">
              <el-input
                v-model="ruleForm.describe"
                type="textarea"
                :rows="4"
                placeholder="请详细描述您的店铺特色、经营理念、主营商品等信息..."
                maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item class="form-actions">
              <el-button type="primary" size="large" @click="submitForm">
                <el-icon><Check /></el-icon>
                保存修改
              </el-button>
              <el-button size="large" @click="resetForm">
                <el-icon><Refresh /></el-icon>
                清空表单
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </div>
    </el-main>
    <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
  </el-container>

  <!-- 图片预览对话框 -->
  <el-dialog
    v-model="previewDialogVisible"
    title="图片预览"
    width="80%"
    center
    @close="closePreview"
  >
    <div class="preview-dialog-content">
      <img
        v-if="currentPreviewIndex >= 0 && previewImages[currentPreviewIndex]"
        :src="previewImages[currentPreviewIndex]"
        alt="预览图片"
        class="preview-dialog-image"
      />
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="closePreview">关闭</el-button>
      </span>
    </template>
  </el-dialog>
</template>
<script setup lang="ts">
import {ref,onMounted } from 'vue';
import axios from 'axios';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import BuyerTheme from '@/moon/buyer_theme';
import {
  Delete,
  Shop,
  Phone,
  Location,
  Picture,
  Plus,
  Check,
  Refresh
} from '@element-plus/icons-vue';

defineOptions({
  name:'BuyerStoreManageIndex',
})
// 预览图片URL列表
const previewImages = ref<string[]>([])
// 当前预览图片索引
const currentPreviewIndex = ref<number>(-1)
// 是否显示预览对话框
const previewDialogVisible = ref<boolean>(false)
// 上传组件的文件列表
const uploadFileList = ref<any[]>([])

const Axios = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
});
const options = [
  {
    value:1,
    label:'开启'
  },
  {
    value:0,
    label:'关闭'
  }
]
// 获取路由实例
const route = useRoute();
// 从路由参数中获取 mall_id
const mall_id = route.params.id;

const token= localStorage.getItem('buyer_access_token');
interface RuleForm {
  storeName: string;
  phone:string;
  site:string;
  describe:string;
  img:any;
  state:number;
}
const ruleForm = ref<RuleForm>({
  storeName: '',
  phone:'',
  site:'',
  describe:'',
  img:[],
  state:1,
});


const rules = ref({
  storeName: [
    { required: true, message: '请输入店铺名称', trigger: 'blur' },
    { min: 2, max: 50, message: '店铺名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  state: [
    { required: true, message: '请选择店铺状态', trigger: 'change' }
  ],
  site: [
    { required: true, message: '请输入店铺地址', trigger: 'blur' },
    { min: 5, max: 100, message: '地址长度在 5 到 100 个字符', trigger: 'blur' }
  ],
  describe: [
    { required: true, message: '请输入店铺描述', trigger: 'blur' },
    { min: 10, max: 200, message: '描述长度在 10 到 200 个字符', trigger: 'blur' }
  ]
});

onMounted(async()=>{
  new BuyerTheme().toggleTheme(true)
  const formdata = new FormData()
  formdata.append("id",mall_id.toString())
  formdata.append("token",token||'')
  try{
    const res = await Axios.post('/buyer_get_mall_info',formdata)
    if(res.status == 200){
      if (res.data.current){
        // 自动填入店铺信息
        ruleForm.value = {
          storeName: res.data.data[0].mall_name|| '',
          phone: res.data.data[0].phone || '',
          site: res.data.data[0].site || '',
          describe: res.data.data[0].info || '',
          img: null,
          state: Number(res.data.data[0].state),
        }
        console.log(res.data.data[0].state);


        // 处理B64格式的图片数据
        if(res.data.data[0].img){
          const processedImages = processB64Images(res.data.data[0].img)
          previewImages.value = processedImages
          if(processedImages.length > 0){
            try {
              const file = base64ToFile(processedImages[0], 'store-image.jpg')
              uploadFileList.value = [{
                name: 'store-image.jpg',
                url: processedImages[0],
                raw: file
              }]
              ruleForm.value.img =uploadFileList.value[0]

              console.log();

            } catch (error) {
              console.error('B64转文件失败:', error)
            }
          }
        }

        ElMessage.success('店铺信息加载成功')
      }
    }
  }catch(err){
  }
})

// 图片预览处理函数
const handlePictureChange = async (file: any) => {
  try {
    const base64String = await fileToBase64(file.raw)
    previewImages.value = [base64String]
    ruleForm.value.img = file
    // 更新上传文件列表
    uploadFileList.value = [{
      name: file.name,
      url: base64String,
      raw: file.raw
    }]
  } catch (error) {
    console.error('文件转换失败:', error)
    ElMessage.error('图片处理失败')
  }
}

// 删除预览图片
const removePreviewImage = (index: number) => {
  previewImages.value = []
  ruleForm.value.img = null
  uploadFileList.value = []
}

// 预览图片
const showPreviewImage = (index: number) => {
  currentPreviewIndex.value = index
  previewDialogVisible.value = true
}

// 关闭预览对话框
const closePreview = () => {
  previewDialogVisible.value = false
  currentPreviewIndex.value = -1
}

// B64字符串转文件对象
const base64ToFile = (base64String: string, filename: string = 'image.jpg'): File => {
  // 提取base64数据和mime类型
  const arr = base64String.split(',')
  const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/jpeg'
  const bstr = atob(arr[1])
  let n = bstr.length
  const u8arr = new Uint8Array(n)

  while (n--) {
    u8arr[n] = bstr.charCodeAt(n)
  }

  return new File([u8arr], filename, { type: mime })
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

// 处理B64图片数据
const processB64Images = (imgData: any): string[] => {
  if(!imgData) return []
  if(Array.isArray(imgData)){
    return imgData.map((imgItem: any) => {
      if(typeof imgItem === 'string' && imgItem.startsWith('data:image')){
        return imgItem
      }
      if(imgItem && imgItem.url){
        return imgItem.url
      }
      if(typeof imgItem === 'string'){
        return `data:image/jpeg;base64,${imgItem}`
      }
      return ''
    }).filter(Boolean) // 过滤掉空值
  }

  if(typeof imgData === 'string'){
    if(imgData.startsWith('data:image')){
      return [imgData]
    }
    return [`data:image/jpeg;base64,${imgData}`]
  }

  return []
}

// 提交表单
const submitForm = async () => {
  console.log(ruleForm.value);
  const commit_form =  new FormData();
  commit_form.append("token",token||'')
  commit_form.append("id",mall_id.toString())
  commit_form.append("mall_name",ruleForm.value.storeName)
  commit_form.append("mall_site",ruleForm.value.site)
  commit_form.append("mall_phone",ruleForm.value.phone)
  commit_form.append("info",ruleForm.value.describe)
  commit_form.append("state",ruleForm.value.state.toString())
  try{
    const res = await Axios.patch('/buyer_update_mall',commit_form)
    if(res.status == 200){
      if (res.data.current){
        const img_form = new FormData();
        img_form.append("token",token||'')
        img_form.append("id",mall_id.toString())
        img_form.append("img",ruleForm.value.img.raw)
        try{
          const img_res = await Axios.patch('/buyer_update_img',img_form)
          if(img_res.status == 200){
            if (img_res.data.current){
              ElMessage.success('信息更新成功')
            }else{
              ElMessage.warning('信息更新成功，但图片更新失败')
            }
          }
        }catch(err){
          ElMessage.warning('信息更新成功，但图片更新失败')
        }
      }
    }
  }catch(err){
    ElMessage.error('更新失败')
  }
}

// 重置表单
const resetForm = () => {
  ruleForm.value = {
    storeName: '',
    phone: '',
    site: '',
    describe: '',
    img: [],
    state: 1,
  }
  previewImages.value = []
  uploadFileList.value = []

}

</script>

<style scoped>
/* 整体容器样式 */
.store-edit-container {
  min-height: 100vh;
}

/* 导航栏样式 */
.management-navigation {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0 20px;
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

/* 深色主题下的标题样式 */
.dark .title {
  background: linear-gradient(to right, #46e2cb, #742bd9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.el-header {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  padding: 20px;
  margin-bottom: 0;
  transition: all 0.3s ease;
}

/* 表单容器样式 */
.form-container {
  padding: 40px 20px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 卡片样式 */
.edit-card {
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--el-border-color);
  overflow: hidden;
  transition: all 0.3s ease;
  background: var(--el-bg-color);
}

.edit-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.edit-card :deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 20px;
  color: white;
}

.header-text {
  font-size: 18px;
  font-weight: 600;
}

/* 表单样式 */
.store-form {
  padding: 32px;
}

.store-form :deep(.el-form-item) {
  margin-bottom: 24px;
}

/* 上传区域样式 */
.upload-section {
  background: var(--el-fill-color-lighter);
  border-radius: 12px;
  padding: 24px;
  border: 2px dashed var(--el-border-color);
  transition: all 0.3s ease;
}

.upload-section:hover {
  border-color: var(--el-color-primary);
  background: var(--el-fill-color-light);
}

.upload-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.upload-icon {
  font-size: 18px;
  color: var(--el-color-primary);
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

/* 上传文件显示样式 */
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
  border: 1px solid var(--el-border-color);
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
  font-weight: 500;
  font-size: 14px;
}

.preview-images {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.preview-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid var(--el-border-color);
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.3s;
}

.preview-image:hover {
  transform: scale(1.05);
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(245, 108, 108, 0.9);
  border: none;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.remove-btn:hover {
  background: rgba(245, 108, 108, 1);
  transform: scale(1.1);
}

/* 表单操作按钮样式 */
.form-actions {
  margin-top: 32px;
  text-align: center;
}

.form-actions :deep(.el-form-item__content) {
  justify-content: center;
  gap: 16px;
}

.form-actions .el-button {
  min-width: 120px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.form-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 选择器样式 */
.store-form :deep(.el-select__wrapper) {
  border-radius: 8px;
  border: 1px solid #e1e8ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.store-form :deep(.el-select__wrapper:hover) {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

/* 预览对话框样式 */
.preview-dialog-content {
  text-align: center;
  padding: 20px;
}

.preview-dialog-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: center;
}

/* 底部样式 */
.footer-content {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
  padding: 20px 0;
  background: rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .store-form {
    padding: 20px;
  }

  .el-row {
    flex-direction: column;
  }

  .el-col {
    width: 100%;
  }

  .upload-section {
    margin-top: 20px;
  }

  .form-actions :deep(.el-button) {
    margin: 8px;
    width: 100%;
    max-width: 200px;
  }

  .title {
    font-size: 20px;
  }

  .form-container {
    padding: 20px 10px;
  }
}

/* 深色主题下的额外样式 */
.dark .upload-section {
  background: var(--el-fill-color-lighter);
}

.dark .preview-container {
  background: var(--el-fill-color-lighter);
}

@media (max-width: 480px) {
  .edit-card {
    margin: 0 10px;
  }

  .store-form {
    padding: 16px;
  }

  .preview-item {
    width: 60px;
    height: 60px;
  }
}
</style>
