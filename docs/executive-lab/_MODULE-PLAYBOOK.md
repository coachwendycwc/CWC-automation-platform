# Executive Leadership Lab — MODULE BUILD PLAYBOOK
### The repeatable process. Follow it in order for every new module. Proven on Module 6 (2026-06).

This playbook exists because the slow, error-prone part of building modules was *rediscovering the process* each time. It's codified here. Each new module = fill in the template, run the gates. The per-module research is the only irreducible work — and it's what guarantees quality.

---

## THE TWO PROBLEMS THIS PROCESS SOLVES
1. **Hallucinated / unsourced stats** in slides + worksheets → fixed by **source-map-first, verify-at-origin**.
2. **Talking points drifting off the slides** → fixed by **one OUTLINE.md driving both files**.

---

## THE 4 GATES (do them in this order — do not skip ahead)

### GATE 1 — SOURCE MAP FIRST (before writing any slide)
- List every spot in the planned module that wants a statistic.
- For EACH: web-search, then **verify at the PRIMARY/origin source** — read the actual report page or PDF, not a search snippet. Snippets paraphrase and mis-attribute.
  - WebFetch first. If blocked (403 / timeout / "domain not safe"), fall back to: `curl -sL -A "<browser UA>" <url>` piped through a python HTML-strip, or download the PDF and `pdftotext`. (Both worked on Module 6 when WebFetch failed.)
  - McKinsey.com hard-blocks curl AND WebFetch — get its stats from a readable secondary that quotes it, or the LeanIn mirror.
- Build a table: **claim → exact number → source (org, title, year) → URL → tier**.
  - **Tier A** = I read the exact figure at origin myself. Safe to use.
  - **Tier B** = consistently attributed but I could NOT read origin. Use ONLY with explicit approval; label honestly.
  - **CUT** = couldn't verify, conflicting, or scope-broken. Does not ship. A plausible guess is the failure, not a shortcut.
- **SCOPE EVERY STAT.** "Women of color" is the FULL umbrella: Black, Latina, Asian/AAPI, Native/AIAN, MENA, Pacific Islander, multiracial. NEVER relabel one group's number as "all WOC." Label each stat's true scope on-slide (e.g. "investment-management professionals," "federal sector FY2020," "all women vs all men"). Uneven coverage is fine. Disclose genuine data gaps; never invent to fill them.

### GATE 2 — RAFAEL/WENDY APPROVE THE SOURCE MAP
- Present the map. Rafael approves which ✅ rows ship and whether any ⚠️ Tier-B rows are allowed.
- Nothing gets written until the facts are signed off. (Cheap check + one generation beats four rewrite passes.)

### GATE 3 — WRITE THE LOCKED OUTLINE (single source of truth)
- Copy `_TEMPLATE-OUTLINE.md` → `module-N/OUTLINE.md`.
- Fill the locked fact table with ONLY approved facts.
- One row per slide: **headline + verbatim on-slide text + speaker script + time + which fact IDs (if any)**.
- Most slides carry NO stat — they're framework/teaching. Only stat-bearing slides cite facts.
- This file is the contract: talking points for Slide N come from Slide N's row → they cannot drift.

### GATE 4 — GENERATE FROM THE OUTLINE, THEN VERIFY
- Generate `slides.html`, `talking-points.html`, and worksheets FROM the outline.
  - Copy any backdrop image into `module-N/images/` BEFORE referencing it (never a bare `images/` ref — that's the Module 2 broken-image bug).
  - References list (last slide + talking-points footer) must contain EXACTLY the sources actually cited — no more, no less. (Module 6 revision caught stale AAAIM/EEOC refs this way.)
- VERIFY with grep + curl, don't assume:
  - file inventory complete; slide count matches; talking-points has Slide 1..N (sync intact)
  - no broken `images/` refs (every ref resolves on disk)
  - every number in slide *content* traces to an approved fact (grep the stats; CSS numbers like padding/60% are noise — check they're inside `<style>`)
  - every inline citation maps to a used stat, and vice versa
  - after deploy: `curl` the live URL until it returns 200 AND contains new content (Pages caches the old version briefly)

---

## CADENCE (Rafael's choice, 2026-06)
**One module at a time. Rafael reviews each before the next.** Full cycle per module: source map → approve → outline → files → browser review → ship. Then move to the next.

---

## DESIGN / TECH CONVENTIONS (match existing docs/executive-lab modules exactly)
- Static HTML, no build step. Deploys via GitHub Pages from `main` at path `/` →
  live at `https://coachwendycwc.github.io/CWC-automation-platform/docs/executive-lab/module-N/<file>.html`
- Fonts: Source Serif 4 (headings) + Inter (body).
- Tokens: `--primary:#1A1A1A; --accent:#2A7B8C (teal); --accent-warm:#D4A574 (gold); --text:#333; --text-light:#666; --text-muted:#999; --bg:#FAF8F5; --bg-warm:#F5F2ED; --border:#E5E0D8`
- Logo: `https://coachingwomenofcolor.com/logo.webp` (use `filter: brightness(0) invert(1)` on dark slides).
- Slides: 21–24, keyboard + touch nav, progress bar, print CSS. Copy module-6/slides.html as the structural base.
- Worksheets: vanilla JS localStorage autosave + print/PDF + responsive (768/480 breakpoints). Copy an existing worksheet as base (save by element `id` AND by class-index for repeating rows).
- Dark slides = gradients. Backdrop images allowed ONLY if copied in first; keep opacity low (~0.18) so text stays readable. NOTE: the CWC photos are ~16MB each — heavy; fine for parity but flag for later optimization.
- Commit messages: **NO Co-Authored-By** (Rafael global pref). Auth as `mdxvision` (collaborator on coachwendycwc repo).
- Ship: branch+PR if Wendy needs to review pre-merge; push-to-main if she's already approved content. Confirm which each time.

---

## MODULE STATUS — SOURCE OF TRUTH IS `_CURRICULUM-2026.md` (NOT the old README)
⚠️ The old README's back-half module list was WRONG. Always build against `_CURRICULUM-2026.md`. It's a **12-month** program (Jan–Dec); Jul–Aug are WORKSHEETS-ONLY summer integration, not live modules.

Built:
- JAN Break Through Career Plateaus — OLD flat folder `cwc-executive-lab/`, NOT migrated
- FEB Strategic Positioning for Promotion — built (module-2)
- MAR Confident Career Pivot — built (module-3)
- APR Leadership Composure — built (module-4)
- MAY Advocacy & Negotiation — built (module-5); v2 "Fortune 500" redesign MISSING its 6 worksheets
- JUN Build Your Board of Advisors — ✅ SHIPPED 2026-06 (module-6, this process)

NOT built (the REAL remaining work):
- **JUL–AUG Summer Integration — WORKSHEETS ONLY** (Board of Advisors Deep Dive + Energy & Cultural Tax Workbook + Mid-Year Reflection + Networking for Introverts + Reciprocity Playbook + Reading List). No live slides/talking-points.
- **SEP Executive Storytelling: Master Your Narrative** (Lane: Value)
- **OCT Inclusive Leadership: Lead Authentically & Build Your Coalition** (Lane: Leadership)
- **NOV Evidence-Based Confidence: From Self-Doubt to Self-Trust** (Lane: Sustainability)
- **DEC Reclaim Your Time: Boundaries, Decisions & Personal Operating System** (Lane: Sustainability)

### Optional cleanup backlog (separate from new builds)
- Migrate Module 1 (January) into docs/
- Add the 6 missing worksheets to module-5-v2 (or reconcile v1/v2)
- Fix the OLD README (it has wrong titles AND a wrong back-half roadmap — `_CURRICULUM-2026.md` supersedes it)
- Confirm folder-naming convention with Rafael before creating Sep–Dec folders (month-number vs sequential)
