import type { Component } from 'vue'

// Auto-discover every island component: core-owned plus each module's own
// `frontend/components/`. Adding a component is "drop a .vue in a module folder" —
// no central edit — mirroring the Python register(registry) pattern. Paths are
// project-root absolute (root = repo, per vite.config.ts).
const modules = import.meta.glob<{ default: Component }>(
  ['/app/core/frontend/components/*.vue', '/app/modules/*/frontend/components/*.vue'],
  { eager: true },
)

function kebab(name: string): string {
  return name
    .replace(/\.vue$/, '')
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .toLowerCase()
}

export const registry: Record<string, Component> = {}
for (const path in modules) {
  const file = path.split('/').pop() ?? ''
  const key = kebab(file)
  // Two components resolving to the same key (e.g. same filename in core and a
  // module, or in two modules) would otherwise clobber each other silently by
  // glob order. Warn loudly rather than mount the wrong component.
  if (key in registry) {
    console.warn(
      `[hexforge] duplicate Vue island name "${key}" — "${path}" overrides an earlier component`,
    )
  }
  registry[key] = modules[path].default
}
