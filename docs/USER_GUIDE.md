# User and administrator instructions

## Your first administrator

Run `manage.py createsuperuser` using the project environment. Supply a username, email address, and strong password. Open `/admin/` and sign in. There is no built-in default login.

The administrator can manage users, groups, records, and API token revocation. Account passwords are hashed. Raw API tokens are never displayed in the admin dashboard.

## Create an account for someone

In **Users → Add user**, enter the username, email, and a password of at least 12 characters. Save, then review permissions. Normal API users should have **Active** enabled and **Staff status** and **Superuser status** disabled. Accounts created by a trusted administrator are considered verified.

Users log in through your app or the API. This starter supplies an administration interface and account email forms; it does not supply a separate end-user application.

Avoid sending a shared password in a chat. Give the user their username and have them request a password-reset email through your app once SMTP is working.

## Optional public signup

Set `ALLOW_REGISTRATION=1` and restart the application. A new signup remains inactive until its email is verified. The email opens a confirmation page; pressing **Verify account** activates the account. Merely opening a link does not activate it. Links expire after one hour.

The API can resend verification email. Duplicate registrations and recovery requests return a generic response. Disabled, previously verified accounts cannot reactivate themselves using a verification email.

## Work with records

Each record has a title, optional body, and one status: **Draft**, **Active**, or **Archived**. These are simple organization labels; they do not publish records. Data stays private to the owning user through the API.

In the admin dashboard, trusted staff with the appropriate permissions can search records, filter by status/date, change ownership, edit, or delete them. Deleting an account also deletes its records and tokens. Back up first if that data might be needed later.

## Staff permissions

Use **Groups** to assign Django model permissions. For a records editor, grant only the required **Record** view/add/change/delete permissions, then enable the user's **Staff status**. Such staff can manage records across owners in the admin interface.

Keep **User**, **Group**, and **Access token** management permissions for fully trusted administrators. Anyone able to change users or groups can grant powerful access. Do not grant those permissions to ordinary support or content staff. Superusers have unrestricted administration access.

The admin dashboard includes Django's built-in change history for admin actions. API record edits are not recorded in that history.

## Recovery and revocation

- **Forgotten password:** request a reset email from the app/API. The email opens a new-password form. Links expire after one hour and stop working after use.
- **Change password:** supply the current and new passwords through the API. Every API session is revoked and users must log in again.
- **Compromised session:** an administrator can delete one or more entries under **Access tokens**.
- **Disable a user:** clear **Active**. All API tokens are revoked. Re-enable the account manually after resolving the issue.
- **Lost administrator access:** run `manage.py changepassword USERNAME` on the server, or create another superuser with server access.

Normal browser admin sessions use Django's session security. Password changes invalidate other sessions when they are next checked. Public API clients use bearer tokens, not the admin session cookie.

## Login limits

Authentication endpoints and admin login allow 10 requests per minute per source IP. General API limits are 60 requests/minute for anonymous callers and 300/minute for authenticated users. A `429` response includes `Retry-After`.

Several people sharing one internet connection can share an IP limit. These controls are approximate abuse controls, not a defense against a large distributed attack.
