# Alpine.js — Directive Quick Reference

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
