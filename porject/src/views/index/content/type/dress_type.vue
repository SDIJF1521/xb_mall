<template>
    <h4 style="color: burlywood;">核心标签</h4>
    <div>
         <el-tag v-for="(item,index) in category"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
    <h4 style="color: cadetblue;">消费偏好</h4>
    <div>
         <el-tag v-for="(item,index) in preference"
        :key = 'index'
        :type="item.type">
            {{item.text}}
    </el-tag>
    </div>
    <h4>使用场景</h4>
    <div>
         <el-tag v-for="(item,index) in scene"
        :key = 'index'
        :type="item.type">
            {{item.text}}
    </el-tag>
    </div>
</template>
<script>
export default {
    name:'DressType',
    data() {
        return {
            category:[
                {type:'primary',text:'男装： 衬衫、T 恤、西装、夹克、牛仔裤、休闲裤、卫衣、羽绒服、皮衣、运动套装'},
                {type:'danger',text:'女装： 连衣裙、短裙、牛仔裤、外套、针织衫、衬衫、卫衣、风衣、旗袍、泳衣'},
                {type:'warning',text:'童装： 婴儿服、儿童套装、童装外套、童鞋、书包、儿童配饰'},
                {type:'info',text:'鞋靴： 运动鞋、皮鞋、马丁靴、高跟鞋、凉鞋、拖鞋、靴子、帆布鞋'},
                {type:'success',text:'箱包： 背包、手提包、钱包、行李箱、挎包、公文包、运动包'}
            ],
            preference:[
                {type:'warning',text:'休闲风格： 卫衣、牛仔裤、帆布鞋、棒球帽、运动套装'},
                {type:'info',text:'职场风格： 西装、衬衫、高跟鞋、公文包、职业连衣裙'},
                {type:'danger',text:'潮流风格： 潮牌 T 恤、破洞牛仔裤、老爹鞋、街头风外套'},
                {type:'warning',text:'复古风格： 复古连衣裙、喇叭裤、格纹衬衫、马丁靴'},
                {type:'primary',text:'运动风格： 运动套装、跑步鞋、健身服、瑜伽裤、运动背包'},
                {type:'success',text:'优雅风格： 旗袍、高跟鞋、真丝衬衫、连衣裙、珍珠配饰'}
            ],
            scene:[
                {type:'info',text:'通勤场景： 西装、衬衫、职业裙、皮鞋、公文包'},
                {type:'success',text:'运动场景： 运动套装、跑步鞋、健身服、瑜伽裤、运动背包'},
                {type:'warning',text:'休闲场景： T 恤、牛仔裤、帆布鞋、棒球帽、双肩包'},
                {type:"danger",text:'宴会场景： 晚礼服、高跟鞋、礼服包、珠宝配饰'},
                {type:'success',text:'户外场景： 冲锋衣、登山鞋、户外背包、防晒衣、运动水壶'},
                {type:'primary',text:'家居场景： 家居服、拖鞋、睡衣、浴袍、家居拖鞋'}
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