<script setup lang="ts">
import {RouterView } from 'vue-router'
import {layoutService} from './services/layoutService'
import { onMounted, onUnmounted, nextTick } from 'vue'

onMounted(() => {
  layoutService.onResize();
  nextTick().then(() => {
      window.addEventListener('resize', () => layoutService.onResize());
  });
});

onUnmounted(() => {
  window.removeEventListener('resize', () => layoutService.onResize()); 
});

</script>

<template>
  <RouterView />
</template>
