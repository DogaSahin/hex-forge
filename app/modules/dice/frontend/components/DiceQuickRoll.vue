<script setup lang="ts">
  import { ref } from 'vue'

  defineProps<{ expr: string }>()

  const rolls = ref(0)
</script>

<template>
  <div class="dice-quick-roll">
    <button type="button" class="btn" @click="rolls++">Quick roll {{ expr }}</button>
    <span class="dice-quick-roll__count">rolled {{ rolls }}× this session</span>
  </div>
</template>

<style scoped>
  .dice-quick-roll {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0.75rem 0;
  }
  .dice-quick-roll__count {
    color: var(--muted, #8a8f98);
    font-size: 0.85rem;
  }
</style>
