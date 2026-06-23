# Module 6 — Build Your Board of Advisors
## MASTER OUTLINE (single source of truth)

**Program:** CWC Executive Leadership Lab — 10-month program for women of color
**Module 6 (June):** Build Your Board of Advisors
**Slide count:** 22

### HOW THIS FILE WORKS (anti-drift contract)
- This outline is the ONLY source. `slides.html` and `talking-points.html` are both generated FROM it.
- Talking points for Slide N describe EXACTLY the on-slide text for Slide N. They cannot desync because they come from the same row.
- **FACTS:** Only the 7 locked, origin-verified stats below may appear as factual claims. Every other line is framework/teaching with NO numbers.
- Each stat carries its scope label. No group's stat is ever relabeled "all women of color."

---

## LOCKED FACT BASE (origin-verified — nothing else may be stated as fact)

| ID | Fact (verbatim scope) | Inline citation for slide |
|----|----------------------|---------------------------|
| F1 | Per 100 men promoted to manager: 93 women, 82 Asian women & Latinas, 60 Black women | McKinsey & LeanIn, *Women in the Workplace* 2025 |
| F2 | 31% of entry-level women have a sponsor vs 45% of men (all women vs all men — NOT race-specific) | McKinsey & LeanIn, 2025 |
| F2b | Sponsor = "someone other than your direct manager who actively advocates for your career advancement and/or creates opportunities for you" | McKinsey & LeanIn, 2025 (definition) |
| F3 | AAPI women: 80% say bamboo ceiling is real; 65% say advancement isn't equitable; 62% say it hit hardest beyond junior level (scope: investment-management professionals, 600+ respondents) | AAAIM & Backstop, *Beyond the Glass Ceiling* 2022 |
| F4 | "Bamboo ceiling" term coined by Jane Hyun | Jane Hyun, *Breaking the Bamboo Ceiling*, 2005 |
| F5 | Native/AIAN women: 0.4% of executives (scope: U.S. federal sector, FY2020) | EEOC, FY2020 |
| F6 | "Personal Board of Directors" concept popularized by Priscilla Claman | Priscilla Claman, HBR, 2010 |
| F7 | Protégés with a sponsor: men +23%, women +19% more likely to get next promotion | Sylvia Ann Hewlett, *The Sponsor Effect*, 2010 |
| F8 | 59% of Black women have never had an informal interaction with a senior leader at their company | LeanIn, *State of Black Women in Corporate America*, 2020 (read via CNBC quoting report) |
| F9 | Latinas: 74 promoted from entry level to manager per 100 men; 90 to VP per 100 men | LeanIn, *State of Latinas in Corporate America*, 2024 (read PDF) |
| F10 | Latinas: 4.9% of entry-level roles → 1.0% of C-suite ("only 1 percent of C-suite executives are Latina") — steepest representation drop of any group | LeanIn, *State of Latinas in Corporate America*, 2024 (read PDF) |
| F11 | Entry→C-suite: white men's representation +64% while Latinas' declines | LeanIn, *State of Latinas in Corporate America*, 2024 (read PDF) |

**CUT (could not origin-verify — do NOT use):** "24% of Black women get the sponsorship they need," "29% Black women manager advocacy" (B3/B4 — not found at any readable origin). Also still cut: "~2x promotion rate," WOC senior-leader access %.

**DATA-GAP DISCLOSURE (to be honored in the deck, not hidden):** Sponsorship/advancement data is not separately reported for MENA and Pacific Islander women in the sources used. The deck names this gap rather than inventing figures. The Board-of-Advisors framework applies to every woman regardless.

---

## DESIGN (must match docs/executive-lab modules exactly)
- Fonts: Source Serif 4 (headings), Inter (body)
- Tokens: `--primary:#1A1A1A; --accent:#2A7B8C; --accent-warm:#D4A574; --text:#333; --bg:#FAF8F5; --bg-warm:#F5F2ED; --border:#E5E0D8`
- Logo: `https://coachingwomenofcolor.com/logo.webp`
- Slide 1 backdrop: `images/0B1A7916.jpg` (CONFIRMED present — copied from module-4 into module-6/images/ BEFORE referencing, so the ref is never broken). Used behind the dark gradient at low opacity so title text stays readable. All other dark slides remain gradient-only — no further image dependencies.
- Worksheets: vanilla JS, localStorage autosave, print/PDF, responsive (768/480 breakpoints) — same pattern as existing worksheets.

---

# SLIDE-BY-SLIDE

> Format per slide — **HEADLINE** | on-slide text (verbatim) | SPEAKER (talking-points script) | time

### Slide 1 — TITLE (dark)
- **On slide:** "Build Your Board of Advisors" · Module 6 — June · Executive Leadership Lab · CWC logo
- **Speaker:** Welcome back. Today we build the single highest-leverage asset in your career that isn't on your résumé — the people in the room when decisions about you get made. No statistics on this slide; this is the warm open and a breath.
- **Time:** 2–3 min · **Facts:** none

### Slide 2 — WHY THIS MODULE (the gap)
- **On slide:** Headline: "Hard Work Alone Doesn't Open the Next Door." Two stat blocks:
  - "31% of entry-level women have a sponsor — vs 45% of men." *(all women vs all men · McKinsey & LeanIn 2025)*
  - "Per 100 men promoted to manager: 93 women · 82 Asian women & Latinas · 60 Black women." *(McKinsey & LeanIn 2025)*
- **Speaker:** Frame the broken rung. Emphasize F2 is a gender gap (label it honestly), F1 shows the spread across groups — read all three numbers, never collapse them into one. This is structural, not a performance problem.
- **Time:** 4–5 min · **Facts:** F1, F2

### Slide 3 — WHAT YOU'LL GAIN (objectives)
- **On slide:** 4 objectives — (1) Distinguish mentor / sponsor / advocate; (2) Map your current board & find the gaps; (3) Write an outreach + specific ask; (4) Build a system to nurture the relationships.
- **Speaker:** Walk the four deliverables, each tied to a worksheet.
- **Time:** 3 min · **Facts:** none

### Slide 4 — THE CORE IDEA: A BOARD, NOT A PERSON
- **On slide:** "Forget the single mentor. Build a board." Note: concept popularized by Priscilla Claman, HBR (2010).
- **Speaker:** Explain why one mentor is fragile; a board diversifies your guidance and advocacy. Attribute the *concept* to Claman (F6); the role taxonomy on the next slides is OUR framework, not hers.
- **Time:** 4 min · **Facts:** F6

### Slide 5 — MENTOR vs SPONSOR vs ADVOCATE (THE TYPES — conceptual)
- **On slide:** Three columns. PURPOSE: teach the DISTINCTION between kinds of relationships (this is the concept; Slide 9 turns it into a roster).
  - MENTOR — advises you (talks TO you)
  - SPONSOR — advocates for you when you're not in the room (talks ABOUT you). On-slide definition: "someone other than your direct manager who actively advocates for your advancement and/or creates opportunities for you." *(McKinsey & LeanIn 2025)*
  - ADVOCATE / CONNECTOR — opens networks, vouches laterally
- **Bridge line on slide (sets up Slide 9):** "These are the *types* of support. Next, we turn them into the specific *seats* on your board."
- **Speaker:** The distinction that changes careers: mentorship is advice; sponsorship is action. Use F2b verbatim. End by teeing up Slide 9: these three types become a five-seat roster.
- **Time:** 5–6 min · **Facts:** F2b
- **NOTE (5 vs 9 overlap resolution — Option A):** Slide 5 = the concept/types. Slide 9 = the roster/seats. The bridge line makes the build explicit so 9 doesn't feel like a repeat.

### Slide 6 — WHY SPONSORSHIP MOVES THE NEEDLE
- **On slide:** "Protégés with a sponsor are more likely to get the next promotion — men +23%, women +19%." *(Hewlett, The Sponsor Effect, 2010)*
- **Speaker:** Sponsorship has a measured promotion effect (F7). Note the gender gap in the benefit itself — women get a real but smaller bump, which is exactly why being deliberate matters.
- **Time:** 4 min · **Facts:** F7

### Slide 7 — QUOTE / REFLECTION
- **On slide:** "The most important conversations about your career happen when you're not in the room. A board makes sure someone in that room is for you." (program voice — NOT attributed to anyone)
- **Speaker:** Pause. Reflection beat. No facts.
- **Time:** 2 min · **Facts:** none

### Slide 8 — THE STEEPEST CLIMBS: BLACK & LATINA WOMEN (Black/Latina focused, per Wendy)
- **On slide:** Headline "The Steepest Climbs: Black & Latina Women." Three cards:
  - CARD 1 — Black Women: "60 promoted to manager per 100 men" + "59% have never had an informal interaction with a senior leader." *(McKinsey & LeanIn 2025; LeanIn State of Black Women 2020)*
  - CARD 2 — Latinas: "74 promoted to manager per 100 men" + "from 4.9% at entry level to just 1% in the C-suite — the steepest drop of any group." *(LeanIn State of Latinas 2024)*
  - CARD 3 — Why a board matters: "When advocacy and senior-leader access are scarcest, building your board deliberately is how you close the gap." (framing, NO stat)
  - Umbrella honesty line (kept): "Other women of color — AAPI, Native, MENA, Pacific Islander — face their own distinct barriers; the strategy applies to all."
- **Speaker:** Lead with Black & Latina realities, each stat WITH source. Frame as structural, not personal. Land card 3: scarce advocacy = build it on purpose. Close with the umbrella line so no one is erased.
- **Time:** 5–6 min · **Facts:** F1 (Black 60), F8 (59%), F9 (Latina 74), F10 (4.9%→1%)
- **CHANGED from v1:** was AAPI/Native-led; now Black/Latina-led per Wendy. AAPI/Native/MENA/PI now compressed into the umbrella honesty line rather than carrying the slide. F3/F4/F5 no longer on this slide.

### Slide 9 — WHAT A STRONG BOARD LOOKS LIKE (THE ROSTER — practical; builds on Slide 5)
- **On slide:** Lead-in line: "Now turn those three types into a five-seat roster." 5 seats to fill: The Sponsor · The Skill Mentor · The Insider (reads the politics) · The Connector · The Truth-Teller (peer who's honest with you).
- **Make the NEW seats visible:** tag The Insider and The Truth-Teller as the two seats that go BEYOND the Slide 5 types (Sponsor/Skill Mentor/Connector map back to the three types; Insider + Truth-Teller are additions).
- **Speaker:** Open by explicitly connecting to Slide 5: "We named three types of support. A real board operationalizes them into five seats." Then describe each seat, flag Insider + Truth-Teller as the additions, note one person can hold two seats.
- **Time:** 5 min · **Facts:** none
- **NOTE (5 vs 9 overlap resolution — Option A):** This slide is the ROSTER. The lead-in + "new seats" tagging removes the "didn't I just see this?" feeling.

### Slide 10 — ACTIVITY: MAP YOUR BOARD (Worksheet 1)
- **On slide:** "Open: Advisor Map / Gap Analysis." Instructions to list current people against the 5 seats and circle the empty seats.
- **Speaker:** Pause-the-video activity. Walk through filling it. Empty seats = your outreach targets.
- **Time:** 12–15 min · **Facts:** none

### Slide 11 — SORT YOUR NETWORK (Worksheet 2 intro)
- **On slide:** "Who's a mentor? Who's actually a sponsor?" Most people overcount sponsors.
- **Speaker:** Lead into the Sorter worksheet. Common trap: assuming a friendly senior person is sponsoring you when they're only mentoring.
- **Time:** 4 min · **Facts:** none

### Slide 12 — ACTIVITY: MENTOR/SPONSOR/ADVOCATE SORTER (Worksheet 2)
- **On slide:** "Open: Mentor vs Sponsor vs Advocate Sorter." Sort each named person; mark which relationship to deepen.
- **Speaker:** Activity. The honesty here is the point — name who is NOT yet advocating.
- **Time:** 10–12 min · **Facts:** none

### Slide 13 — FROM MENTOR TO SPONSOR
- **On slide:** How a mentor becomes a sponsor: deliver visible wins, make the ask specific, give them something to advocate for.
- **Speaker:** You don't "get" a sponsor by asking "will you sponsor me." You earn it by making advocacy easy and specific.
- **Time:** 5 min · **Facts:** none

### Slide 14 — THE ASK (framework)
- **On slide:** The Specific Ask formula: Context → Specific request → Why you → Easy out.
- **Speaker:** Walk the 4-part ask. Specific beats vague every time. Connect to Module 3's outreach formula if cohort did it.
- **Time:** 5 min · **Facts:** none

### Slide 15 — ACTIVITY: OUTREACH & ASK SCRIPT (Worksheet 3)
- **On slide:** "Open: Outreach & Ask Script Template." Draft one outreach message + one specific ask for an empty seat.
- **Speaker:** Activity. Use a real empty seat from Worksheet 1.
- **Time:** 10–12 min · **Facts:** none

### Slide 16 — WOC-SPECIFIC STRATEGY
- **On slide:** Named realities + moves: navigate the "prove-it-again" tax with documented wins; build cross-racial AND in-community sponsors; don't mistake visibility for advocacy.
- **Speaker:** Strengths-based, structural framing (matches Module 4 tone). No new stats — reference the verified ones already shown.
- **Time:** 5 min · **Facts:** none (callbacks only)

### Slide 17 — NURTURE THE BOARD (framework)
- **On slide:** A board is a relationship, not a transaction: give value back, stay in regular contact, update them on wins they helped create.
- **Speaker:** The mistake is going silent until you need something. Reciprocity keeps the board alive.
- **Time:** 4 min · **Facts:** none

### Slide 18 — ACTIVITY: NURTURE TRACKER (Worksheet 4)
- **On slide:** "Open: Relationship-Nurture Tracker." Set cadence + a value-back idea per advisor.
- **Speaker:** Activity. Cadence beats intensity.
- **Time:** 8–10 min · **Facts:** none

### Slide 19 — THE 14-DAY BOARD SPRint
- **On slide:** 3 actions: (1) Fill one empty seat's outreach this week; (2) Send one value-back message to an existing advisor; (3) Convert one mentor toward sponsorship with a specific ask.
- **Speaker:** Concrete, time-boxed actions. Mirror the sprint pattern from other modules.
- **Time:** 4 min · **Facts:** none

### Slide 20 — QUOTE / REFLECTION (dark)
- **On slide:** "You are not asking for a favor. You are building the infrastructure your career deserves." (program voice)
- **Speaker:** Reframe the ask from burden to infrastructure. Pause.
- **Time:** 2 min · **Facts:** none

### Slide 21 — KEY TAKEAWAYS
- **On slide:** 5 bullets: board > single mentor; sponsor ≠ mentor; map → spot gaps → fill them; the ask is specific; nurture or it dies.
- **Speaker:** Summarize. Tie each to its worksheet.
- **Time:** 3 min · **Facts:** none

### Slide 22 — HOMEWORK & CLOSE (dark)
- **On slide:** Homework: complete all 4 worksheets; send 1 outreach; book 1 nurture conversation; post your biggest gap in the community. Close: "Build Your Board. Own the Room." CWC logo.
- **Speaker:** Assign homework, preview Module 7, warm close.
- **Time:** 3 min · **Facts:** none

---

## WORKSHEETS (4) — to be generated, same design/JS pattern as existing modules

1. **advisor-map.html** — "Advisor Map / Gap Analysis"
   - 5 seats (Sponsor, Skill Mentor, Insider, Connector, Truth-Teller) × fields: Name / Relationship strength / Empty? → gap list auto-summary.

2. **mentor-sponsor-advocate-sorter.html** — "Mentor vs Sponsor vs Advocate Sorter"
   - Definitions header (sponsor def = F2b verbatim). Rows: person → category (radio: mentor/sponsor/advocate/none-yet) → "deepen this?" → next step.

3. **outreach-ask-script.html** — "Outreach & Ask Script Template"
   - Target seat; 4-part ask builder (Context / Specific request / Why you / Easy out); assembled message textarea; delivery notes.

4. **nurture-tracker.html** — "Relationship-Nurture Tracker"
   - Per-advisor rows: name / cadence (dropdown) / last contact / value-back idea / next touch date.

**No stats appear in worksheets** except the verified sponsor DEFINITION (F2b) as a teaching header in Worksheet 2. Zero numbers invented anywhere.

---

## CITATIONS BLOCK (to appear on a final references line in slides + talking points)
- McKinsey & LeanIn, *Women in the Workplace 2025*
- AAAIM & Backstop, *Beyond the Glass Ceiling* (2022)
- EEOC, *American Indian and Alaska Native Women in the Federal Sector* (FY2020)
- Jane Hyun, *Breaking the Bamboo Ceiling* (2005)
- Priscilla Claman, "Forget Mentors: Employ a Personal Board of Directors," HBR (2010)
- Sylvia Ann Hewlett, *The Sponsor Effect* (2010)
