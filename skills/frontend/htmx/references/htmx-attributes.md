# HTMX — Key Attributes Reference

| Attribute | Purpose | Example |
|---|---|---|
| `hx-get` | GET request | `hx-get="/items/"` |
| `hx-post` | POST request | `hx-post="/items/create/"` |
| `hx-put` | PUT request | `hx-put="/items/1/update/"` |
| `hx-delete` | DELETE request | `hx-delete="/items/1/"` |
| `hx-target` | Where to place response | `hx-target="#js-list"` |
| `hx-swap` | How to swap content | `innerHTML`, `outerHTML`, `beforeend`, `afterbegin`, `delete`, `none` |
| `hx-trigger` | What triggers the request | `click`, `change`, `keyup changed delay:500ms`, `load`, `revealed`, `intersect` |
| `hx-indicator` | Loading indicator element | `hx-indicator="#js-spinner"` |
| `hx-confirm` | Confirmation dialog | `hx-confirm="¿Está seguro?"` |
| `hx-boost` | Boost links/forms to AJAX | `hx-boost="true"` |
| `hx-push-url` | Update browser URL | `hx-push-url="true"` |
| `hx-swap-oob` | Out of Band swap | `hx-swap-oob="true"` |
| `hx-select` | Select subset of response | `hx-select="#js-fragment"` |
| `hx-vals` | Extra values to send | `hx-vals='{"key": "value"}'` |
| `hx-headers` | Extra headers | `hx-headers='{"X-Custom": "val"}'` |
| `hx-include` | Include extra inputs | `hx-include="[name='csrf']"` |
