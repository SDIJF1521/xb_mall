<template>
    <el-container>
        <el-header>
            <div class="management-navigation">
                <h2 class="title_night">小白的商城-店铺创建页</h2>
            </div>
        </el-header>

        <el-main>
            <el-dialog
                v-model="dialogVisible"
                title="店铺创建"
                width="500"
                :before-close="handleClose"
            >
                <span>{{dialog_content}}</span>
                <template #footer>
                <div class="dialog-footer">
                    <el-button @click="dialogVisible = false">取消</el-button>
                    <el-button type="primary" @click= "handleOk">
                    确认
                    </el-button>
                </div>
                </template>
            </el-dialog>
            <el-row :gutter="20">
                <el-col :span="5"><div class="grid-content ep-bg-purple" /></el-col>
                 <el-col :span="15">
                    <el-form :model="mall_info" label-width="auto" class="el-info" :rules="rules" ref="ruleFormRef">
                        <h2 class="title_daytime">店铺创建</h2>
                        <el-form-item label="" prop="mall_name">
                            <el-input v-model="mall_info.mall_name" placeholder="店铺名称" />
                        </el-form-item>

                        <el-form-item label="" prop="mall_address">
                            <el-input v-model="mall_info.mall_address" placeholder="店铺地址" />
                        </el-form-item>

                        <div class="from-div">
                            <el-form-item label="" style="width: 100%;" prop="mall_phone">
                                <el-input v-model="mall_info.mall_phone" style="width: 100%;" placeholder="店铺联系电话" />
                            </el-form-item>

                            <el-form-item label="" style="width: 100%;" prop="mall_admin">
                                <el-select style="width: 100%;" v-model="mall_info.mall_admin">
                                    <el-option v-for="item in optiins" :label="item.label" :value="item.value"/>
                                </el-select>
                            </el-form-item>
                        </div>
                        <el-form-item>
                            <el-upload
                               v-model:file-list="mall_info.mall_img"
                                :auto-upload = "false"
                                :limit="1"
                                class="upload-demo"
                                list-type="picture"
                            >
                                <el-button type="primary">Click to upload mall of img</el-button>
                            </el-upload>
                        </el-form-item>
                        <el-form-item label="" prop="mall_description">
                              <el-input
                                    v-model="mall_info.mall_description"
                                    maxlength="200"
                                    placeholder="店铺描述"
                                    :autosize="{ minRows: 2, maxRows: 5 }"
                                    show-word-limit
                                    type="textarea"
                                />
                        </el-form-item>

                        <el-button type="primary" style="width: 100%;" @click="submitForm(ruleFormRef)" plain>提交</el-button>
                    </el-form>
                </el-col>
                <el-col :span="7"><div class="grid-content ep-bg-purple" /></el-col>
            </el-row>
        </el-main>
        <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script lang="ts" setup>
import axios from 'axios';
import { onMounted, reactive, ref } from 'vue';
import type { UploadProps, UploadUserFile } from 'element-plus'
import { ElMessage, ElStep } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

// 定义表单数据类型
interface RuleForm {
    mall_name: string;
    mall_address: string;
    mall_phone: string;
    mall_description: string;
    mall_admin: string;
    mall_img: UploadUserFile[];
}

// 定义组件名称
defineOptions({
    name: 'BuyerSideAddMall',
})
// 定义弹窗状态
const dialogVisible = ref(false)
// 定义表单引用
const ruleFormRef = ref<FormInstance>()
// 定义表单数据
const mall_info = ref<RuleForm>({
    mall_name: '',
    mall_address: '',
    mall_phone: '',
    mall_description: '',
    mall_admin: '',
    mall_img: [],
})

// 数据校验规则
const rules = reactive<FormRules<RuleForm>>({
    mall_name: [
        { required: true, message: '请输入店铺名称', trigger: 'blur' },
        { min: 2, max: 30, message: '长度在 2 到 30 个字符', trigger: 'blur' }
    ],
    mall_address: [
        { required: true, message: '请输入店铺地址', trigger: 'blur' },
        { min: 5, max: 50, message: '长度在 5 到 50 个字符', trigger: 'blur' }
    ],
    mall_phone: [
        { required: true, message: '请输入联系电话', trigger: 'blur' },
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
    ],
    mall_description: [
        { required: true, message: '请输入店铺描述', trigger: 'blur' },
        { min: 20, max: 100, message: '长度在 20 到 200 个字符', trigger: 'blur' }
    ],
    mall_admin: [
        { required: true, message: '请选择店铺管理员', trigger: 'change' },
        {min: 1, max: 30, message: '长度在 2 到 30 个字符', trigger: 'blur' }

    ],
    mall_img: [
        { required: true, message: '请上传店铺图片', trigger: 'change' },
        { type: 'array', min: 1, max: 1, message: '只能上传一张图片', trigger: 'change' }
    ]

})

// 下拉选项
const optiins = [{
    label: '默认',
    value: '小白',
}]

// 弹窗内容
const dialog_content = ref("确认创建店铺吗？")

// 关闭弹窗
const handleClose = (done: () => void) => {
    done();
};

onMounted(()=>{
    document.documentElement.classList.add('dark')
})

// 定义后端API地址
const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
    timeout: 5000,
});

//提交按钮点击事件
async function submitForm(formEl: FormInstance | undefined){
    if (!formEl) return
    await formEl.validate((valid, fields) => {
        if (valid) {
            // 初始化 FormData 对象，买家端重复店铺检测路由表单数据
            console.log(mall_info.value);
            if (mall_info.value.mall_img.length === 0){
                ElMessage.error("请上传店铺图片")
                return
            }
            const formdata = new FormData();
            formdata.append('token',localStorage.getItem('buyer_access_token') || '')
            formdata.append('mall_name',mall_info.value.mall_name)
            formdata.append("user",mall_info.value.mall_admin)
            formdata.append('mall_site',mall_info.value.mall_address)
            formdata.append('mall_phone',mall_info.value.mall_phone)
            formdata.append('info',mall_info.value.mall_description)
            Axios.post("/buyer_repeat_show",formdata)
            .then(async (res) => {
                if (res.data.code === 200){
                    if(res.data.current){
                        dialog_content.value = "该店铺已存在，是否继续创建？"
                    }
                    dialogVisible.value = true
                }else{
                    ElMessage.error(res.data.msg)
                }
            })
        } else {
        console.log('error submit!', fields)
        }
  })

}


// 弹出窗确认按钮
async function handleOk() {
    // 初始化 FormData 对象，买家端创建店铺路由表单数据
    const mall_info_commit = new FormData();
    mall_info_commit.append('token',localStorage.getItem('buyer_access_token') || '')
    mall_info_commit.append('mall_name',mall_info.value.mall_name)
    mall_info_commit.append("user",mall_info.value.mall_admin)
    mall_info_commit.append('mall_site',mall_info.value.mall_address)
    mall_info_commit.append('mall_phone',mall_info.value.mall_phone)
    mall_info_commit.append('info',mall_info.value.mall_description)
    Axios.post("/add_mall",mall_info_commit)
    .then(res =>{
        if (res.data.code === 200 && res.data.current){
            // 初始化FormData 对象，店铺图片数据
            const mall_img = new FormData();
            mall_img.append('token',localStorage.getItem('buyer_access_token') || '')
            mall_img.append('id',res.data.prod_id)
            console.log(mall_info.value.mall_img);

            mall_img.append('mall_img',mall_info.value.mall_img[0]["raw"]||'')
            Axios.post("/mall_img_upload",mall_img)
            .then(res =>{
                if (res.data.current){
                    mall_info.value.mall_name = "";
                    mall_info.value.mall_address = "";
                    mall_info.value.mall_phone = "";
                    mall_info.value.mall_description = "";
                    mall_info.value.mall_admin = "";
                    mall_info.value.mall_img = [];
                    ElMessage.success("店铺创建成功")

                    return
                }else if(res.data.code == 403 && res.data.code == 500){
                    ElMessage.warning("店铺创建成功，但店铺图片上传失败")
                }else{
                    ElMessage.warning("店铺创建成功，但店铺图片上传失败")
                }
            })

        }else{
            ElMessage.error(res.data.msg)
        }
    })
    dialogVisible.value = false


}
</script>

<style scoped>

.footer-content {
    text-align: center;
    color: darkgray;
    }

.management-navigation {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0 20px;
}
.title_night{
    background: linear-gradient(to right, #46e2cb, #742bd9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    color: transparent;
}
.title_daytime{
    color: #000;
}
.from-div{
    display: flex;
}
.el-header {
    border-bottom: 1px solid #575859;
    padding-bottom: 10px;
    margin-bottom: 10px;
}
.el-info {
    border-style:solid;
    border-width: 1px;
    border-color: #605d6b;
    padding: 10px;
    width: 70%;
    margin: 0 auto;
    border-radius: 10px;

}
.title_daytime{
    font-size: 20px;
    font-weight: 600;
    color: #4fe2cc;
}
</style>
