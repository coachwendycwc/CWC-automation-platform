# Executive Leadership Lab — Start Here (for Wendy)

This is your plain-language guide to building and editing Lab modules using Claude Code, the same way Module 6 was built. No coding required from you — you direct Claude, Claude does the work.

---

## What's in this folder
- **Modules 2–6** — each is a folder with `slides.html` (the deck), `talking-points.html` (your facilitator script), and worksheets. Module 6 is the newest and the best example.
- **`_MODULE-PLAYBOOK.md`** — the exact process Claude follows to build a module. You don't need to read all of it; Claude does.
- **`_TEMPLATE-OUTLINE.md`** — a blank module skeleton Claude copies to start a new one.
- **`_FOR-WENDY-START-HERE.md`** — this file.

Everything is live on the web at:
`https://coachwendycwc.github.io/CWC-automation-platform/docs/executive-lab/module-N/slides.html`
(swap `module-N` for the module number, e.g. `module-6`).

---

## One-time setup on your computer
1. Install **Claude Code** (Anthropic's coding assistant). Rafael can help with this — it's a one-time install.
2. **Clone this repo** (download a working copy):
   `git clone https://github.com/coachwendycwc/CWC-automation-platform.git`
3. Open Claude Code inside that folder.

That's it. From then on you just talk to Claude.

---

## How to build a NEW module (Modules 7–10 remain)
Open Claude Code in the repo and say, in plain English:

> "Read docs/executive-lab/_MODULE-PLAYBOOK.md, then build Module 7 (Lead and Develop Teams) following it."

Claude will then:
1. **Research the facts** and show you a "source map" — a list of every statistic with its real source. **It will pause and ask you to approve it.** Nothing gets written until you say yes. (This is what guarantees no made-up numbers.)
2. Write the module outline, then generate the slides, talking points, and worksheets from it.
3. Verify everything and show you the result to review.

**Your only jobs:** approve the source map, and review the result. Claude does the building.

---

## How to EDIT an existing module
Just describe the change in plain English, naming the module and slide. Examples:

> "On Module 6, Slide 8, the Latina stat should also mention the 90-per-100 VP number."
>
> "Make Module 4's title slide use the same photo backdrop as Module 6's."

Claude updates the outline first, then regenerates the affected files so the slides and talking points stay matched.

---

## The two rules that keep quality high (Claude enforces these)
1. **Every statistic must have a real, checked source.** Claude verifies each number at its original report — not a Google snippet — and shows you before using it. If it can't verify a number, it cuts it rather than guessing.
2. **Slides and talking points come from ONE outline**, so the script always matches what's on the slide. (This is what stopped the "talking points don't match the slides" problem.)

---

## Publishing (making it live)
When you're happy with a module, tell Claude:

> "Commit and push this to main."

Within a minute or two it's live on the web at the module's URL. To share with clients, send the `slides.html` and worksheet links.

> ⚠️ If you and Rafael are both editing at the same time, coordinate (or work on different modules) to avoid conflicts. When in doubt, ask Claude "is my copy up to date?" before starting — it can pull the latest first.

---

## What's left to build
Modules **7 (Lead and Develop Teams)**, **8 (Lead Difficult Conversations)**, **9 (Get Promoted)**, **10 (Set the Table for Your Future)**.
Optional cleanup: migrate Module 1 into this folder; add the missing worksheets to Module 5-v2; fix a few module titles in the old README.

Questions? Ask Rafael, or just ask Claude — it knows this repo.
