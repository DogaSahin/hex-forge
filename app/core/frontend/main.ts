import { mountIslands, unmountIslands } from './mount'

function start(): void {
  mountIslands()
  // HTMX swaps server-rendered fragments in and out, so islands can arrive (or leave)
  // after the initial load. Mount the ones swapped in and unmount the ones swapped out,
  // scoped to the swapped subtree. Guard on window.htmx so this is inert without HTMX.
  if ('htmx' in window) {
    document.body.addEventListener('htmx:beforeSwap', (e) => unmountIslands(e.target as ParentNode))
    document.body.addEventListener('htmx:afterSwap', (e) => mountIslands(e.target as ParentNode))
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start)
} else {
  start()
}
