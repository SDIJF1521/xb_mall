<template>
  <div>
    <el-container>
      <el-header>
        <AppNavigation/>
      </el-header>
      <el-main>

        <!--头像框-->
        <div>
          <el-upload
            class="upload-demo"
            drag
            :auto-upload="false"
            v-model:file-list="fileList"
            :limit="1"
            :disabled = on_upload
            multiple
            :on-change="handleFileChange"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              在此处托拽或<em>上传图片</em>
            </div>
          </el-upload>
          <!-- 图片预览区域 -->
          <div class="preview-container" v-if="previewImage">
              <el-card class="preview-card" shadow="hover">
                <img :src="previewImage" class="preview-image" alt="预览图片">
                <el-button class="delete-button" @click = 'imageDelete' plain><el-icon><Delete /></el-icon></el-button>
              </el-card>
          </div>
        </div>


        <!--基本信息填写框-->
        <div class="content">
          <div>
              <el-input
                v-model="name"
                style="width: 300px"
                placeholder="昵称"
                clearable
              />
          </div>

        
          <div >
            <el-select v-model="value" placeholder="Select" style="width: 300px">
              <el-option
                v-for="item in options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
                :disabled="item.disabled"
              />
            </el-select>
          </div>
          
          <div>
              <el-text class="mx-1" size="large">年龄：</el-text>
              <el-input-number
                  v-model="num"
                  :min="1"
                  :max="300"
                  controls-position="right"
                  size="large"
                  style="width: 250px"
                />
          </div>
          <el-button style="width: 300px; height: 300;" @click="SubmitEvent" round>提交</el-button>
      </div>

      </el-main>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>
  </div>
  
  
</template>

<script>
import AppNavigation from '@/moon/navigation.vue'
import axios from 'axios';
import { ElMessage } from 'element-plus';
import router from '@/router';

export default {
  name: "PersonalDetailsChange",
  data() {
  return {
    fileList: [],
    on_upload: false,
    previewImage: '',
    value: '未知',
    num: 1,
    name: '',
    options: [
      { value: '男', label: '男' },
      { value: '女', label: '女' },
      { value: '未知', label: '未知' }
    ],
  Axios:axios.create({
     baseURL: 'http://127.0.0.1:8000/api'
  })
  }
},


// 进入网页后立即执行方法
mounted() {
  const formdata = new FormData()
  const token = localStorage.getItem('access_token')
  formdata.append('token', token)
  this.Axios.post('/userinfo', formdata)
    .then(ref => {
      if (ref.status == 200 && ref.data.current) {
        this.value = ref.data.data[3] || '未知'
        this.num = ref.data.data[2] || 1
        this.name = ref.data.data[1] || ''
      }
    })
},
  watch: {
    fileList: {
      deep: true,
      handler(newVal) {
        console.log('文件列表更新:', newVal);
        if (newVal.length == 1){
          const imageExtensions = ['jpg','png','gif','bmp','webp','svg','jpeg']
          const file = newVal[0];
          const filename = file?.name || '';
          const ext = filename.split('.').pop()?.toLowerCase();
          if (!(ext && imageExtensions.includes(ext))){
            ElMessage.error('文件必须是图片');
            this.fileList = [];
            this.on_upload = false;
          }else{
            this.on_upload = true;
          }
          
        }else{
          this.on_upload = false;
        }
        this.updatePreview(); // 监听文件列表变化更新预览
      }
    }
  },
  components: {
    AppNavigation
  },
  methods: {
    // 处理文件变化
    handleFileChange(file, fileList) {
      console.log('选择的文件:', file);
      this.updatePreview();
    },
    
    // 更新预览图片
    updatePreview() {
      if (this.fileList.length > 0) {
        const file = this.fileList[0];
        // 优先使用已上传的URL，否则使用本地文件URL
        this.previewImage = file.url || URL.createObjectURL(file.raw);
      } else {
        this.previewImage = '';
      }
    },
    // 删除图片
    imageDelete(){
       this.fileList = [];
    },
    SubmitEvent(){
      const token = localStorage.getItem('access_token')
      if (this.previewImage != ''){
        fetch(this.previewImage)
        .then(res => res.blob())
        .then(blob => {
          const formdata = new FormData()
          formdata.append('file',blob,this.previewImage)
          formdata.append('token',token)
          this.Axios({method:'patch',
                      url:'/uploading_profile_photo',
                      data:formdata
                            })
                            .then(ref=>{
                              if (ref.status == 200){
                                if (ref.data.current){
                                  // console.log(ref.data.msg);
                                  
                                  ElMessage.success(ref.data.msg)
                                  this.previewImage=''
                                }else{
                                  ElMessage.error(ref.data.msg)

                                }
                                // console.log(ref.data);
                              }else{
                                ElMessage.error('请求错误')
                                console.log('后端请求错误');
                              }
                              
                            })
                            .catch(error => {
                              ElMessage.error('图片上传失败')
                              console.log('后端访问异常');
                              
                            })
        })
      }
      const formdata = new FormData
      console.log(typeof this.num);
      
      formdata.append('nickname',this.name)
      formdata.append('age',this.num)
      formdata.append('sex',this.value)
      formdata.append('token',token)
      this.Axios({
        method:'patch',
        url:'/user_data_amend',
        data:formdata

      })
      .then(ref=>{
        if (ref.status == 200){
          if (ref.data.current){

            ElMessage.success(ref.data.msg)
            router.push('/personal_center')
            

          }else{
            ElMessage.error(ref.data.msg)
          }
        }else{
           ElMessage.error('请求错误')
           console.log('后端请求错误');
        }
        
      })
    }
  }
}
</script>

<style scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}

.upload-demo {
  margin-bottom: 20px;
}

.preview-container {
  margin-top: 15px;
}

.preview-card {
  width: 150px;
  height: 150px;
  position: relative;
  overflow: hidden;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 新增删除按钮样式 */
.delete-button {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5); /* 半透明黑色背景 */
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0; /* 初始隐藏按钮 */
  transition: opacity 0.3s; /* 添加过渡效果 */
}

/* 鼠标悬停时显示按钮 */
.preview-card:hover .delete-button {
  opacity: 1;
}

/* 调整图标大小 */
.delete-button .el-icon {
  font-size: 24px;
}
.content{
  display: flex;
  align-items: center;      /* 水平方向居中（交叉轴） */
  flex-direction: column;   /* 垂直布局 */
  justify-content: center;
   border: 1px solid #474646;      /* 灰色边框 */
}
.content > *{
   margin-top: 16px; /* 你需要的距离 */
   margin-bottom: 16px;
}

</style>  