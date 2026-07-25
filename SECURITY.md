# Security Policy

## Threat model

AdityaNet is a **fully static site with no runtime server, no database, no authentication,
and no user input**. Every response is a file produced at build time. This removes entire
classes of vulnerability (injection, SSRF, auth bypass, server RCE) by construction — there
is no server to compromise.

The security posture that remains is about **transport and content isolation**, and it is
enforced in the shipped response headers:

- **Content‑Security‑Policy** — `default-src 'self'`, `script-src 'self'` plus build‑time
  SHA‑256 hashes (no `unsafe-inline`), and no external origins of any kind. A stale or
  missing hash blocks the site's own scripts rather than permitting foreign ones.
- **Strict‑Transport‑Security** with `preload`.
- `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`,
  `Cross-Origin-Opener-Policy` / `Cross-Origin-Resource-Policy: same-origin`, and a
  restrictive `Permissions-Policy`.

These headers are generated from a single source into `_headers`, `vercel.json`, and
`render.yaml`, so they cannot silently diverge between hosts. You can verify them directly:

```bash
curl -sSI https://adityanet-re1t.onrender.com/ | grep -i content-security-policy
```

## Supported versions

The deployed `main` branch is the only supported version. Fixes are applied there and
redeployed.

## Reporting a vulnerability

Please report security issues **privately**, not through public GitHub issues.

- Use **GitHub's private vulnerability reporting** on this repository
  (Security → *Report a vulnerability*), or
- contact the maintainer directly through the account listed on the repository profile.

Please include a description, reproduction steps, and the affected URL or file. We aim to
acknowledge reports promptly and will keep you informed of remediation progress. Because the
site is static, most fixes ship as a rebuild and redeploy.

## Scope

In scope: the served headers and CSP, the build/deploy configuration, and any way to make
the site load or execute content from an origin other than itself.

Out of scope: the absence of features that do not exist (there is no login, no form, no
API). Reports that the site "has no server‑side rate limiting" or similar are not
applicable to a static site.
