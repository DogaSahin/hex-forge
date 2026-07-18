import { createApp, type App } from 'vue'

import { registry } from './registry'

// Remember each island's Vue app so it can be torn down when its host node is
// swapped out (see unmountIslands). Keyed weakly so removed nodes stay collectable.
const mounted = new WeakMap<HTMLElement, App>()

// Find every island placeholder and mount an isolated Vue app on it. Each island
// is its own createApp root — islands never share state. Props arrive as JSON in
// data-props (the server controls this payload; on /player it is broadcast-safe only).
// Re-invokable and idempotent (the vueMounted guard), so it is safe to call again on
// fragments that HTMX swaps in after the initial load.
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
    const app = createApp(component, props)
    app.mount(el)
    mounted.set(el, app)
    el.dataset.vueMounted = '1'
  })
}

// Tear down islands inside `root` before HTMX detaches them, so long DM sessions
// that repeatedly swap fragments don't accumulate orphaned Vue apps and listeners.
export function unmountIslands(root: ParentNode = document): void {
  const nodes = root.querySelectorAll<HTMLElement>('[data-vue]')
  nodes.forEach((el) => {
    const app = mounted.get(el)
    if (!app) return
    app.unmount()
    mounted.delete(el)
    delete el.dataset.vueMounted
  })
}
