---
name: django-components
description: >
  django-components patterns — reusable template components with slots, props, and composition.
  Trigger: When creating or editing django-components (template components with Python class).
license: Apache-2.0
metadata:
  version: "1.0"
---

## When to Use

Use this skill when:
- Creating a new reusable UI component (button, badge, field, tooltip, etc.)
- Editing an existing component's Python class or template
- Composing components inside other components (nesting)
- Adding slots, props, or HTMX/Alpine.js behavior to a component

---

## Critical Patterns

### Pattern 1: Component Directory Structure

Every component lives in its own directory under the project-root `components/` folder. One directory per component, named after the component in `snake_case`.

```
components/
├── badge/
│   └── badge.py
│   └── badge.html
├── button/
│   ├── button.py
│   ├── button.html
│   ├── button_icon.html
│   ├── link.html
│   └── link_icon.html
├── field/
│   ├── field.py
│   ├── _attrs.html          # partial shared across templates
│   ├── input.html
│   ├── select.html
│   └── textarea.html
└── tooltip/
    ├── tooltip.py
    └── tooltip.html
```

- **No JS/CSS files inside component dirs** — styling uses Tailwind utility classes, interactivity uses Alpine.js `x-data` directives referencing globally-registered Alpine components.
- Partial templates (shared within a component) use `_` prefix: `_attrs.html`.
- Template paths are relative to the component dir: `'badge/badge.html'`, not absolute.

### Pattern 2: Python Class — Registration and Props

```python
from django_components import component


@component.register('badge')
class Badge(component.Component):
    """A component that generates HTML badge."""

    template_name = 'badge/badge.html'

    def get_context_data(self, text, **extras):
        color_list = {
            'primary': 'badge--primary',
            'green': 'badge--green',
        }
        color_class = color_list.get(extras.get('color'), color_list['primary'])

        return {
            'text': text,
            'final_class': f'badge {color_class} {extras.get("extra_class", "")}',
        }
```

**Rules:**
- Import ONLY `from django_components import component`
- Register with `@component.register('name')` — name matches directory name
- Class inherits `component.Component`
- No module-level docstrings (project coding standard)
- Required props are positional args in `get_context_data`; optional props go in `**extras`
- Return a flat dict — no nested structures
- Build CSS class strings in Python using BEM-like lookups (`color_list`, `size_list`)

### Pattern 3: Dynamic Template Selection

When a component has multiple visual variants, use `get_template_name` instead of `template_name`:

```python
def get_template_name(self, context):
    template_list = {
        'button': 'button/button.html',
        'button_icon': 'button/button_icon.html',
        'link': 'button/link.html',
        'link_icon': 'button/link_icon.html',
    }
    return template_list.get(context['style'], template_list['button'])
```

### Pattern 4: Slots — Default, Named, and Required

Templates use `{% slot %}` / `{% endslot %}` for extension points. Callers fill them with `{% fill %}` / `{% endfill %}`.

```html
{# Define slots in component template #}
<button class="{{ final_class }}"
        {% slot "extra_attrs" %}{% endslot %}>
    {{ text }}
    {% slot "btn_svg" default %}
    {% endslot %}
</button>
```

- **`{% slot "name" %}`** — named slot, optional by default
- **`{% slot "name" default %}`** — slot with default content (renders inner content if not filled)
- **`{% slot "name" required %}`** — caller MUST fill this slot
- **`{% slot "extra_attrs" %}`** — convention for injecting HTML attributes (HTMX, Alpine, etc.)

### Pattern 5: Invoking Components and Filling Slots

```html
{# Simple — no slots #}
{% component "badge" text="Active" color="green" %}
{% endcomponent %}

{# With slot fills #}
{% component "button" style="button_icon" text="Delete" color="error" size="sm" %}
    {% fill "extra_attrs" %}
        hx-delete="/api/item/1" hx-target="#item-1" hx-swap="outerHTML"
    {% endfill %}
    {% fill "btn_svg" %}
        {% include "svg/_trash.html" with svg_css_class="btn__svg" %}
    {% endfill %}
{% endcomponent %}
```

- Props are passed as `key=value` or `key=variable` (no quotes for variables)
- Every `{% component %}` MUST have a matching `{% endcomponent %}`
- Slot fills go INSIDE the component block

### Pattern 6: Component Composition (Nesting)

Components can render other components inside their templates:

```html
{# message/message.html — nests button component #}
<div class="message {{ final_class }}">
    {% slot "content" %}
        <p class="message__text">{{ text }}</p>
    {% endslot %}
    {% if allow_close %}
        {% component "button" style="button_icon" text="Close" color="no-color" extra_class="message__btn" %}
            {% fill "extra_attrs" %}
                @click="$el.closest('.message').remove()" x-data
            {% endfill %}
            {% fill "btn_svg" %}
                {% include "svg/_close.html" with svg_css_class="btn__svg" %}
            {% endfill %}
        {% endcomponent %}
    {% endif %}
</div>
```

### Pattern 7: Alpine.js Integration

Components reference globally-registered Alpine components via `x-data`. They do NOT define inline Alpine logic.

```html
<span x-data="tooltip"
      x-init="placement = '{{ placement }}'; offset = {{ offset }};">
    <span @mouseover="show()" @mouseleave="hide()">
        {% slot "action" %}
            <span>{{ action_text }}</span>
        {% endslot %}
    </span>
    <template x-teleport="body">
        <span x-show="isOpen" x-bind="attrs" x-cloak>
            {% slot "content" %}
                <span class="tooltip__text">{{ content_text }}</span>
            {% endslot %}
        </span>
    </template>
</span>
```

- `x-data="componentName"` — Alpine component registered globally
- `x-init` — pass Django template variables to Alpine state
- `x-teleport="body"` — for overlays, tooltips, modals
- `x-cloak` — prevent FOUC on Alpine-managed elements

### Pattern 8: HTMX Integration

HTMX attributes are injected via the `extra_attrs` slot pattern or directly in templates:

```html
{# Caller injects HTMX via slot #}
{% component "button" text="Delete" color="error" %}
    {% fill "extra_attrs" %}
        hx-delete="{{ remove_url }}"
        hx-target="#{{ target_id }}"
        hx-swap="outerHTML"
    {% endfill %}
{% endcomponent %}

{# Or directly in the component template #}
<button {% if remove_url %}hx-delete="{{ remove_url }}"{% endif %}
        {% if target_id %}hx-target="#{{ target_id }}" hx-swap="outerHTML"{% endif %}>
    {% include "svg/_close.html" %}
</button>
```

---

## Decision Tree

```
New UI element needed?
├── Reusable across pages?        → Create component in components/{name}/
├── Used only in one template?    → Use template partial (_name.html) or {% include %}
└── Exists already?               → Reuse, extend via slots or add variant

Component has one visual form?    → Use template_name = 'name/name.html'
Component has multiple variants?  → Use get_template_name() with style dict

Needs caller-injected HTML attrs? → Add {% slot "extra_attrs" %}{% endslot %}
Needs caller-injected content?    → Add {% slot "content" %}{% endslot %}
Content is mandatory?             → Add required: {% slot "content" required %}{% endslot %}

Needs interactivity?              → Alpine.js x-data="globalComponent"
Needs server communication?       → HTMX attrs via extra_attrs slot
Needs styling?                    → Tailwind classes, BEM class maps in Python
```

---

## Code Examples

### Example 1: Simple Component (Badge)

**`components/badge/badge.py`**
```python
from django_components import component


@component.register('badge')
class Badge(component.Component):
    template_name = 'badge/badge.html'

    def get_context_data(self, text, **extras):
        color_list = {
            'primary': 'badge--primary',
            'green': 'badge--green',
            'red': 'badge--red',
        }
        color_class = color_list.get(extras.get('color'), color_list['primary'])

        return {
            'text': text,
            'final_class': f'badge {color_class} {extras.get("extra_class", "")}',
        }
```

**`components/badge/badge.html`**
```html
<span class="{{ final_class }}"
      {% slot "extra_attrs" %}{% endslot %}>
    {{ text }}
</span>
```

**Usage in template:**
```html
{% component "badge" text="Activo" color="green" %}
{% endcomponent %}
```

### Example 2: Component with Required Slot (Tabs)

**`components/tabs_slider/tabs_slider.py`**
```python
from django_components import component


@component.register('tabs_slider')
class TabsSlider(component.Component):
    template_name = 'tabs_slider/tabs_slider.html'
```

**`components/tabs_slider/tabs_slider.html`**
```html
<div class="tab-nav" x-data="tabsSlider" x-cloak>
    <div class="tab-nav__container">
        {% slot "nav_detail" required %}
        {% endslot %}
    </div>
    <div class="tab-nav__actions">
        {% slot "nav_actions" %}
        {% endslot %}
    </div>
</div>
```

### Example 3: Component Wrapping a Django Form Field

**`components/field/field.py`**
```python
from django_components import component


@component.register('field')
class Field(component.Component):
    def get_template_name(self, context):
        template_list = {
            'input': 'field/input.html',
            'select': 'field/select.html',
            'textarea': 'field/textarea.html',
        }
        input_type = context['element'].field.widget.input_type
        return template_list.get(input_type, template_list['input'])

    def get_context_data(self, element, *, show_label=True, **extras):
        element.label = extras.get('label', element.label)
        return {
            'element': element,
            'show_label': show_label,
            'field_class': extras.get('field_class', ''),
        }
```

**Usage in template:**
```html
{% component "field" element=form.first_name %}
{% endcomponent %}

{% component "field" element=form.email label="Correo" field_class="col-span-2" %}
{% endcomponent %}
```

---

## Commands

```bash
bat components/<name>/<name>.py      # Read component class
bat components/<name>/<name>.html    # Read component template
rg "component.*\"<name>\"" --glob "*.html"  # Find all usages of a component
bat config/settings/django_components.py    # Check component dirs config
bat config/django/base.py            # Check template loader & builtins
```

---

## Resources

- **Configuration**: `config/settings/django_components.py` — `COMPONENTS.dirs` points to `components/`
- **Template loader**: `config/django/base.py` — `django_components.template_loader.Loader` in cached loader chain
- **Builtins**: `django_components.templatetags.component_tags` — auto-loaded, no `{% load %}` needed
- **Project docs**: `docs/01-architecture.md` (Frontend Architecture section)
