---
name: tailwind-4
description: "Tailwind CSS 4 for Django/Alpine/HTMX — @theme CSS-first config, js- selector convention, no var()/hex in class attributes. Trigger: writing utility classes, @theme, dark-mode, or js- hooks."
metadata:
  version: "2.0"
---

## Critical Patterns

### Never Use var() in Class Attributes

```html
<!-- NEVER: var() in class attribute -->
<div class="bg-[var(--color-primary)]"></div>
<div class="text-[var(--text-color)]"></div>

<!-- ALWAYS: Use Tailwind semantic classes -->
<div class="bg-primary"></div>
<div class="text-slate-400"></div>
```

### Never Use Hex Colors in Class Attributes

```html
<!-- NEVER: Hex colors -->
<p class="text-[#ffffff]"></p>
<div class="bg-[#1e293b]"></div>

<!-- ALWAYS: Use Tailwind color classes or theme tokens -->
<p class="text-white"></p>
<div class="bg-slate-800"></div>
```

### Use js- Prefix for JavaScript Selectors

Separate styling from behavior. The `js-` prefix is MANDATORY for any element with JavaScript functionality (HTMX, Alpine.js, vanilla JS).

```html
<!-- CORRECT: js- prefix for behavior, Tailwind for styling -->
<button class="js-submit-form rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
  Enviar
</button>
<div id="js-policy-list" class="space-y-4"></div>

<!-- WRONG: no js- prefix on interactive elements -->
<button id="submitForm" class="rounded-lg bg-blue-600 px-4 py-2">Enviar</button>
```

Rules:
- `js-` classes/IDs are exclusively for JavaScript hooks, NEVER for styling
- Prefer `.js-` classes for elements that appear multiple times
- Use `#js-` IDs only for unique elements
- When using Alpine.js, prefer `x-ref` over `js-` for intra-component references

---

## Before submitting
- [ ] No `var()` in `class=` attributes
- [ ] No hex colors in `class=` attributes
- [ ] Every interactive element (JS/HTMX/Alpine target) has a `js-` prefix

---

## Decision Tree

```
Tailwind class exists?           → class="..."
Need theme token for utilities?  → @theme { --color-brand: oklch(...); }
Conditional classes (Alpine.js)? → x-bind:class="{ 'bg-blue-500': active }"
Dynamic server-side class?       → Django template {% if %} with class
Truly dynamic value (percent)?   → style="width: {{ percentage }}%"
Library needs raw CSS value?     → Use var(--color-*) in style attribute only
Static only?                     → class="..." (no conditionals needed)
```

---

## CSS-First Configuration (@theme)

Tailwind CSS 4 replaces `tailwind.config.js` with CSS-native `@theme`:

```css
@import "tailwindcss";

@theme {
  /* Custom colors — generates bg-brand, text-brand, border-brand, etc. */
  --color-brand: oklch(0.72 0.11 178);
  --color-brand-light: oklch(0.85 0.08 178);
  --color-brand-dark: oklch(0.55 0.14 178);

  /* Custom fonts */
  --font-display: "Satoshi", sans-serif;
  --font-body: "Inter", sans-serif;

  /* Custom breakpoint */
  --breakpoint-3xl: 120rem;

  /* Custom easing */
  --ease-fluid: cubic-bezier(0.3, 0, 0, 1);

  /* Custom animation */
  --animate-fade-in: fade-in 0.3s ease-out;

  @keyframes fade-in {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }
}
```

### Key @theme Namespaces

| Namespace          | Utilities Generated                            |
| ------------------ | ---------------------------------------------- |
| `--color-*`        | `bg-*`, `text-*`, `border-*`, `fill-*`, etc.  |
| `--font-*`         | `font-sans`, `font-display`, etc.              |
| `--text-*`         | `text-xs`, `text-xl`, etc.                     |
| `--font-weight-*`  | `font-bold`, `font-light`, etc.                |
| `--breakpoint-*`   | `sm:*`, `md:*`, `3xl:*` responsive variants    |
| `--spacing-*`      | `px-*`, `mb-*`, `w-*`, `h-*` sizing utilities  |
| `--radius-*`       | `rounded-sm`, `rounded-lg`, etc.               |
| `--shadow-*`       | `shadow-md`, `shadow-lg`, etc.                 |
| `--animate-*`      | `animate-spin`, `animate-fade-in`, etc.        |

### Override vs Extend

```css
@theme {
  /* Extend: adds alongside defaults */
  --color-brand: oklch(0.72 0.11 178);

  /* Override a specific value */
  --breakpoint-sm: 30rem;

  /* Replace entire namespace: reset then define */
  --color-*: initial;
  --color-white: #fff;
  --color-brand: oklch(0.72 0.11 178);
}
```

---

## @apply and @utility Directives

### @apply — Inline Utilities in Custom CSS

Use `@apply` to apply Tailwind utilities inside custom CSS rules. Best for styling third-party widgets or elements you cannot add classes to directly:

```css
/* Styling a third-party widget */
.select2-dropdown {
  @apply rounded-b-lg shadow-md;
}

.select2-search {
  @apply rounded border border-gray-300;
}
```

### @utility — Define Custom Utilities

Create custom utilities that work with all variants (hover, dark, responsive, etc.):

```css
@utility content-auto {
  content-visibility: auto;
}

@utility scrollbar-hidden {
  scrollbar-width: none;
  &::-webkit-scrollbar {
    display: none;
  }
}
```

Usage in templates:

```html
<main class="content-auto scrollbar-hidden">...</main>
<div class="hover:content-auto lg:content-auto">...</div>
```

### @variant — Apply Variants in CSS

```css
.card {
  background: white;
  @variant dark {
    background: var(--color-slate-800);
  }
}
```

---

## Theme Variables in Custom CSS

(var() is CSS-only — never in class attributes; see Critical Patterns above.)

```css
@layer components {
  .prose {
    font-size: var(--text-base);
    color: var(--color-gray-700);
  }

  .prose h1 {
    font-size: var(--text-2xl);
    font-weight: var(--font-weight-semibold);
  }
}
```

### --spacing() and --alpha() Functions

```css
.custom-card {
  /* Spacing function */
  padding: --spacing(4);
  margin-bottom: --spacing(6);

  /* Alpha/opacity function */
  background-color: --alpha(var(--color-brand) / 50%);
  border-color: --alpha(var(--color-gray-500) / 20%);
}
```

---

## Dark Mode

### Default: System Preference

The `dark:` variant uses `prefers-color-scheme` by default:

```html
<div class="bg-white text-gray-900 dark:bg-slate-900 dark:text-white">
  <h2 class="text-lg font-bold text-gray-800 dark:text-gray-100">Title</h2>
  <p class="text-gray-600 dark:text-gray-400">Description text.</p>
</div>
```

### Manual Toggle with CSS Class

```css
/* In your main CSS file */
@import "tailwindcss";
@custom-variant dark (&:where(.dark, .dark *));
```

```html
<!-- Toggle via class on <html> -->
<html class="dark">
  <body class="bg-white dark:bg-slate-900">
    ...
  </body>
</html>
```

### Manual Toggle with Data Attribute

```css
@import "tailwindcss";
@custom-variant dark (&:where([data-theme=dark], [data-theme=dark] *));
```

```html
<html data-theme="dark">
  <body class="bg-white dark:bg-slate-900">...</body>
</html>
```

### Dark Mode with Alpine.js Toggle

```html
<div x-data="{ dark: localStorage.getItem('theme') === 'dark' }"
     x-init="$watch('dark', val => { localStorage.setItem('theme', val ? 'dark' : 'light'); document.documentElement.classList.toggle('dark', val) })">
  <button class="js-theme-toggle" @click="dark = !dark">
    <span x-show="!dark">Dark</span>
    <span x-show="dark">Light</span>
  </button>
</div>
```

### Theme Variable Overrides for Dark Mode

```css
@import "tailwindcss";

@theme {
  --color-surface: oklch(0.99 0 0);
  --color-surface-dark: oklch(0.15 0.02 260);
  --color-text-primary: oklch(0.2 0 0);
  --color-text-primary-dark: oklch(0.95 0 0);
}
```

```html
<div class="bg-surface text-text-primary dark:bg-surface-dark dark:text-text-primary-dark">
  ...
</div>
```

---

## Responsive Design

Mobile-first: apply base styles for mobile, then override at larger breakpoints. Container queries (built into v4, no plugin needed) let components respond to their own container width rather than the viewport.

```html
<!-- Container query example -->
<div class="@container">
  <div class="grid grid-cols-1 @sm:grid-cols-2 @lg:grid-cols-4">
    {% for card in cards %}
      <div class="rounded-lg border p-4">{{ card.title }}</div>
    {% endfor %}
  </div>
</div>
```

For the full breakpoints table and responsive snippets (grid, show/hide, typography, spacing), see [references/utility-patterns.md](./references/utility-patterns.md#responsive).

---

## Common Utility Patterns

For standard utility snippets (Flexbox, Grid, Spacing, Typography, Borders, States, Gradients, arbitrary values), see [references/utility-patterns.md](./references/utility-patterns.md).

---

## Code Examples

### Django Template: Card Component

```html
{# templates/components/card.html #}
<article class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm
                transition-shadow hover:shadow-md
                dark:border-gray-700 dark:bg-slate-800">
  {% if image_url %}
    <img src="{{ image_url }}" alt="{{ title }}"
         class="h-48 w-full object-cover" loading="lazy">
  {% endif %}
  <div class="p-4 sm:p-6">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
      {{ title }}
    </h3>
    <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
      {{ description|truncatewords:30 }}
    </p>
    {% if cta_url %}
      <a href="{{ cta_url }}"
         class="mt-4 inline-flex items-center gap-1 text-sm font-medium text-blue-600
                hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300">
        {{ cta_text }}
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
        </svg>
      </a>
    {% endif %}
  </div>
</article>
```

### Django Template: Conditional Classes

```html
{# Server-side conditional classes #}
<span class="inline-flex items-center rounded-full px-2 py-1 text-xs font-medium
             {% if status == 'active' %}bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300
             {% elif status == 'pending' %}bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300
             {% else %}bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300
             {% endif %}">
  {{ status|title }}
</span>
```

### Alpine.js: Dynamic Classes

```html
{# Client-side conditional classes with Alpine.js #}
<div x-data="{ open: false }">
  <button class="js-dropdown-trigger flex items-center gap-2 rounded-lg border px-4 py-2
                  text-sm font-medium transition-colors
                  hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
          @click="open = !open">
    Menu
    <svg class="h-4 w-4 transition-transform" :class="{ 'rotate-180': open }"
         fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
    </svg>
  </button>

  <div x-show="open" x-transition
       class="js-dropdown-menu mt-2 rounded-lg border bg-white p-2 shadow-lg
              dark:border-gray-700 dark:bg-slate-800">
    <a href="#" class="block rounded px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700">
      Option 1
    </a>
    <a href="#" class="block rounded px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700">
      Option 2
    </a>
  </div>
</div>
```

### Alpine.js: x-bind:class Pattern

```html
<nav x-data="{ current: 'home' }">
  {% for item in nav_items %}
    <a href="{{ item.url }}"
       class="rounded-lg px-3 py-2 text-sm font-medium transition-colors"
       :class="current === '{{ item.slug }}'
         ? 'bg-blue-600 text-white'
         : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'"
       @click="current = '{{ item.slug }}'">
      {{ item.label }}
    </a>
  {% endfor %}
</nav>
```

### HTMX Integration

```html
{# HTMX dynamic content with loading states #}
<button class="js-load-more inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2
               text-sm font-medium text-white transition-colors
               hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        hx-get="{% url 'policy-list' %}?page={{ next_page }}"
        hx-target="#js-policy-list"
        hx-swap="beforeend"
        hx-indicator="#js-loading-spinner">
  Cargar más
</button>

<div id="js-policy-list" class="space-y-4">
  {% for policy in policies %}
    {% include "insurance/partials/policy_card.html" %}
  {% endfor %}
</div>

{# HTMX loading indicator #}
<div id="js-loading-spinner" class="htmx-indicator flex items-center justify-center py-4">
  <svg class="h-6 w-6 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
    <path class="opacity-75" fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
  </svg>
</div>
```

### HTMX: Inline Editing Pattern

```html
{# Display mode #}
<div id="js-field-{{ field.id }}" class="group flex items-center justify-between">
  <span class="text-sm text-gray-700 dark:text-gray-300">{{ field.value }}</span>
  <button class="js-edit-trigger invisible rounded p-1 text-gray-400
                  hover:text-gray-600 group-hover:visible"
          hx-get="{% url 'field-edit' field.id %}"
          hx-target="#js-field-{{ field.id }}"
          hx-swap="outerHTML">
    Edit
  </button>
</div>
```

### Responsive Table with Django

```html
{# Responsive data table #}
<div class="overflow-x-auto rounded-lg border dark:border-gray-700">
  <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
    <thead class="bg-gray-50 dark:bg-slate-800">
      <tr>
        <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider
                    text-gray-500 dark:text-gray-400">
          Nombre
        </th>
        <th class="hidden px-4 py-3 text-left text-xs font-medium uppercase tracking-wider
                    text-gray-500 dark:text-gray-400 sm:table-cell">
          Estado
        </th>
        <th class="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider
                    text-gray-500 dark:text-gray-400">
          Acciones
        </th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-slate-900">
      {% for item in items %}
        <tr class="transition-colors hover:bg-gray-50 dark:hover:bg-slate-800">
          <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-900 dark:text-white">
            {{ item.name }}
          </td>
          <td class="hidden whitespace-nowrap px-4 py-3 sm:table-cell">
            {% include "components/status_badge.html" with status=item.status %}
          </td>
          <td class="whitespace-nowrap px-4 py-3 text-right text-sm">
            <a href="{{ item.get_absolute_url }}"
               class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300">
              Ver
            </a>
          </td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
```

---

## Commands

```bash
# Build CSS (with Vite plugin)
npx vite build

# Watch mode during development
npx vite dev

# Build CSS with Tailwind CLI
npx @tailwindcss/cli -i app.css -o dist/output.css --watch

# Check compiled CSS output size
bat dist/output.css | rg "\.text-" | wc -l
```

---

## Resources

- **Theme docs**: https://tailwindcss.com/docs/theme
- **Dark mode**: https://tailwindcss.com/docs/dark-mode
- **Directives**: https://tailwindcss.com/docs/functions-and-directives
