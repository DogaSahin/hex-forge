import { createApp } from 'vue'

import { registry } from './registry'

// Find every island placeholder and mount an isolated Vue app on it. Each island
// is its own createApp root — islands never share state. Props arrive as JSON in
// data-props (the server controls this payload; on /player it is broadcast-safe only).
export function mountIslands(root: ParentNode = document): void {
  const nodes = root.querySelectorAll<HTMLElement>('[data-vue]')
  nodes.forEach((el) => {
    if (el.dataset.vueMounted) return
    const name = el.dataset.vue
    if (!name) return
    const component = registry[name]
    if (!component) {
      console.warn(`[hexforge] unknown Vue island: "${name}"`)
      return
    }
    let props: Record<string, unknown> = {}
    if (el.dataset.props) {
      try {
        props = JSON.parse(el.dataset.props)
      } catch (err) {
        console.error(`[hexforge] invalid data-props on island "${name}"`, err)
        return
      }
    }
    createApp(component, props).mount(el)
    el.dataset.vueMounted = '1'
  })
}
