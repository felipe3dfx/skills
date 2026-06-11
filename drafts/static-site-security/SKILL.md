---
name: static-site-security
description: "Trigger: valida seguridad, validar seguridad, revisá seguridad, security check, is my site secure. Advisory security review of a static website's files for a non-technical author."
metadata:
  version: "1.0"
---

## Activation Contract

Run when the user asks to validate the security of the static site they are building — "valida seguridad", "revisá seguridad", "security check", "is my site secure", or equivalent. The audience is **non-technical**: a person using AI to build and publish a static website. Speak to them as a technical colleague would — name the problem, explain why it matters in one plain sentence, tell them exactly what to do.

This is an **advisory** skill. It reviews and reports. It does not edit files or change hosting config unless the user explicitly asks afterward.

## Hard Rules

- **Detect, do not eyeball.** A checklist gives consistency, not detection. For every pattern-based check, run the native search tool (Grep/ripgrep) with the explicit regexes below across every file. Reading files by eye misses leaks — that is the dangerous failure for a security review.
- **Static sites have a small, specific attack surface.** No backend, no database. Do not invent server-side, SQL, or auth findings that cannot exist here.
- **Detect when it is no longer just static.** If you find serverless functions (`netlify/functions/`, `functions/`, `api/`), auth (login/session/cookies, `credentials: 'include'`), or a database (`.netlify/db`, connection strings), STOP treating it as a pure static site. Run the checklist on the published files anyway, but flag the backend explicitly: its access-control and data-handling logic is OUT of scope for this review, and escalate it to the tech team with emphasis. This is the single most important judgment call — a leaked admin endpoint is worse than any static finding.
- **Declare what you could NOT verify.** Minified/bundled JS, host-level headers, and anything you could not scan go in a mandatory "No pude verificar" section. Silence there creates a false sense of security — worse than no review.
- **Ignore obvious placeholders.** A secret match is only real if it looks like a real value. Skip `.env.example`, and skip placeholder values like `YOUR_API_KEY`, `xxx...`, `changeme`, `<...>`, `example`, or empty assignments. A false positive scares or desensitizes a non-technical author.
- **Respond in the user's language.** Match the language of their request.

## Detection Checklist

Run each check across all `*.html`, `*.js`, `*.css`, `*.json`, config, and hidden files in the workspace.

| # | Check | How to detect |
|---|---|---|
| 1 | **Leaked secrets** (incl. in comments) | Grep: `(api[_-]?key|secret|token|password|passwd)\s*[:=]`, `sk-[A-Za-z0-9]{20,}`, `AKIA[0-9A-Z]{16}`, `AIza[0-9A-Za-z_\-]{35}`, `ghp_[A-Za-z0-9]{36}`, `Bearer\s+[A-Za-z0-9._\-]+`, `-----BEGIN.*PRIVATE KEY-----` |
| 2 | **Files that must not publish** | Find: `.env*`, `.git/`, `*.bak`, `*.sql`, `*.js.map`/`*.css.map` (source maps leak original source), `node_modules/`, `*.key`, `*.pem`. Exclude runtime/cache dirs like `.netlify/`, `.atl/`, `.pi/` — and never flag `*.map` outside JS/CSS (e.g. Postgres `pg_filenode.map` is not a source map) |
| 3 | **Third-party scripts** | Grep `<script src="http`: flag external CDNs without an `integrity=` (SRI) attribute and any non-HTTPS source |
| 4 | **Forms** | Grep `<form`: report the `action=` target — warn if it posts to a third party or over `http://` |
| 5 | **Mixed content** | Grep `http://` in resource URLs (`src=`, `href=` to assets) on an HTTPS site |
| 6 | **Unsafe external links** | Grep `target="_blank"` without `rel="noopener"` (tab-nabbing) |
| 7 | **Security headers** | Cannot live in files — they are host config. Report as "no verificable desde acá" and give the per-host pointer (Netlify `_headers`, Vercel `vercel.json`, Cloudflare, GitHub Pages limits): CSP, HSTS, X-Frame-Options, X-Content-Type-Options |

## Output Contract

Report in the user's language, plain and non-technical. Lead with the verdict.

Tag every finding with a severity so the author knows what to fix first:
- 🔴 **Crítico** — fix before publishing (leaked real secret, published `.env`/`.git`, mixed content on a login page)
- 🟡 **Menor** — worth doing, not urgent (missing a secondary header, tracking iframe)

For every finding, three parts — all required:
- **Qué** — the specific problem, with file and line
- **Por qué importa** — one plain sentence (what an attacker could do)
- **Cómo se arregla** — the concrete step. For missing security headers (#7), give the author the ready-to-paste block from `references/headers.md` for their host

Then two mandatory sections:
- **No pude verificar** — list headers (host config), minified/bundled JS, and anything unscanned. Be explicit; do not imply full coverage.
- **¿Necesitás ayuda?** — closing line offering escalation to the tech team: "Si algo de esto te excede o no sabés cómo aplicarlo, escribile al área de tecnología: it@grupoilao.com."

If nothing is found, say so — but still show the "No pude verificar" section so the clean result is honest about its limits.

## References

- `references/headers.md` — ready-to-paste hardened security-header blocks per host (Netlify, Vercel, Cloudflare Pages, GitHub Pages). Hand the author the block for their host when reporting finding #7.
