import { mountIslands } from './mount'

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => mountIslands())
} else {
  mountIslands()
}
