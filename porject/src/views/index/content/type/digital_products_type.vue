<template>
    <h4 style="color: lightcoral;">手机通讯</h4>
    <div>
         <el-tag v-for="(item,index) in pe"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
    <h4 style="color:dodgerblue;">电脑办公</h4>
    <div>
        <el-tag v-for="(item,index) in pc"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
    <h4 style="color: cadetblue;">影像设备</h4>
    <div>
        <el-tag v-for="(item,index) in image"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
        <h4 style="color: brown;">存储与网络</h4>
    <div>
        <el-tag v-for="(item,index) in storage"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
        <h4>游戏设备</h4>
    <div>
        <el-tag v-for="(item,index) in game"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
        <h4 style="color: cornflowerblue;">音频设备</h4>
    <div>
        <el-tag v-for="(item,index) in audio"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
</template>
<script>
export default {
    name: 'CigitalProductsType',
    data() {
        return{
            pe:[
                {type: 'primary',text:'智能手机： 5G 手机、折叠屏手机、拍照手机（长焦 / 夜景）、游戏手机（高刷屏 / 散热）、千元机 / 旗舰机'},
                {type:'info',text:'手机配件： 手机壳、钢化膜、无线充电器、充电宝、数据线、手机支架'},
                {type:'danger',text:'通讯设备： 对讲机、随身 WiFi、手机信号放大器'}
            ],
            pc:[
                {type:'info',text:'笔记本电脑： 轻薄本、游戏本（RTX 显卡）、商务本（长续航）、设计师本（高色域）'},
                {type:'warning',text:'台式电脑： 组装主机、品牌整机、迷你主机、工作站'},
                {type:'danger',text:'电脑配件： 显卡、CPU、内存条、固态硬盘、机箱、电源'},
                {type:'primary',text:'办公设备： 打印机（喷墨 / 激光）、扫描仪、投影仪、数位板、手写笔'}
            ],
            image:[
                 {type:'success',text:'数码相机： 单反相机（佳能 / 尼康）、微单相机（索尼 / 富士）、卡片机'},
                 {type:'warning',text:'摄影配件： 镜头（广角 / 长焦）、三脚架、滤镜、摄影包、闪光灯'}
            ],
            storage:[
                {type:'danger',text:'存储设备： 移动硬盘（SSD/HDD）、U 盘（高速 / 加密）、SD 卡（相机专用）、NAS 网络存储'},
                {type:'primary',text:'网络设备： 无线路由器（Wi-Fi 6）、交换机、网线、随身 WiFi、网络机顶盒'},
                {type:'info',text:'配件： 扩展坞、集线器、网线转接器'}
            ],
            game:[
                {type:'primary',text:'游戏主机： PS5、Xbox Series X、Switch、Steam Deck'},
                {type:'info',text:'电竞配件： 游戏手柄、机械键盘（青轴 / 红轴）、电竞鼠标（轻量化）、电竞椅'},
                {type:'success',text:'VR/AR 设备： VR 一体机（Oculus Quest）、AR 眼镜、动作捕捉设备'},
            ],
            audio:[
                {type:'primary',text:'耳机耳塞： TWS 无线耳机（AirPods / 国产降噪）、头戴式耳机（HiFi / 电竞）、入耳式监听耳机'},
                {type:'success',text:'音箱设备： 蓝牙音箱（便携 / 户外）、家用音响（2.1 声道）、智能音箱（语音助手）'},
                {type:'info',text:'配件： 耳机转接头、音频线、耳麦（游戏 / 直播）'}
            ]

        }
    }
}
</script>
<style scoped>
div {
    display: flex;
    flex-wrap: wrap; /* 允许标签换行 */
    gap: 20px;
}

</style>

