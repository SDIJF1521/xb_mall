<template>
  <div class="session-list">
    <!-- 搜索框 -->
    <div class="sl-search">
      <el-input
        v-model="keyword"
        placeholder="搜索用户..."
        size="small"
        clearable
        :prefix-icon="Search"
      />
    </div>

    <!-- 加载状态 -->
    <div v-if="props.loading" class="sl-loading">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="filteredSessions.length === 0" class="sl-empty">
      <el-icon :size="36"><ChatDotSquare /></el-icon>
      <p>{{ props.sessions.length === 0 ? '暂无用户咨询' : '没有找到相关用户' }}</p>
    </div>

    <!-- 会话列表 -->
    <div v-else class="sl-items">
      <div
        v-for="session in filteredSessions"
        :key="session.session_id"
        class="sl-item"
        :class="{
          'sl-item--active': props.activeSessionId === session.session_id,
          'sl-item--online': session.online,
        }"
        @click="emit('select', session.session_id)"
      >
        <div class="si-avatar">
          <span>{{ session.session_id.slice(0, 1).toUpperCase() }}</span>
          <span class="si-status" :class="session.online ? 'online' : 'offline'" />
        </div>
        <div class="si-content">
          <div class="si-top">
            <span class="si-name">{{ session.session_id }}</span>
            <span class="si-time">{{ session.last_time }}</span>
          </div>
          <div class="si-last">{{ session.last_message || '暂无消息' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, ChatDotSquare } from '@element-plus/icons-vue'

export interface Session {
  session_id: string
  online: boolean
  last_message: string
  last_time: string
}

const props = defineProps<{
  sessions: Session[]
  activeSessionId: string
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'select', sessionId: string): void
}>()

const keyword = ref('')

const filteredSessions = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return props.sessions
  return props.sessions.filter(s => s.session_id.toLowerCase().includes(kw))
})
</script>

<style scoped lang="scss">
.session-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.sl-search {
  padding: 12px 12px 8px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--el-border-color-light);
}

.sl-loading {
  padding: 12px;
}

.sl-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 16px;
  color: var(--el-text-color-placeholder);
  font-size: 13px;

  p { margin: 0; }
}

.sl-items {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb {
    background: var(--el-border-color);
    border-radius: 4px;
  }
}

.sl-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.18s;

  &:hover { background: var(--el-fill-color-light); }

  &--active {
    background: rgba(102, 126, 234, 0.1);
    border-right: 3px solid #667eea;
  }
}

.si-avatar {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.si-status {
  position: absolute;
  bottom: 1px;
  right: 1px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--el-bg-color);

  &.online  { background: #67c23a; }
  &.offline { background: #bbb; }
}

.si-content {
  flex: 1;
  min-width: 0;
}

.si-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 3px;
}

.si-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  .sl-item--online & { color: #409eff; }
}

.si-time {
  font-size: 10px;
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
  margin-left: 6px;
}

.si-last {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
