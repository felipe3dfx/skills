# Hardened security headers — copy/paste per host

Give the author the block for THEIR host. These are safe defaults for a static site. The CSP below is a starting point — if the site embeds YouTube/Spotify/Google Fonts, it already accounts for them; remove what the site does not use.

## Netlify — `netlify.toml` (repo root)

```toml
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"
    Strict-Transport-Security = "max-age=31536000; includeSubDomains"
    Permissions-Policy = "geolocation=(), microphone=(), camera=()"
    Content-Security-Policy = "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; frame-src https://www.youtube-nocookie.com https://open.spotify.com; script-src 'self'"
```

## Netlify (alternative) — `_headers` (in the publish dir)

```
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Permissions-Policy: geolocation=(), microphone=(), camera=()
  Content-Security-Policy: default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self'
```

## Vercel — `vercel.json` (repo root)

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains" },
        { "key": "Permissions-Policy", "value": "geolocation=(), microphone=(), camera=()" },
        { "key": "Content-Security-Policy", "value": "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self'" }
      ]
    }
  ]
}
```

## Cloudflare Pages — `_headers` (in the publish dir)

Same syntax as Netlify's `_headers` block above. Cloudflare Pages reads a root `_headers` file with the identical format.

## GitHub Pages — limitation

GitHub Pages does **not** let you set custom response headers. You cannot add CSP, HSTS, or X-Frame-Options there. If headers matter (the site has login or handles data), move the site behind Cloudflare (free) or to Netlify/Vercel. Tell the author this plainly and escalate to the tech team.

## Notes for the reviewer

- `'unsafe-inline'` in `style-src` is tolerated because static sites often inline styles; avoid it in `script-src` — inline scripts are the main XSS vector.
- If the site has no external embeds, drop the `frame-src`, `fonts.googleapis.com`, and `fonts.gstatic.com` entries for a tighter policy.
- A CSP that breaks the site is worse than none for a non-technical author. Tell them to publish, open the site, and check the browser console for "Content-Security-Policy" errors; loosen only the directive that complains.
