<template>
  <div class="group-chat-view">
    <GroupChatComponent />
  </div>
</template>

<script setup>
import GroupChatComponent from '@/components/group-chat/GroupChatComponent.vue'
</script>

<style scoped>
.group-chat-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style> 