<template>

    <el-container>
      <el-header>
        <app-navigation/>
      </el-header>
      <el-main>
        <el-table :data="tableData" style="width: 100%" >
            <el-table-column prop="save" label="省" />
            <el-table-column prop="city" label="市" />
            <el-table-column prop="county" label="县" />
            <el-table-column prop="detail_address" label="详细地址" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="mobile" label="手机号" />

            <el-table-column prop="id" label="操作">
                <template #default="scope">
                    <el-button type="warning" plain>应用</el-button>
                    <el-button type="info" @click="modify(scope.row.id,scope.row.data_id)" plain>编辑</el-button>
                    <el-button type="danger" @click="delete_fun(scope.row.data_id)" plain>删除</el-button>
                </template>
            </el-table-column>
        </el-table>
        <el-drawer v-model="drawer" title="信息填写" size="50%">
            <el-form :model="form" :rules="rules" ref="addressForm" label-width="80px" style="max-width: 800px; margin: 0 auto;">
                <el-row :gutter="20">
                    <el-col :span="10">
                        <el-form-item label="名称" prop="name">
                            <el-input
                                v-model="form.name"
                                style="width: 100%"
                                type="text"
                                placeholder="请输名称"
                            />
                        </el-form-item>
                    </el-col>
                    <el-col :span="10">
                        <el-form-item label="手机号" prop="mobile">
                            <el-input
                                v-model="form.mobile"
                                style="width: 100%"
                                type="text"
                                placeholder="请输入手机号"
                            />
                        </el-form-item>
                    </el-col>
                </el-row>
                <el-row :gutter="20">
                    <el-col :span="8">
                        <el-form-item label="省" prop="save">
                            <el-select
                                v-model="form.save"
                                placeholder="请选择省"
                                size="large"
                                style="width: 100%"
                            >
                                <el-option
                                    v-for="item in save_list"
                                    :key="item"
                                    :label="item"
                                    :value="item"
                                />
                            </el-select>
                        </el-form-item>
                    </el-col>
                    <el-col :span="8">
                        <el-form-item label="市" prop="city">
                            <el-select
                                v-model="form.city"
                                placeholder="请选择市"
                                size="large"
                                style="width: 100%"
                            >
                                <el-option
                                    v-for="item in city_list"
                                    :key="item"
                                    :label="item"
                                    :value="item"
                                />
                            </el-select>
                        </el-form-item>
                    </el-col>
                    <el-col :span="8">
                        <el-form-item label="县" prop="county">
                            <el-select
                                v-model="form.county"
                                placeholder="请选择县"
                                size="large"
                                style="width: 100%"
                            >
                                <el-option
                                    v-for="item in county_list"
                                    :key="item"
                                    :label="item"
                                    :value="item"
                                />
                            </el-select>
                        </el-form-item>
                    </el-col>
                </el-row>
                <el-form-item label="详细地址" prop="detail_address">
                    <el-input
                        v-model="form.detail_address"
                        style="width: 100%"
                        :autosize="{ minRows: 3, maxRows: 5}"
                        type="textarea"
                        placeholder="请输入详细地址"
                    />
                </el-form-item>
                <el-form-item style="text-align: right; margin-top: 20px;">
                    <el-button @click="drawer = false" style="margin-right: 10px;">取消</el-button>
                    <el-button type="primary" @click="commit">保存</el-button>
                </el-form-item>
            </el-form>
        </el-drawer>
      </el-main>
      <el-button type="primary" @click="add_addre">添加地址</el-button>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>

</template>
<script setup lang="ts">
import {ref,reactive,onMounted,watch} from 'vue'
import axios from 'axios';
import router from '@/router'
import AppNavigation from '@/moon/navigation.vue'
import { ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElRow, ElCol, ElButton, ElMessage } from 'element-plus'

const form = reactive({
    'id':null,
    'name':'',
    'mobile':'',
    'save':'',
    'city':'',
    'county':'',
    'detail_address':'',
    'data_id':null
})

const tableData:any = ref<any[]>([]) 

const rules = reactive({
    name: [
        { required: true, message: '名称', trigger: 'blur' }
    ],
    mobile: [
        { required: true, message: '请输入手机号', trigger: 'blur' },
        { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号', trigger: 'blur' }
    ],
    save: [
        { required: true, message: '请选择省份', trigger: 'change' }
    ],
    city: [
        { required: true, message: '请选择城市', trigger: 'change' }
    ],
    county: [
        { required: true, message: '请选择县区', trigger: 'change' }
    ],
    detail_address: [
        { required: true, message: '请输入详细地址', trigger: 'blur' },
        { min: 5, message: '地址长度不能少于5个字符', trigger: 'blur' }
    ]
})

const addressForm = ref<InstanceType<typeof ElForm> | null>(null)

const Axios = axios.create({
    baseURL:'http://127.0.0.1:8000/api'
})
// 抽屉开关
const drawer = ref(false)

const add_addre = ref(()=>{
    drawer.value = true
})
defineOptions({
    name:'AddreSet',
    components:{
        AppNavigation
    }
    })
const save_list = ref<string[]>([])
const city_list = ref<string[]>([])
const county_list = ref<string[]>([])


const get_address = ref()

async function fetchData(){
    tableData.value = []

    await Axios.get('/get_address_options')
    .then(res =>{
        if (res.status == 200){
            save_list.value = res.data.save_list
            city_list.value = res.data.city_list
            county_list.value = res.data.county_list
        }
    })
    const fromdata = new FormData()
    fromdata.append('token',localStorage.getItem('access_token')||'')
    await Axios.post('/get_address',fromdata)
    .then(res=>{
        if (res.status == 200){
            if (res.data.current){
                console.log(Object.keys(res.data.save_list).length);
                
                for (let i =0; i<Object.keys(res.data.save_list).length; i++){
                    tableData.value.push({

                        'save':res.data.save_list[i][4],
                        'city':res.data.save_list[i][5],
                        'county':res.data.save_list[i][6],
                        'detail_address':res.data.save_list[i][7],
                        'name':res.data.save_list[i][2],
                        'mobile':res.data.save_list[i][3],
                        'id':res.data.save_list[i][0],
                        'data_id':res.data.save_list[i][1]
                })

                
                console.log(tableData);
                
            }
        }
    }})

}


onMounted(async()=>{
    await fetchData()
})

// 省份选择框
watch(()=>form.save,(newVal,oldVal)=>{
    if (newVal != oldVal){
        if(newVal !=''){
            Axios.get('/get_address_options?save='+newVal)
            .then(res=>{
                if (res.status == 200){
                    city_list.value = Object.values(res.data.city_list)
                    county_list.value = Object.values(res.data.county_list)
                    if(!city_list.value.includes(form.city)){
                        form.city = ''
                        form.county = ''
                    }
                }
            })
        }
    }
})

// 城市选择框
watch(()=>form.city,(newVal,oldVal)=>{

    if (newVal != oldVal && newVal != ''){
        console.log(newVal);
        console.log(oldVal);
        
        console.log(newVal != oldVal);
        
        Axios.get('/get_address_options?city='+newVal)
        .then(res=>{
            if (res.status == 200){
                county_list.value = Object.values(res.data.county_list)
                if(!county_list.value.includes(form.county)){
                    form.county = ''
                }
            }
        })

    }
})

watch(()=>drawer.value,(newVal,oldVal)=>{
    if (newVal == false){
        form.save = ''
        form.city = ''
        form.county = ''
        form.detail_address = ''
        form.name = ''
        form.mobile = ''
        console.log();
        console.log(addressForm.value);
    }
    if (addressForm.value) {
            addressForm.value.clearValidate()
        }
})

// 修改按钮功能
const modify = ref(async(order: number,id: number)=>{
    console.log(order,id);

    
    const data = tableData.value[order-1];
    form.save = data.save
    form.id = data.id
    form.data_id = data.data_id
    form.city= data.city
    form.county= data.county
    form.detail_address= data.detail_address
    form.name= data.name
    form.mobile= data.mobile
    drawer.value = true
})

// 提交按钮功能
const commit = ref(async ()=>{
    const token = localStorage.getItem('access_token')||''
    if (form.data_id == null){
        // 添加逻辑
        const address_formdata = new FormData()
        if (token =='' && form.save=='' && form.city=='' && form.county=='' && form.detail_address=='' && form.name=='' && form.mobile==''){
            ElMessage.error('请填写完整信息')
            return
        }else{
        address_formdata.append('token',token)
        address_formdata.append('save',form.save)
        address_formdata.append('city',form.city)
        address_formdata.append('county',form.county)
        address_formdata.append('address',form.detail_address)
        address_formdata.append('name',form.name)
        address_formdata.append('phone',form.mobile)
        await Axios.post('/add_address',address_formdata,{headers: {
            'Content-Type': 'multipart/form-data'
        }})
        .then(async res =>{
            if (res.status == 200){
                if (res.data.current){
                    ElMessage.success('添加成功')
                    await fetchData()
                    form.save = ''
                    form.city = ''
                    form.county = ''
                    form.detail_address = ''
                    form.name = ''
                    form.mobile = ''
                    drawer.value = false
                }
                else{
                    ElMessage.error(res.data.msg)
                    form.save = ''
                    form.city = ''
                    form.county = ''
                    form.detail_address = ''
                    form.name = ''
                    form.mobile = ''
                }
            }
    })}
    }else{
        // 修改逻辑
        const fromdata = new FormData()
        fromdata.append('token',localStorage.getItem('access_token')||'')
        fromdata.append('id',form.data_id)
        fromdata.append('save',form.save)
        fromdata.append('city',form.city)
        fromdata.append('county',form.county)
        fromdata.append('address',form.detail_address)
        fromdata.append('name',form.name)
        fromdata.append('phone',form.mobile)
        await Axios.patch('/modify_address',fromdata)
        .then(async res=>{
            if (res.status == 200){
                if (res.data.current){
                    ElMessage.success('修改成功')
                    await fetchData()
                    form.save = ''
                    form.city = ''
                    form.county = ''
                    form.detail_address = ''
                    form.name = ''
                    form.mobile = ''
                    drawer.value = false
                }else{
                    ElMessage.error(res.data.msg)
                    form.save = ''
                    form.city = ''
                    form.county = ''
                    form.detail_address = ''
                    form.name = ''
                    form.mobile = ''
                }
            }
        })
    }
})

// 删除按钮功能
const delete_fun = ref(async (id: number)=>{
    const fromdata = new FormData()
    console.log(id.toString());
    
    fromdata.append('id',id.toString())
    fromdata.append('token',localStorage.getItem('access_token')||'')
    await Axios.delete('/delete_address', {
        data: fromdata
    })
    .then(res=>{
        if (res.status == 200){
            if (res.data.current){
                ElMessage.success('删除成功')
                fetchData()
            }else{
                ElMessage.error('删除失败')
                fetchData()
            }
        }
    })

})

</script>
<style scoped>
    .footer-content {
    text-align: center;
    color: darkgray;
    }
</style>