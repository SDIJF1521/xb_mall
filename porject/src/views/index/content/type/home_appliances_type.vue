<template>
    <h4 style="color: cadetblue">厨房家电</h4>
    <div class="tag-group">
      <el-tag 
        v-for="(item, index) in kitchenAppliances" 
        :key="index" 
        :type="item.type"
      >
        {{ item.text }}
      </el-tag>
    </div>
    
    <h4 style="color: burlywood">生活家电</h4>
    <div>
      <el-tag v-for="(item,index) in homeAppliance"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
    
    <h4>客厅与卧室家电</h4>
    <div>
      <el-tag v-for="(item,index) in bedroomAppliances"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
</template>

<script>
export default {
  name: 'HomeAppliancesType',
  data() {
    return {
      // 优化厨房家电数据结构，包含类型和文本
      kitchenAppliances: [
        { type: 'warning', text: '烹饪电器：电饭煲、电压力锅、微波炉、空气炸锅、电烤箱、蒸烤箱、电饼铛、电磁炉' },
        { type: 'success', text: '厨房大电：油烟机、燃气灶、消毒柜、集成灶、洗碗机、垃圾处理器' },
        { type: 'danger', text: '食材处理：榨汁机、破壁机、厨师机、绞肉机、切菜器、打蛋器' },
        { type: 'info', text: '制冷保鲜：冰箱、冰柜、红酒柜、制冰机、酸奶机' },
        { type: 'primary', text: '厨房小电：电水壶、咖啡机、面包机、煮蛋器、电炖锅、养生壶' }
      ],
      homeAppliance:[
        {type:'success',text:'清洁电器：吸尘器、扫地机器人、蒸汽拖把、洗地机、空气净化器' },
        { type: 'warning', text: '洗护电器：洗衣机、干衣机、熨烫机、挂烫机、洗鞋机' },
        { type: 'danger', text: '健康电器：电热毯、电暖器、电风扇、加湿器、除湿机' },
        { type: 'info', text: '按摩护理：按摩椅、足浴盆、筋膜枪、按摩披肩、颈椎按摩器、眼部按摩仪' }
      ],
      bedroomAppliances:[
        {type:'warning',text:'影音娱乐：电视机、投影仪、音响、家庭影院、游戏机主机、K歌设备'},
        {type:'success',text:'智能设备：智能音箱、智能灯具、智能窗帘、智能门锁、智能家居中控'},
        {type:'info',text:'其他设备：饮水机、电暖桌、电蚊拍、灭蝇灯、空气循环扇'}
      ]

    }
  },
  methods: {}
}
</script>

<style scoped>
div {
    display: flex;
    flex-wrap: wrap; /* 允许标签换行 */
    gap: 20px;
}


</style>