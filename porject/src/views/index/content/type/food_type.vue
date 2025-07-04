<template>
    <h4 style="color:deepskyblue;">生鲜食品</h4>
    <div>
        <el-tag v-for="(item,index) in fresh"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
    <h4 style="color:chocolate">加工食品</h4>
    <div>
        <el-tag v-for="(item,index) in processing"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
    <h4>饮品酒水</h4>
    <div>
        <el-tag v-for="(item,index) in beverage"
        :key = 'index'
        :type="item.type">
            {{item.text}}
        </el-tag>
    </div>
    
</template>
<script>
export default {
    name:'FoodType',
    data() {
        return {
            fresh:[
                {type:'success',text:'蔬菜水果：苹果、草莓、西兰花、菠菜等新鲜果蔬。'},
                {type:'info',text:'肉蛋水产：猪肉、牛肉、鸡蛋、活鱼、鲜虾等生鲜食材。'},
                {type:'warning',text:'粮油米面: 大米、面粉、食用油、挂面等主食原料。'},
                {type:'danger',text:'乳制品：牛奶、酸奶、奶酪、黄油等乳制商品'},
            ],
            processing:[
                {type:'warning',text:'休闲零食：薯片、坚果、巧克力、饼干、辣条等。'},
                {type:'primary',text:'方便食品：方便面、自热火锅、速冻水饺、即食粥等'},
                {type:'success',text:'调味品：食用油、酱油、醋、盐、糖等厨房必备调料。'},
                {type:'danger',text:'烘焙食品：面包、蛋糕、饼干、糕点等烘焙美食。'},
            ],
            beverage:[
                {type:'info',text:'饮料：碳酸饮料、果汁、茶饮、矿泉水等各类饮品。'},
                {type:'primary',text:'酒类：啤酒、葡萄酒、白酒、洋酒等各类酒水。'},
                {type:'success',text:'咖啡茶叶：咖啡豆、茶叶、花草茶等饮品原料。'}
            ]
        }
    },
    methods:{}
}
</script>
<style scoped>
div {
    display: flex;
    flex-wrap: wrap; /* 允许标签换行 */
    gap: 20px;
}

</style>