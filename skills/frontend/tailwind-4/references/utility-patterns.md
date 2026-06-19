# Tailwind v4 — Standard Utility Patterns

## Flexbox

```html
<div class="flex items-center justify-between gap-4">...</div>
<div class="flex flex-col gap-2">...</div>
<div class="inline-flex items-center">...</div>
```

## Grid

```html
<div class="grid grid-cols-3 gap-4">...</div>
<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">...</div>
```

## Spacing

```html
<div class="p-4"></div>            {# All sides #}
<div class="px-4 py-2"></div>      {# Horizontal, vertical #}
<div class="mx-auto"></div>        {# Center horizontally #}
<div class="mt-8 mb-4"></div>      {# Top, bottom margins #}
```

## Typography

```html
<h1 class="text-2xl font-bold text-gray-900 dark:text-white">...</h1>
<p class="text-sm text-gray-600 dark:text-gray-400">...</p>
<span class="text-xs font-medium uppercase tracking-wide">...</span>
```

## Borders and Shadows

```html
<div class="rounded-lg border border-gray-200 dark:border-gray-700">...</div>
<div class="rounded-full shadow-lg">...</div>
<div class="ring-2 ring-blue-500 ring-offset-2">...</div>
```

## States

```html
<button class="hover:bg-blue-600 focus:ring-2 active:scale-95">...</button>
<input class="focus:border-blue-500 focus:outline-none">
<div class="group-hover:opacity-100">...</div>
```

## Gradients (v4 syntax)

```html
<div class="bg-linear-to-r from-indigo-500 via-purple-500 to-pink-500">...</div>
<div class="bg-linear-45 from-blue-600 to-cyan-400">...</div>
```

## Arbitrary Values (Escape Hatch)

```html
<!-- OK for one-off values not in the design system -->
<div class="w-[327px]"></div>
<div class="grid-cols-[1fr_2fr_1fr]"></div>

<!-- NEVER for colors — use @theme instead -->
<div class="bg-[#1e293b]"></div>  {# NO #}
```

## Responsive

Mobile-first: style mobile first, then layer on larger screens with min-width prefixes.

| Prefix | Min-Width | Typical Use         |
| ------ | --------- | ------------------- |
| `sm:`  | 40rem     | Large phones        |
| `md:`  | 48rem     | Tablets             |
| `lg:`  | 64rem     | Small desktops      |
| `xl:`  | 80rem     | Large desktops      |
| `2xl:` | 96rem     | Extra-large screens |

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

<!-- Stack on mobile, side-by-side on md+, three columns on lg+ -->
<div class="flex flex-col gap-4 md:flex-row lg:gap-6">
  <aside class="w-full md:w-64 lg:w-72">Sidebar</aside>
  <main class="flex-1">Content</main>
</div>
```
