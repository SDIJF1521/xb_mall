<template>
    <el-container>
        <el-header>
            <div class="management-navigation">
                <h2 class="title_night">小白的商城-店铺创建页</h2>
            </div>
        </el-header>

        <el-main>
            <el-row :gutter="20">
                <el-col :span="5"><div class="grid-content ep-bg-purple" /></el-col>
                 <el-col :span="15">
                    <el-form :model="mall_info" label-width="auto" class="el-info">
                        <h2 class="title_daytime">店铺创建</h2>
                        <el-form-item label="">
                            <el-input v-model="mall_info.mall_name" placeholder="店铺名称" />
                        </el-form-item>

                        <el-form-item label="">
                            <el-input v-model="mall_info.mall_address" placeholder="店铺地址" />
                        </el-form-item>

                        <div class="from-div">
                            <el-form-item label="" style="width: 100%;">
                                <el-input v-model="mall_info.mall_phone" style="width: 100%;" placeholder="店铺联系电话" />
                            </el-form-item>
                            
                            <el-form-item label="" style="width: 100%;">
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
                        <el-form-item label="">
                            <el-input v-model="mall_info.mall_description" placeholder="店铺描述" />
                        </el-form-item>
                        
                        <el-button type="primary" style="width: 100%;" @click="submitForm" plain>提交</el-button>
                    </el-form>
                </el-col>
                <el-col :span="7"><div class="grid-content ep-bg-purple" /></el-col>
            </el-row>
        </el-main>
        <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import type { UploadProps, UploadUserFile } from 'element-plus'

const mall_info = ref({
    mall_name: '',
    mall_address: '',
    mall_phone: '',
    mall_description: '',
    mall_admin: '',
    mall_img: [],
    
})


const optiins = [{
    label: '默认',
    value: '小白',
}]

// 定义组件名称
defineOptions({
    name: 'BuyerSideAddMall',
})
onMounted(()=>{
    document.documentElement.classList.add('dark')
})

//提交
function submitForm(){
    console.log(mall_info.value.mall_img)
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