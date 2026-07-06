# AGENTS.md — Burp WP (WordPress Scanner)

Context notes for AI agents working on this repo. Keep this up to date as we learn more.

## What this is

A **Jython** Burp Suite extension (`burp_wp.py`) that scans for vulnerable
WordPress plugins/themes using the WPScan Vulnerability Database API. It's a fork
of `kacperszurek/burp_wp`, modernized for WPScan API v3 and repointed to the
`f8al/wordpress-scanner` GitHub repo for auto-update + database downloads.

- **Language: Python 2 / Jython.** Do NOT introduce Python-3-only syntax. The file
  uses `.iteritems()`, `urlparse`, `print_debug`, etc. There is no `python2` in the
  dev environment, so you can't do a local syntax check — edit carefully.
- Runs inside Burp on the **legacy Extender API** (`IBurpExtender`, `callbacks`,
  `helpers`), which in current Burp is a **shim over the Montoya API**.

## The Montoya-shim gotcha (IMPORTANT — likely more of these lurking)

Current Burp implements the deprecated legacy `IBurpExtenderCallbacks` methods on
top of the Montoya API. Some deprecated overloads now **return `null`** instead of
working. Symptom in the debug log:

```
NullPointerException: Cannot invoke
"burp.api.montoya.http.message.responses.HttpResponse.headers()" because "<parameter1>" is null
```

That's `analyzeResponse(null)` — the request call above it silently returned null.

**Bad (deprecated, returns null):**
```python
response = self.callbacks.makeHttpRequest(host, 443, True, request)   # -> null
```

**Good (IHttpService overload, works):**
```python
http_service = self.helpers.buildHttpService(host, port, use_https)
request_response = self.callbacks.makeHttpRequest(http_service, request)
response = request_response.getResponse() if request_response else None
```

Fixed so far (commit pending):
- `_make_http_request_wrapper` (~line 696) — auto-update + `admin_ajax.json` download.
- `api_request` (~line 1078) — the core WPScan v3 vuln lookup.

The readme-fetch path (~line 1037) already used the good overload, which is how we
diagnosed it. **When touching any Burp API call, prefer the non-deprecated
overload and guard for `null` results** — assume other deprecated legacy calls may
be similarly broken and need the same treatment.

## HTTP / update mechanics

- Auto-update + DB come from `raw.githubusercontent.com/f8al/wordpress-scanner/master/...`
  (`version.sig`, `data/admin_ajax.json`, `data/admin_ajax.json.sha512`). All return 200.
- DB downloads are integrity-checked against a `.sha512` sibling file.
- `data/admin_ajax.json` is ~2 MB.
- Releases are signed via `sign_release.sh` using `version_signing_key.pem`
  (gitignored private key — do not commit). `version.sig` is the signed version blob.
- WPScan API v3 base: `https://wpscan.com/api/v3/{type}/{name}`, auth header
  `Authorization: Token token=<api_key>`. Now fronted by Cloudflare, which rejects
  malformed GET-with-body — send an empty body via `buildHttpMessage(headers, None)`.

## Testing reality

Can't run the extension outside Burp/Jython here. Real verification = load in Burp,
click **force update**, and watch the debug log. Ask the user to confirm.
