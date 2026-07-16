<script setup lang="ts">
  import { ref } from 'vue'

  const props = withDefaults(
    defineProps<{
      title: string
      items?: string[]
      open?: boolean
    }>(),
    { items: () => [], open: true },
  )

  const isOpen = ref(props.open)
</script>

<template>
  <section class="hex-panel">
    <button type="button" class="hex-panel__head" @click="isOpen = !isOpen">
      <span class="hex-panel__title">{{ title }}</span>
      <span class="hex-panel__toggle">{{ isOpen ? '−' : '+' }}</span>
    </button>
    <ul v-if="isOpen && items.length" class="hex-panel__body">
      <li v-for="item in items" :key="item">{{ item }}</li>
    </ul>
  </section>
</template>

<style scoped>
  .hex-panel {
    border: 1px solid var(--border, #2a2e36);
    border-radius: 8px;
    overflow: hidden;
    margin: 1rem 0;
  }
  .hex-panel__head {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0.9rem;
    background: var(--surface, #1c1f25);
    color: inherit;
    border: 0;
    font: inherit;
    cursor: pointer;
  }
  .hex-panel__body {
    list-style: none;
    margin: 0;
    padding: 0.6rem 0.9rem;
  }
  .hex-panel__body li {
    padding: 0.2rem 0;
  }
</style>
