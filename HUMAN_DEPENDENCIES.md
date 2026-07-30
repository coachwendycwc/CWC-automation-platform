# Things only a human can do — CWC platform

Everything on this list is blocked on a decision, a credential, or an account
action. None of it can be unblocked by writing code. Ordered by what unblocks
the most.

**Status as of 2026-07-30:** 8 PRs verified locally and merged to `main`.
Nothing is deployed anywhere.

---

## 1. Decide where (or whether) the platform runs — blocks everything downstream

There is **no evidence CWC is deployed**. `DEPLOYMENT.md` is a generic Docker
template, there is no CI/CD workflow, and the only live URLs in the repo are
GitHub Pages for the Executive Lab slides.

Until this is answered, "deploy" has no meaning:
- Is Wendy using the platform live today? If so, **where** — host, provider, how it restarts?
- If not deployed: is standing it up a real goal, and on what timeline?

Everything in section 2 is only relevant once this is answered.

---

## 2. Before any first deploy (do not skip)

### 2a. The migration chain cannot build a database from scratch
Models define **52 tables**; migrations create **34**. These 18 have no
migration anywhere and exist locally only because someone ran `create_all`:

`contractors` · `contractor_payments` · `testimonials` · `client_sessions` ·
`client_notes` · `client_goals` · `client_action_items` · `client_contents` ·
`goal_milestones` · `offboarding_workflows` · `offboarding_templates` ·
`offboarding_activities` · `expenses` · `expense_categories` ·
`recurring_expenses` · `mileage_logs` · `mileage_rates` · `portal_audit_logs`

`alembic upgrade head` on an empty database dies at migration 012
("relation contractors does not exist"). **Pre-existing — not caused by any
recent work.** Someone must decide: write the missing migration (I can, on
request), or accept that new environments are stood up with `create_all`.

Note: the chain is only testable against **Postgres**. SQLite fails even
earlier, at migration 008, on an `ALTER` it does not support.

### 2b. Two changes log people out on deploy — expected, but tell Wendy first
- **Client portal sessions** invalidate (tokens are now hashed at rest). Clients request a fresh magic link.
- **Outstanding password-reset links** stop working, same reason. Users request a new one.

Neither is a bug. Both generate "it stopped working" messages if unannounced.

### 2c. PR #1 cannot be merged as-is
`codex/wendy-booking-platform-upgrades` carries a **parallel migration chain**
reusing numbers 011–017 (booking/calendar series) that collides with the
current chain. It needs renumbering before it can ever land. Decide: renumber
and merge, or close it.

---

## 3. Credentials I do not have

| Needed for | What | Consequence of not having it |
|---|---|---|
| **Zoom recording export** (PR #19) | A Zoom OAuth token on a live account | Feature is **completely unverified** — built against Zoom's published API shape only. Needs one real run before trusting it. |
| **Google OAuth login** | Google client credentials | The OAuth takeover fix (PR #16) is unit-tested but never driven end to end against real Google. |
| **Email delivery** | Gmail SMTP config (`GMAIL_EMAIL`, `GMAIL_APP_PASSWORD`) | Locally, emails are logged instead of sent. Notification/invite/reset emails are untested against a real mailbox. |
| **Daily.co video** (not built) | A Daily.co account + API key | Video work cannot start. Free tier covers current volume. |

---

## 4. Zoom account decisions — ~$960/year at stake

From invoice INV363489384 (Jul 25, 2026): **$94.35/mo** = 3 × Workplace Pro
@ $16.99 **monthly** + **$40 Cloud Recording 200 GB**. Real recording usage is
~340 GB (140 GB over the tier, zero-rated that cycle).

Rafael has said only **one** seat is needed for CWC.

1. **Drop to 1 seat and switch to annual** — $16.99/mo → $14.16/mo, and two fewer seats. Do this in Zoom billing; I will not touch billing.
2. **Cancel the $40/mo storage add-on** — but **export the ~340 GB first**. One Pro seat includes only 10 GB; hitting the cap stops recording, reportedly without a clear warning.
3. **Order matters:** export recordings → reduce seats → cancel storage.

Result: roughly **$1,132/yr → ~$170/yr**.

⚠️ The recording export (PR #19) currently stores **Zoom's download URLs, not
the video files**. Those URLs die when the recording is deleted from Zoom, so
the export **does not yet make deletion safe**. Downloading the media to owned
storage is a follow-up that needs a destination chosen (S3? the existing
Cloudinary account?).

---

## 5. Product decisions waiting on you

- **Video platform.** Daily.co recommended (~$0–30/mo at current volume, branded in-app sessions, recordings by webhook). Only becomes urgent if the branded experience matters. If PHI ever enters the picture, Whereby instead — its BAA is $16.99/mo vs Daily's $500/mo. Full analysis: `VIDEO_PLATFORM_ANALYSIS.md`.
- **Importer presets.** Need **one real HoneyBook export and one real Dubsado export** to validate. Built from vendor help articles; the UI now says so. Procedure: `docs/importer-presets.md`.
- **Fathom.** Does not work with Daily (its bot only joins Zoom/Meet/Teams). If video moves to Daily, session notes come from Daily transcripts through CWC's existing Claude pipeline instead.

---

## 6. Known gaps nobody has decided to fix

- **Anonymous resource-creation / rate limiting** — the public org-assessment intake creates Contact + Organization rows with no throttle (flagged in `auth_gate.py`). Spam/DoS exposure.
- **~23 pre-existing failing tests** — a triaged baseline that predates this work (AI extraction field mismatches, scheduling, subscriptions hitting the real Stripe API with a fake key). Not regressions; nobody has claimed them.
