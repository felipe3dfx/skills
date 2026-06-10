---
name: tailwind-4
description: >
  Tailwind CSS 4 patterns — theme variables, utility classes, Django template integration.
  Trigger: When styling with Tailwind — utility classes, theme variables, responsive design.
license: Apache-2.0
metadata:
  version: "2.0"
---

## When to Use

Use this skill when:
- Styling HTML elements with Tailwind CSS utility classes
- Defining or extending theme variables via `@theme`
- Writing `@apply` or `@utility` directives in CSS files
- Working with dark mode, responsive design, or conditional classes
- Integrating Tailwind with Django templates, Alpine.js, or HTMX

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

Use `var()` with theme variables ONLY inside CSS files or `style` attributes — NEVER in `class` attributes:

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

### Mobile-First Breakpoints

Tailwind uses min-width breakpoints. Style mobile first, then layer on larger screens:

```html
<!-- Stack on mobile, side-by-side on md+, three columns on lg+ -->
<div class="flex flex-col gap-4 md:flex-row lg:gap-6">
  <aside class="w-full md:w-64 lg:w-72">Sidebar</aside>
  <main class="flex-1">Content</main>
</div>
```

### Default Breakpoints

| Prefix | Min-Width | Typical Use         |
| ------ | --------- | ------------------- |
| `sm:`  | 40rem     | Large phones        |
| `md:`  | 48rem     | Tablets             |
| `lg:`  | 64rem     | Small desktops      |
| `xl:`  | 80rem     | Large desktops      |
| `2xl:` | 96rem     | Extra-large screens |

### Responsive Patterns

```html
<!-- Responsive grid -->
<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
  {% for item in items %}
    <div class="rounded-lg border p-4">{{ item.name }}</div>
  {% endfor %}
</div>

<!-- Show/hide by breakpoint -->
<nav class="hidden md:block">Desktop nav</nav>
<nav class="block md:hidden">Mobile nav</nav>

<!-- Responsive typography -->
<h1 class="text-xl font-bold sm:text-2xl lg:text-4xl">{{ page.title }}</h1>

<!-- Responsive spacing -->
<section class="px-4 py-6 sm:px-6 lg:px-8 lg:py-12">
  {{ content }}
</section>
```

### Container Queries (Built-in in v4)

No plugin needed:

```html
<div class="@container">
  <div class="grid grid-cols-1 @sm:grid-cols-2 @lg:grid-cols-4">
    {% for card in cards %}
      <div class="rounded-lg border p-4">{{ card.title }}</div>
    {% endfor %}
  </div>
</div>
```

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

## Common Utility Patterns

### Flexbox

```html
<div class="flex items-center justify-between gap-4">...</div>
<div class="flex flex-col gap-2">...</div>
<div class="inline-flex items-center">...</div>
```

### Grid

```html
<div class="grid grid-cols-3 gap-4">...</div>
<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">...</div>
```

### Spacing

```html
<div class="p-4"></div>            {# All sides #}
<div class="px-4 py-2"></div>      {# Horizontal, vertical #}
<div class="mx-auto"></div>        {# Center horizontally #}
<div class="mt-8 mb-4"></div>      {# Top, bottom margins #}
```

### Typography

```html
<h1 class="text-2xl font-bold text-gray-900 dark:text-white">...</h1>
<p class="text-sm text-gray-600 dark:text-gray-400">...</p>
<span class="text-xs font-medium uppercase tracking-wide">...</span>
```

### Borders and Shadows

```html
<div class="rounded-lg border border-gray-200 dark:border-gray-700">...</div>
<div class="rounded-full shadow-lg">...</div>
<div class="ring-2 ring-blue-500 ring-offset-2">...</div>
```

### States

```html
<button class="hover:bg-blue-600 focus:ring-2 active:scale-95">...</button>
<input class="focus:border-blue-500 focus:outline-none">
<div class="group-hover:opacity-100">...</div>
```

### Gradients (v4 syntax)

```html
<div class="bg-linear-to-r from-indigo-500 via-purple-500 to-pink-500">...</div>
<div class="bg-linear-45 from-blue-600 to-cyan-400">...</div>
```

### Arbitrary Values (Escape Hatch)

```html
<!-- OK for one-off values not in the design system -->
<div class="w-[327px]"></div>
<div class="grid-cols-[1fr_2fr_1fr]"></div>

<!-- NEVER for colors — use @theme instead -->
<div class="bg-[#1e293b]"></div>  {# NO #}
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
