---
name: htmx
description: "HTMX — partial rendering, Django CBV integration (HTMXFilterMixin/HTMXRequestMixin), OOB swaps. Trigger: adding HTMX attributes, partial templates, or HTMX mixins; deciding HTMX vs Alpine.js."
metadata:
  version: "1.0"
---

## Critical Patterns

### Pattern 1: `js-` Prefix is MANDATORY

Every element with HTMX behavior MUST have a `js-` prefixed class or ID. This separates styling from behavior.

```html
<!-- ✅ Correct -->
<button class="js-load-more btn" hx-get="/items/" hx-target="#js-item-list">
  Cargar más
</button>
<div id="js-item-list"></div>

<!-- ❌ Wrong: no js- prefix -->
<button class="load-more btn" hx-get="/items/" hx-target="#item-list">
  Cargar más
</button>
```

### Pattern 2: Partial Templates

Full templates include the page shell. Partial templates render ONLY the fragment HTMX replaces.

```
templates/
  myapp/
    list.html                  # Full page (extends base)
    partials/
      _list.html               # Just the list fragment
      _list_item.html          # Single item (for OOB or append)
```

```html
{# myapp/partials/_list.html #}
<div id="js-item-list">
  {% for item in object_list %}
    {% include "myapp/partials/_list_item.html" %}
  {% endfor %}
</div>
```

### Pattern 3: Django CBV + HTMXFilterMixin

Use `HTMXFilterMixin` for list views that filter via HTMX. The mixin auto-switches between full and partial templates.

```python
from apps.core.mixins import HTMXFilterMixin, DashboardMixin
from django.views.generic import ListView

class PolicyListView(HTMXFilterMixin, DashboardMixin, ListView):
    model = Policy
    template_name = 'insurance/policy_list.html'
    partial_name = 'insurance/partials/_policy_list.html'
    context_object_name = 'policies'
    active_page = 'policies'

    def get_queryset(self):
        queryset = Policy.objects.find_all_by_agency(self.agency)
        # Apply filters from GET params
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset
```

### Pattern 4: Django CBV + HTMXRequestMixin

Use `HTMXRequestMixin` for views that ONLY accept HTMX requests (returns 400 for non-HTMX).

```python
from apps.core.mixins import HTMXRequestMixin, DashboardMixin
from django.views.generic import FormView

class InlineEditView(HTMXRequestMixin, DashboardMixin, FormView):
    template_name = 'myapp/partials/_edit_form.html'

    def form_valid(self, form):
        entity = form.save()
        return self.render_to_response(self.get_context_data(entity=entity))
```

---

## Decision Tree

```
Need to filter/search a list?                  → HTMXFilterMixin + hx-get with query params
Need a form that only works via HTMX?          → HTMXRequestMixin + hx-post
Need to update multiple DOM areas at once?     → OOB swap (hx-swap-oob)
Need client-side toggle/state (no server)?     → Alpine.js, NOT HTMX
  Toggle visibility, dropdowns?               → Alpine.js (no server trip)
  Form validation (live)?                     → Alpine.js (instant feedback, no latency)
  Complex UI state (modals, wizards)?         → Alpine.js (local state management)
  Tabs switching pre-loaded content?          → Alpine.js (already in DOM, just toggle)
Need navigation without full reload?           → hx-boost="true" on <a> or <form>
Need to replace content?                       → hx-swap="innerHTML" (default)
Need to append to a list?                      → hx-swap="beforeend"
Need to remove an element after action?        → hx-swap="delete" or hx-swap="outerHTML" with empty response
Fetch/submit data to server?                   → HTMX (server-rendered HTML partials)
  CRUD operations?                            → HTMX (server must process + persist)
  Tabs loading content from server?           → HTMX (each tab fetches its partial)
  Filter/search with server data?             → HTMX (needs fresh data from backend)
```

**Rule**: If the interaction requires the server, use HTMX. If it is purely client-side state, use Alpine.js. When using Alpine.js, prefer `x-ref` over `js-` selectors for intra-component references.

---

## Code Examples

### Example 1: Filter Form with HTMX

```html
<form class="js-filter-form"
      hx-get="{% url 'policy-list' %}"
      hx-target="#js-policy-list"
      hx-trigger="change, keyup changed delay:300ms from:find input"
      hx-swap="innerHTML"
      hx-indicator="#js-loading">
  <input type="text" name="search" placeholder="Buscar..." />
  <select name="status">
    <option value="">Todos</option>
    <option value="active">Activa</option>
    <option value="expired">Vencida</option>
  </select>
</form>

<div id="js-loading" class="htmx-indicator">Cargando...</div>

<div id="js-policy-list">
  {% include "insurance/partials/_policy_list.html" %}
</div>
```

### Example 2: OOB (Out of Band) Swap

Update the list AND a counter badge in a single response.

```html
{# Response returned by Django view #}
<div id="js-policy-list">
  {% for policy in policies %}
    {% include "insurance/partials/_policy_item.html" %}
  {% endfor %}
</div>

{# OOB: also update the counter in the sidebar #}
<span id="js-policy-count" hx-swap-oob="true">{{ total_count }}</span>
```

### Example 3: Boosted Navigation

```html
{# Apply hx-boost to a nav container — all child links become HTMX requests #}
<nav hx-boost="true" hx-target="#js-main-content" hx-swap="innerHTML" hx-push-url="true">
  <a href="{% url 'dashboard' %}">Dashboard</a>
  <a href="{% url 'policy-list' %}">Pólizas</a>
</nav>

<main id="js-main-content">
  {% block content %}{% endblock %}
</main>
```

### Example 4: Delete with Confirmation

```html
<button class="js-delete-policy btn-danger"
        hx-delete="{% url 'policy-delete' policy.pk %}"
        hx-target="closest tr"
        hx-swap="outerHTML swap:300ms"
        hx-confirm="¿Está seguro de eliminar esta póliza?">
  Eliminar
</button>
```

### Example 5: Loading Indicators and Transitions

```html
{# Indicator scoped to a specific element #}
<button class="js-submit btn"
        hx-post="{% url 'policy-create' %}"
        hx-target="#js-result"
        hx-indicator="#js-spinner">
  Crear Póliza
</button>
<span id="js-spinner" class="htmx-indicator">
  <svg class="animate-spin h-5 w-5">...</svg>
</span>
```

```css
/* HTMX built-in indicator class */
.htmx-indicator { opacity: 0; transition: opacity 200ms ease-in; }
.htmx-request .htmx-indicator { opacity: 1; }
.htmx-request.htmx-indicator { opacity: 1; }
```

### Example 6: Inline Edit Pattern

```html
{# Display mode #}
<div id="js-policy-{{ policy.pk }}" class="js-policy-display">
  <span>{{ policy.number }}</span>
  <button class="js-edit-trigger"
          hx-get="{% url 'policy-edit' policy.pk %}"
          hx-target="#js-policy-{{ policy.pk }}"
          hx-swap="outerHTML">
    Editar
  </button>
</div>

{# Edit mode (returned by the edit view) #}
<form id="js-policy-{{ policy.pk }}" class="js-policy-edit"
      hx-put="{% url 'policy-update' policy.pk %}"
      hx-target="this"
      hx-swap="outerHTML">
  <input name="number" value="{{ policy.number }}" />
  <button type="submit">Guardar</button>
  <button class="js-cancel-edit"
          hx-get="{% url 'policy-display' policy.pk %}"
          hx-target="#js-policy-{{ policy.pk }}"
          hx-swap="outerHTML">
    Cancelar
  </button>
</form>
```

---

## Key HTMX Attributes Reference

Full HTMX attribute reference: see [references/htmx-attributes.md](./references/htmx-attributes.md).

---

## Common Pitfalls

- **Missing CSRF token**: Django requires CSRF for POST/PUT/DELETE. Add `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'` directly on the form or triggering element (or on a common ancestor).
- **Forgetting `hx-target`**: Without it, HTMX replaces the triggering element itself (`hx-swap="outerHTML"` is NOT the default — `innerHTML` is)
- **N+1 partials**: Keep partials lean. Do not query the DB inside template tags — pass pre-fetched data from the view
- **No `js-` prefix**: Every element with HTMX attributes MUST have a `js-` prefixed class or ID
- **Using HTMX for client-only state**: Dropdowns, toggles, modals that need no server data belong in Alpine.js, not HTMX

---

## Resources

- **Project mixins**: `apps/core/mixins.py` — `HTMXRequestMixin`, `HTMXFilterMixin`, `DashboardMixin`
- **Project docs**: start with `docs/agents/AGENTS.md` as the agent-facing router for repo conventions; follow the project-specific HTMX or JavaScript guide it points to for integration patterns and `js-` prefix rules.
