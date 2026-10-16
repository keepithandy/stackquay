# API reference

Base path: `/api/v1/`. Send JSON with `Content-Type: application/json`. Paths end in `/`; always include the slash for write requests. Interactive documentation is at `/api/docs/`, and the committed [OpenAPI schema](openapi.yaml) can be imported into API clients.

## Authentication

Login accepts a username and password. The response contains an opaque token, its expiry, and the user profile:

```json
{
  "token": "<returned-once>",
  "expires_at": "2026-10-23T12:00:00Z",
  "user": {
    "id": 1, "username": "sam", "email": "sam@example.com",
    "first_name": "", "last_name": "", "date_joined": "2026-10-16T12:00:00Z"
  }
}
```

Send it on subsequent requests:

```http
Authorization: Bearer <returned-once>
```

Store the token securely in your client. It expires after `TOKEN_TTL_HOURS` (default 168). There is no refresh-token flow: log in again after expiry. At most 20 tokens are retained per user; a new login evicts the oldest beyond that limit. Logout revokes the current token. Password change/reset revokes all tokens. Disabling a user also revokes tokens.

API authentication uses bearer tokens. Admin authentication uses its own CSRF-protected session cookie. An admin browser cookie does not authenticate API calls.

## Account endpoints

All paths below begin with `/api/v1/auth/`.

| Method / path | JSON fields | Result |
| --- | --- | --- |
| `POST login/` | `username`, `password` | `200` token, expiry, profile; `401` invalid login |
| `POST logout/` | None; bearer required | `204` current token revoked |
| `GET me/` | None; bearer required | `200` profile |
| `PATCH me/` | `first_name`, `last_name`; bearer required | `200` updated profile |
| `POST change-password/` | `current_password`, `password`; bearer required | `200`; all API tokens revoked |
| `POST register/` | `username`, `email`, `password` | `202` generic response; `403` if disabled |
| `POST verify/` | `uid`, `token` from verification email | `200` account activated; `400` invalid link |
| `POST resend-verification/` | `email` | `202` generic response; `403` if signup disabled |
| `POST password-reset/` | `email` | `202` generic response |
| `POST password-reset/confirm/` | `uid`, `token`, `password` | `200` password reset; `400` invalid link |

Password input is limited to 128 characters and must pass Django's validators, including a minimum of 12 characters. Username and email uniqueness is case-insensitive; login uses the exact username spelling. Profile updates cannot change username, email, active status, or privileges. Unknown/read-only profile fields are ignored. Account identity changes are an administrator task in 1.0.

When registration is enabled, new users remain inactive until they confirm their email. Verification and reset tokens expire after one hour. Email links open built-in browser forms, so a client app does not have to build those screens. GET requests do not activate accounts.

Recovery and duplicate-signup responses are generic:

```json
{"detail":"If the account is eligible, an email with next steps has been sent."}
```

## Records

Every API query is scoped to the caller. Guessing another user's UUID returns `404`. Staff and superusers have the same owner scope through the API. Cross-user administration is available only through the admin dashboard with model permissions.

| Method / path | Action |
| --- | --- |
| `GET /api/v1/records/` | Paginated list |
| `POST /api/v1/records/` | Create; returns `201` |
| `GET /api/v1/records/{id}/` | Read |
| `PATCH /api/v1/records/{id}/` | Partial update |
| `PUT /api/v1/records/{id}/` | Replace editable fields; `title` required |
| `DELETE /api/v1/records/{id}/` | Delete; returns `204` |

Editable fields:

```json
{"title":"Trip plan","body":"Optional notes","status":"draft"}
```

- `title`: required, nonblank, at most 200 characters.
- `body`: optional, at most 10,000 characters; default empty string.
- `status`: `draft`, `active`, or `archived`; default `draft`.
- Server-controlled: `id` (UUID), `created_at`, `updated_at`, and owner.

List response:

```json
{"count":1,"next":null,"previous":null,"results":[{"id":"<uuid>","title":"Trip plan","body":"Optional notes","status":"draft","created_at":"2026-10-16T12:00:00Z","updated_at":"2026-10-16T12:00:00Z"}]}
```

Pages contain 25 records. Query parameters:

| Parameter | Example | Behavior |
| --- | --- | --- |
| `page` | `2` | Page number |
| `status` | `active` | Exact status; invalid values return `400` |
| `search` | `trip` | Search title/body |
| `ordering` | `title` or `-updated_at` | Sort by title, created_at, updated_at |

Default order is newest first, then UUID as a tie-breaker. Records are plain text data, not trusted HTML. Escape their contents when displaying them in a frontend. Concurrent edits use last-write-wins behavior; 1.0 does not provide revision history or optimistic locking.

## PowerShell example

```powershell
$login = Invoke-RestMethod -Method Post `
  -Uri 'http://127.0.0.1:8000/api/v1/auth/login/' `
  -ContentType 'application/json' `
  -Body (@{username='your-user'; password='your-password'} | ConvertTo-Json)

$headers = @{Authorization = "Bearer $($login.token)"}
Invoke-RestMethod -Method Post `
  -Uri 'http://127.0.0.1:8000/api/v1/records/' `
  -Headers $headers -ContentType 'application/json' `
  -Body (@{title='First record'; status='active'} | ConvertTo-Json)

Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/records/' -Headers $headers
```

## Errors and limits

Handled API errors share this shape:

```json
{"error":{"status":400,"details":{"title":["This field is required."]}},"request_id":"<uuid>"}
```

`details` can be an object, list, or string depending on the error. The same ID appears in `X-Request-ID` and application request logs. API responses have `Cache-Control: no-store`. Unhandled server errors and unknown non-API routes use a generic plain-text response in production. Proxy-level errors may have their own format.

Status codes: `400` validation, `401` absent/invalid bearer or failed login, `403` permission denied, `404` missing/private object, `405` unsupported method, `415` non-JSON request, `429` rate limited, `500` unexpected failure, `503` dependency not ready.

Auth endpoints: 10/minute/IP. General API: 60/minute anonymous, 300/minute/user. Throttles use shared Redis in production, but are approximate under concurrency. Requests are limited to 1 MB at the supplied proxy; application in-memory upload size is also bounded. CORS is disabled unless allowed origins are configured.

## Health endpoints

`GET /health/live/` returns `{"status":"ok"}` while the process responds. `GET /health/ready/` additionally checks the database and cache, returning `503` and `{"status":"unavailable"}` on failure. These routes are public, exempt from SSL redirection for internal container probes, and disclose no dependency addresses. The public proxy still redirects HTTP to HTTPS.
