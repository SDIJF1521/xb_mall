<template>
  <el-collapse v-model="activeNames" @change="handleChange">
    <el-collapse-item title="" name="1">
      <el-container>
        <!-- 侧边导航栏 -->
        <el-aside width="200px">
          <el-menu
            default-active="2"
            class="el-menu-vertical-demo"
            @select="handleSelect"
          >
            <el-menu-item-group title="分类">
              <el-menu-item 
                index="食品" 
                @mouseenter="handleMouseEnter('食品')"
                @mouseleave="handleMouseLeave"
              >食品</el-menu-item>
              <el-menu-item 
                index="家电" 
                @mouseenter="handleMouseEnter('家电')"
                @mouseleave="handleMouseLeave"
              >家电</el-menu-item>
              <el-menu-item 
                index="数码" 
                @mouseenter="handleMouseEnter('数码')"
                @mouseleave="handleMouseLeave"
              >数码</el-menu-item>
              <el-menu-item 
                index="服饰" 
                @mouseenter="handleMouseEnter('服饰')"
                @mouseleave="handleMouseLeave"
              >服饰</el-menu-item>
            </el-menu-item-group>
          </el-menu>
        </el-aside>
        <el-container>
          <el-main>
            <div>
              <!-- 使用 v-if 替代硬编码的组件名 -->
              <el-empty v-if="selectedType == '' && hoverType ==''" description="请选择一个分类" />
              <component :is="currentComponent" />
            </div>
          </el-main>
        </el-container>
      </el-container>
    </el-collapse-item>
     <el-main>
      <component :is="mods"></component>
     </el-main>
  </el-collapse>
</template>

<script>
// 修正导入路径
import FoodType from './type/food_type.vue'
import HomeAppliancesType from './type/home_appliances_type.vue'
import DigitalProductsType from './type/digital_products_type.vue'
import DressType from './type/dress_type.vue'
import NallPage from './nall_page.vue'
import IndexGoods from './index_goods.vue'

export default {
  name: 'IndexMain',
  components: {
    FoodType,
    HomeAppliancesType,
    DigitalProductsType,
    DressType,
    NallPage,
    IndexGoods
  },
  data() {
    return {
      activeNames: ['1'], // 手风琴激活项
      selectedType: '',   // 选中的菜单分类
      hoverType: '',       // 鼠标悬停的分类
      mods:'NallPage'
    };
  },
  computed: {
    // 使用计算属性确定当前显示的组件
    currentComponent() {
      if (this.hoverType === '食品') {
        return FoodType;
      }else if (this.hoverType === '家电') {
        return HomeAppliancesType
      }else if (this.hoverType === '数码') {
        return DigitalProductsType;
      }else if (this.hoverType === '服饰') {
        return DressType;
      }
      if (this.hoverType ==='' && this.selectedType === '食品') {
        return FoodType;
      }else if (this.hoverType ==='' && this.selectedType === '家电') {
        return HomeAppliancesType;
      }else if (this.hoverType ==='' && this.selectedType === '数码') {
        return DigitalProductsType;
      }else if (this.hoverType ==='' && this.selectedType === '服饰') {
        return DressType
      }
      // 可以为其他分类添加更多组件
      return null;
    }
  },
  methods: {
    handleChange(activeNames) {
      console.log('手风琴激活项变更:', activeNames);
      this.activeNames = activeNames;
    },
    handleSelect(key, keyPath) {
      this.selectedType = key;
      console.log('菜单选中项:', key, keyPath);
    },
    // 鼠标进入菜单项事件
    handleMouseEnter(type) {
      this.hoverType = type;
      console.log('鼠标悬停在:', this.hoverType);
    },
    // 鼠标离开菜单项事件
    handleMouseLeave() {
      this.hoverType = '';
      console.log('鼠标已离开菜单项');
    },
    //留存用于后续对接后端
  }
}
</script>

<style scoped>
.el-menu-vertical-demo {
  border-right: none;
}
.mall {
  flex-wrap: wrap; /* 允许标签换行 */
}
</style>