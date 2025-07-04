<template>
  <div class="verify-code-container">
    <canvas 
      ref="verifyCanvas"
      width="120"
      height="40"
      class="verify-code-image"
      @click="refreshVerifyCode"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, defineProps, defineEmits } from 'vue';

const props = defineProps<{
  // 可以添加需要的props
}>();

const emit = defineEmits<{
  (e: 'update:verifyCode', value: string): void;
}>();

const verifyCanvas = ref<HTMLCanvasElement>();
const verifyCodeText = ref('');

const generateVerifyCode = (length = 4) => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz0123456789';
  let code = '';
  for (let i = 0; i < length; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
};

const drawVerifyCode = () => {
  if (!verifyCanvas.value) return;
  const ctx = verifyCanvas.value.getContext('2d');
  if (!ctx) return;

  // 清空画布
  ctx.clearRect(0, 0, verifyCanvas.value.width, verifyCanvas.value.height);

  // 生成验证码文本
  verifyCodeText.value = generateVerifyCode();
  emit('update:verifyCode', verifyCodeText.value);

  // 设置背景
  ctx.fillStyle = '#f5f5f5';
  ctx.fillRect(0, 0, verifyCanvas.value.width, verifyCanvas.value.height);

  // 绘制文本
  ctx.font = 'bold 20px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  // 随机文本颜色
  const textColors = ['#333', '#666', '#999'];
  ctx.fillStyle = textColors[Math.floor(Math.random() * textColors.length)];

  // 绘制每个字符，位置随机微调
  verifyCodeText.value.split('').forEach((char, index) => {
    const x = 20 + index * 25 + Math.random() * 10 - 5;
    const y = 20 + Math.random() * 10 - 5;
    const rotation = (Math.random() - 0.5) * 0.4;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rotation);
    ctx.fillText(char, 0, 0);
    ctx.restore();
  });

  // 绘制干扰线
  for (let i = 0; i < 4; i++) {
    ctx.beginPath();
    ctx.moveTo(Math.random() * verifyCanvas.value.width, Math.random() * verifyCanvas.value.height);
    ctx.lineTo(Math.random() * verifyCanvas.value.width, Math.random() * verifyCanvas.value.height);
    ctx.strokeStyle = `rgb(${Math.random() * 100 + 100}, ${Math.random() * 100 + 100}, ${Math.random() * 100 + 100})`;
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  // 绘制噪点
  for (let i = 0; i < 50; i++) {
    ctx.beginPath();
    ctx.arc(
      Math.random() * verifyCanvas.value.width,
      Math.random() * verifyCanvas.value.height,
      1,
      0,
      2 * Math.PI
    );
    ctx.fillStyle = `rgb(${Math.random() * 200}, ${Math.random() * 200}, ${Math.random() * 200})`;
    ctx.fill();
  }
};

const refreshVerifyCode = () => {
  drawVerifyCode();
};

onMounted(() => {
  drawVerifyCode();
});

// 暴露刷新方法给父组件
defineExpose({
  refreshVerifyCode
});
</script>

<style scoped>
.verify-code-container {
  display: inline-block;
}

.verify-code-image {
  height: 40px;
  cursor: pointer;
  vertical-align: middle;
}
</style>