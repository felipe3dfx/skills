---
name: alpinejs
description: >
  Alpine.js component patterns — directives, reactivity, Django template integration.
  Trigger: When using Alpine.js directives (x-data, x-show, x-bind) in templates.
license: Apache-2.0
metadata:
  version: "1.0"
---

## When to Use

Use this skill when:
- Writing or editing templates that use Alpine.js directives (`x-data`, `x-show`, `x-bind`, `x-on`, etc.)
- Creating interactive UI components (dropdowns, modals, tabs, tooltips, form toggles)
- Integrating Alpine.js with HTMX in Django templates
- Registering reusable Alpine components via `Alpine.data()` or `Alpine.store()`

---

## Critical Patterns

### Pattern 1: `js-` Prefix is MANDATORY

Every HTML element with JavaScript behavior (Alpine, HTMX, or vanilla JS) MUST use `js-` prefixed classes or IDs. This separates styling from behavior.

```html
<!-- classes for multiple elements -->
<div class="js-dropdown" x-data="{ open: false }">
  <button class="js-dropdown-trigger" @click="open = !open">Menu</button>
</div>

<!-- IDs for unique elements -->
<div id="js-main-modal" x-data="modal">...</div>
```

### Pattern 2: Alpine for Client-Side, HTMX for Server

Alpine.js handles **client-side state and interactions** (show/hide, toggles, local form state). HTMX handles **server communication** (fetching partials, submitting forms, swapping content). They work together, not as alternatives.

```html
<!-- Alpine: local UI state -->
<div class="js-filter-panel" x-data="{ expanded: false }">
  <button @click="expanded = !expanded">Filtros</button>
  <div x-show="expanded" x-transition x-cloak>
    <!-- HTMX: server-driven content -->
    <form class="js-filter-form" hx-get="/api/results/" hx-target="#js-results">
      ...
    </form>
  </div>
</div>
<div id="js-results"></div>
```

### Pattern 3: Register Reusable Components with `Alpine.data()`

Complex or reused components are registered via `Alpine.data()` inside the `ax3Common` callback. Keep inline `x-data` for trivial one-off state only.

```javascript
// In page-specific JS file (e.g., task-detail.js)
import { ax3Common } from './common/index.js';

ax3Common(Alpine => {
    Alpine.data('taskPrioritySelect', () => ({
        isOpen: false,
        selectedValue: '',
        toggle() { this.isOpen = !this.isOpen; },
        select(value) {
            this.selectedValue = value;
            this.isOpen = false;
        },
    }));
});
```

```html
<!-- In template: reference by name -->
<div class="js-priority-select" x-data="taskPrioritySelect">
  <button @click="toggle()" x-text="selectedValue || 'Seleccionar'"></button>
  <ul x-show="isOpen" x-transition x-cloak>
    <li @click="select('high')">Alta</li>
    <li @click="select('medium')">Media</li>
  </ul>
</div>
```

### Pattern 4: Global State with `Alpine.store()`

Use stores for state shared across components on the same page (modal, alert, toast, filters).

```javascript
ax3Common(Alpine => {
    Alpine.store('confirmationAlert', {
        getConfirmationText() {
            return 'Are you sure?';
        },
    });
});
```

```html
<!-- Access store in templates -->
<button @click="Alpine.store('alert').show({
    type: 'warning',
    title: 'Confirmar',
    text: Alpine.store('confirmationAlert').getConfirmationText(),
    doneBtn: 'Confirmar',
    cancelBtn: 'Cancelar',
    doneCallback: (alertId) => { Alpine.store('alert').close(alertId); }
})">
  Eliminar
</button>
```

### Pattern 5: `ax3Common` Bootstrap Pattern

All page JS files follow the same structure: import `ax3Common`, register plugins, register components, start Alpine.

```javascript
import collapse from '../node_modules/@alpinejs/collapse/dist/module.esm.js';
import { ax3Common } from './common/index.js';

ax3Common(Alpine => {
    Alpine.plugin(collapse);

    Alpine.data('myComponent', () => ({
        // component state and methods
    }));

    // HTMX event listeners for Alpine + HTMX coordination
    htmx.on('htmx:afterSettle', () => {
        // re-process or re-init after HTMX swaps
    });
});
```

### Pattern 6: Use `x-ref` for Intra-Component References

Inside an Alpine component, prefer `x-ref` + `$refs` over `js-` selectors for accessing sibling elements. Reserve `js-` for cross-component or external JS targeting.

```html
<form x-data="{ showClearBtn: false }"
      x-init="if ($refs.searchInput.value) showClearBtn = true;"
      x-ref="searchForm">
  <input x-ref="searchInput"
         @input="showClearBtn = $refs.searchInput.value.length > 0" />
  <button x-show="showClearBtn" x-cloak
          @click="$refs.searchInput.value = ''; showClearBtn = false;">
    Limpiar
  </button>
</form>
```

---

## Decision Tree

```
Trivial toggle (show/hide, boolean)?  -> Inline x-data="{ open: false }"
Reusable across pages?                -> Alpine.data() in extend-alpine.js
Reusable on one page only?            -> Alpine.data() in page JS file
Shared state between components?      -> Alpine.store()
Need server data or partial swap?     -> HTMX (hx-get, hx-post, hx-target)
Client-side interaction only?         -> Alpine.js directives
Need both local UI + server fetch?    -> Combine Alpine + HTMX on same element
Reference sibling inside component?   -> x-ref + $refs
Reference from outside component?     -> js- prefixed class/ID
```

---

## Code Examples

### Example 1: Dropdown with Transitions

```html
<div class="js-dropdown" x-data="{ open: false }">
  <button class="js-dropdown-trigger" @click="open = !open">
    Opciones
  </button>
  <div x-show="open"
       x-cloak
       x-transition:enter="transition duration-300 ease-in-out"
       x-transition:enter-start="opacity-0"
       x-transition:enter-end="opacity-100"
       x-transition:leave="transition duration-300 ease-in-out"
       x-transition:leave-start="opacity-100"
       x-transition:leave-end="opacity-0"
       @click.outside="open = false"
       @keydown.escape.window="open = false">
    <ul>
      <li><a href="#">Editar</a></li>
      <li><a href="#">Eliminar</a></li>
    </ul>
  </div>
</div>
```

### Example 2: Django Component with Alpine + HTMX

```html
<!-- django-components template: tooltip.html -->
<span class="js-tooltip-wrapper"
      x-data="tooltip"
      x-init="placement = '{{ placement }}'; offset = {{ offset }};">
  <span @mouseover="show()" @mouseleave="hide()">
    {% slot "action" %}
      <span class="text-sm text-primary-600">{{ action_text }}</span>
    {% endslot %}
  </span>
  <template x-teleport="body">
    <span x-show="isOpen"
          x-bind="attrs"
          x-cloak
          x-init="htmx.process($el)"
          x-transition>
      {% slot "content" %}
        <span class="p-2 rounded-sm shadow-sm bg-gray-950 text-white">{{ content_text }}</span>
      {% endslot %}
    </span>
  </template>
</span>
```

### Example 3: Form with `setupForm` Bind + HTMX Modal

```html
<form x-bind="setupForm" x-data>
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit" class="js-submit-btn btn btn-primary">Guardar</button>
</form>

<!-- HTMX button that opens Alpine modal -->
<button class="js-open-modal btn"
        hx-get="{% url 'myapp:modal_content' %}"
        hx-swap="none"
        hx-on::after-on-load="Alpine.store('modal').show({
            content: event.detail.xhr.response,
            loaded(modal) { htmx.process(modal); },
            transition: 'appear-center'
        })">
  Abrir Modal
</button>
```

### Example 4: Inline Alpine for Simple File Input

```html
<label class="js-file-input form-input input-icon input-icon--file"
       x-data="{ fileName: 'Seleccionar archivo...' }">
  <input type="file"
         class="hidden"
         @change="fileName = $event.target.files[0]?.name || 'Seleccionar archivo...'" />
  <span x-text="fileName"></span>
</label>
```

### Example 5: Conditional Form Fields

```html
<div x-data="{ ticketType: '{{ object.request_type|default:"" }}' }">
  <select x-model="ticketType" class="js-ticket-type form-select">
    <option value="">Seleccionar...</option>
    <option value="claim">Reclamo</option>
    <option value="request">Solicitud</option>
  </select>

  <div x-show="ticketType === 'claim'" x-transition x-cloak>
    <!-- Claim-specific fields -->
  </div>

  <div x-show="ticketType === 'request'" x-transition x-cloak>
    <!-- Request-specific fields -->
  </div>
</div>
```

---

## Directive Quick Reference

| Directive | Purpose | Example |
|-----------|---------|---------|
| `x-data` | Initialize component state | `x-data="{ open: false }"` |
| `x-show` | Toggle visibility (CSS display) | `x-show="open"` |
| `x-if` | Conditionally render (DOM add/remove) | `<template x-if="active">` |
| `x-for` | Loop over items | `<template x-for="item in items">` |
| `x-bind` | Bind attributes dynamically | `x-bind:class="{ active: isActive }"` or `:class` |
| `x-on` | Listen to events | `x-on:click="open = true"` or `@click` |
| `x-model` | Two-way binding on inputs | `x-model="searchQuery"` |
| `x-text` | Set element text content | `x-text="message"` |
| `x-html` | Set element innerHTML | `x-html="richContent"` |
| `x-ref` | Reference element via `$refs` | `x-ref="input"` -> `$refs.input` |
| `x-init` | Run expression on init | `x-init="fetchData()"` |
| `x-effect` | Re-run on reactive dependency change | `x-effect="console.log(count)"` |
| `x-transition` | Apply enter/leave transitions | `x-transition` or granular modifiers |
| `x-cloak` | Hide until Alpine initializes | `x-cloak` (pair with `[x-cloak] { display: none }`) |
| `x-teleport` | Render element elsewhere in DOM | `<template x-teleport="body">` |

## Alpine Plugins Used in ilaos

| Plugin | Import | Purpose |
|--------|--------|---------|
| `@alpinejs/collapse` | `import collapse from '@alpinejs/collapse/...'` | Smooth height transitions for expand/collapse |
| `@alpinejs/mask` | `import mask from '@alpinejs/mask/...'` | Input masking (currency, phone, etc.) |

Register plugins inside `ax3Common` callback: `Alpine.plugin(collapse);`

---

## Anti-Patterns

```html
<!-- WRONG: No js- prefix on interactive element -->
<div id="dropdown" x-data="{ open: false }">...</div>

<!-- WRONG: Using Alpine for server communication -->
<button @click="fetch('/api/data').then(...)">Load</button>
<!-- RIGHT: Use HTMX for server requests -->
<button class="js-load-data" hx-get="/api/data" hx-target="#js-results">Load</button>

<!-- WRONG: Complex inline x-data for reusable components -->
<div x-data="{ items: [], loading: false, async fetch() { ... }, filter(q) { ... } }">
<!-- RIGHT: Register with Alpine.data() -->
<div class="js-item-list" x-data="itemList">

<!-- WRONG: Using querySelector inside Alpine component -->
<div x-data="{ toggle() { document.querySelector('#target').classList.toggle('active') } }">
<!-- RIGHT: Use x-ref or Alpine reactivity -->
<div x-data="{ active: false }">
  <div :class="{ active: active }" x-ref="target">...</div>
</div>

<!-- WRONG: Using x-if for simple show/hide -->
<template x-if="open"><div>Content</div></template>
<!-- RIGHT: Use x-show (keeps element in DOM, better for transitions) -->
<div x-show="open" x-transition x-cloak>Content</div>
```

---

## Resources

- **Project bootstrap**: `ax3Common` in `apps/core/static/js/common/index.js`
- **Shared components**: `Alpine.data()` registrations in `apps/core/static/js/utils/extend-alpine.js`
- **Coding standards**: `docs/02-coding-standards.md` (js- prefix rules)
