# Executive Coaching Deck Design Research & Grade

> Research conducted: January 2025
> Purpose: Guide aesthetic improvements for the CWC Executive Leadership Lab slide deck

---

## Current Deck Grade: A- (Updated from B-)

### Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| **Color Palette** | B | Clean charcoal + teal. Functional but lacks warmth. |
| **Typography** | A- | Source Serif 4 + Inter is solid. Good hierarchy. |
| **White Space** | C+ | Content-heavy slides. Needs more breathing room. |
| **Visual Interest** | C | No imagery, textures, or visual anchors. Too flat. |
| **Layout Balance** | B | Grid-based but dense. Cards feel cramped. |
| **Language/Tone** | A | Strengths-based, empowering, WOC-centered. |
| **Brand Consistency** | B- | Logo present but brand feels generic. |
| **Interactivity** | A | Smooth navigation, keyboard, touch support. |

**Overall: B-** — Functional and professional, but reads as a "template" rather than a premium coaching experience. Needs visual warmth and polish.

---

## What's Working

1. **Typography pairing** — Source Serif 4 (headings) + Inter (body) is executive-appropriate
2. **Language is strengths-based** — "You're Not Stuck. You're Ready to Elevate." leads with empowerment
3. **Structure is clear** — Section labels, numbered features, consistent patterns
4. **Dark title/closing slides** — Creates visual bookends
5. **Navigation UX** — Progress bar, keyboard nav, swipe support all work well

---

## What Needs Improvement

### 1. Visual Flatness (Critical)
**Problem:** Every slide is pure white + text. No visual anchors, imagery, or textural interest.

**Fix Options:**
- Add subtle background textures (paper grain, light geometric patterns)
- Use photography on 2-3 key slides (abstract, professional)
- Add a warm cream/sand background (`#FAF8F5`) instead of pure white
- Use gradient overlays on dark slides for depth

### 2. Color Palette Lacks Warmth
**Problem:** Charcoal + bright teal feels clinical, not coaching-warm.

**Current Palette:**
```css
--primary: #1A1A1A     /* Charcoal - good */
--accent: #3EBCE8      /* Bright teal - too cool */
--bg: #FFFFFF          /* Pure white - cold */
```

**Recommended Palette:**
```css
--primary: #1A1A1A     /* Keep charcoal */
--accent: #2A7B8C      /* Deeper teal - more sophisticated */
--accent-warm: #D4A574 /* Warm gold/sand accent */
--bg: #FAF8F5          /* Warm cream - approachable */
--bg-warm: #F5F2ED     /* Slightly warmer sections */
```

### 3. Density / White Space
**Problem:** Cards and content feel cramped. 6-card grids are overwhelming.

**Fix:**
- Increase card padding (32px → 40px)
- Add more margin between sections
- Consider 2-column max for key frameworks
- Use progressive reveal instead of showing all content at once

### 4. No Emotional Anchors
**Problem:** Quote slide is the only "moment" in the deck. Needs more.

**Fix:**
- Add 1-2 more quote/reflection slides
- Use a subtle background image on title slide
- Add visual metaphors (staircase, path, growth imagery)

### 5. Brand Generic
**Problem:** Aside from logo, nothing says "CWC" or "Executive Leadership Lab"

**Fix:**
- Create consistent accent pattern/graphic element
- Use warmer, more distinctive color palette
- Add custom "ELL" badge or mark for the program

---

## Competitive Analysis

### McKinsey / Bain / BCG
- **Colors:** Navy + white + single accent (often orange or teal)
- **Imagery:** Abstract, professional photography
- **Layout:** Lots of white space, one idea per slide
- **Typography:** Clean sans-serif (Helvetica, Akkurat)

### Harvard Business School Executive Education
- **Colors:** Crimson (#A51C30) + cream (#FAF8F5) + charcoal
- **Imagery:** Campus shots, professional portraits
- **Tone:** Authoritative but aspirational
- **Texture:** Subtle paper textures, elegant borders

### Brené Brown / Major Coaching Brands
- **Colors:** Warmer palettes — sand, terracotta, muted greens
- **Imagery:** Nature metaphors, growth imagery
- **Tone:** Personal, vulnerable, strengths-based
- **Feel:** Premium self-help, not corporate

### Center for Creative Leadership (CCL)
- **Colors:** Navy + warm gold + white
- **Imagery:** Diverse leadership photos
- **Tone:** Research-backed, inclusive
- **Layout:** Clean, modular, well-spaced

---

## Design Recommendations

### Immediate Fixes (Quick Wins)

1. **Swap pure white for warm cream**
   ```css
   --bg: #FAF8F5;  /* Instead of #FFFFFF */
   ```

2. **Deepen the teal accent**
   ```css
   --accent: #2A7B8C;  /* Instead of #3EBCE8 */
   ```

3. **Increase card padding**
   ```css
   .card { padding: 40px; }  /* Instead of 32px */
   ```

4. **Add warm secondary accent for highlights**
   ```css
   --accent-warm: #D4A574;  /* Gold/sand for warmth */
   ```

### Medium-Effort Improvements

1. **Add subtle background texture**
   - Light paper grain or geometric pattern at 3-5% opacity
   - Creates depth without distraction

2. **Add 1-2 slides with photography**
   - Abstract professional imagery (not stock photos of people)
   - Use as section dividers

3. **Add a second quote/reflection slide**
   - Break up dense content
   - Create emotional anchors

4. **Simplify dense slides**
   - 6-card grids → 3-card or 2-column layouts
   - Let content breathe

### Premium Polish (High Effort)

1. **Custom "Executive Leadership Lab" visual mark**
   - Subtle geometric or typographic element
   - Appears as watermark or corner accent

2. **Gradient overlays on dark slides**
   - Subtle depth instead of flat black

3. **Animated transitions between sections**
   - Fade + slight scale on entry
   - Creates more polished feel

4. **Print-optimized PDF version**
   - Separate stylesheet for clean printing

---

## Typography Research

### Recommended Font Pairings for Executive Coaching

| Heading | Body | Vibe |
|---------|------|------|
| **Source Serif 4** | Inter | Current - solid, slightly cool |
| **Crimson Pro** | DM Sans | Warmer, more classic |
| **Playfair Display** | Lato | Elegant, editorial |
| **Cormorant Garamond** | Work Sans | Sophisticated, premium |
| **Libre Baskerville** | Source Sans Pro | Traditional authority |

### Current Choice Assessment
Source Serif 4 + Inter is a good pairing. It's modern and readable. For warmer feel, could swap to Crimson Pro + DM Sans.

---

## Color Psychology for Executive Coaching

| Color | Psychology | Best For |
|-------|------------|----------|
| **Navy/Charcoal** | Authority, trust, professionalism | Primary text, headers |
| **Teal/Deep Blue** | Growth, wisdom, clarity | Accents, CTAs |
| **Gold/Warm Sand** | Excellence, achievement, warmth | Secondary accent |
| **Cream/Off-White** | Approachability, calm, premium | Backgrounds |
| **Muted Green** | Balance, growth, renewal | Nature/growth themes |

### Colors to Avoid
- Bright primary colors (red, yellow, blue) — signal "startup" not "executive"
- Pure white backgrounds — feel clinical
- Neon or saturated tones — unprofessional

---

## Language & Tone for WOC Leaders

### Lead with Strengths
| Instead of... | Use... |
|---------------|--------|
| "Fix your gaps" | "Leverage your strengths" |
| "What's holding you back" | "What's ready to unlock" |
| "You need to..." | "You have the capacity to..." |
| "Career problems" | "Career evolution" |

### Current Deck Language: A
The deck already does this well:
- "You're Not Stuck. You're Ready to Elevate."
- "Transform stagnation into strategic momentum"
- "Break Through" (action) vs "Overcome Obstacles" (deficit)

### Empowerment Framing
- Acknowledge systemic barriers (visibility gap, access problem)
- Frame solutions as agency and strategy
- Use "you" not "one should"
- Balance aspiration with realism

---

## Slide Structure Best Practices

### One Idea Per Slide
The deck has some dense slides (6-card grids). Consider:
- Breaking into 2-3 slides
- Using progressive reveal
- Summarizing in text, detailing in worksheets

### Visual Hierarchy
1. **Section label** — Small, uppercase, accent color
2. **Main headline** — Large serif, high contrast
3. **Supporting text** — Medium sans-serif, lighter gray
4. **Cards/Lists** — Consistent, well-spaced

### Slide Types to Include
- Title slide (dark, impactful)
- Content slides (teaching, frameworks)
- Activity slides (clearly marked with time)
- Quote/reflection slides (breathing room)
- Summary slides (key takeaways)
- Closing slide (dark, forward-looking)

---

## Worksheet Design Principles

### Current Worksheets Grade: B+
Worksheets are clean and functional. Could be warmer.

### Recommendations
1. Match deck's warm cream background
2. Add subtle accent borders or headers
3. Increase form field padding
4. Add "Purpose" callout at top of each worksheet
5. Print-optimize with page break hints

---

## Action Items Summary

### Priority 1 (Do First) ✅ COMPLETE
- [x] Change background from pure white to warm cream (#FAF8F5)
- [x] Deepen teal accent (#3EBCE8 → #2A7B8C)
- [x] Add gold/sand secondary accent (#D4A574)
- [x] Increase card padding (32px → 40px)

### Priority 2 (Next Iteration) ✅ COMPLETE
- [x] Add subtle paper texture to background (3% opacity SVG noise)
- [x] Add 1 more quote/reflection slide (slide 9: "The ceiling you're hitting...")
- [x] Simplify 6-card grids to 2-column layouts
- [x] Match worksheets to new color palette

### Priority 3 (Polish) ✅ COMPLETE
- [x] Add abstract photography to 2-3 slides (title, closing, quote slides via Unsplash)
- [x] Create custom ELL visual mark (subtle watermark on title + closing slides)
- [x] Add gradient depth to dark slides (135deg gradients with photography overlays)
- [x] Create print-optimized CSS (@media print styles added)

---

## Resources

### Free Fonts (Google Fonts)
- [Source Serif 4](https://fonts.google.com/specimen/Source+Serif+4)
- [Crimson Pro](https://fonts.google.com/specimen/Crimson+Pro)
- [Inter](https://fonts.google.com/specimen/Inter)
- [DM Sans](https://fonts.google.com/specimen/DM+Sans)

### Color Tools
- [Coolors](https://coolors.co) — Palette generator
- [Contrast Checker](https://webaim.org/resources/contrastchecker/) — Accessibility

### Photography (Free)
- [Unsplash](https://unsplash.com) — High-quality abstract/professional
- [Pexels](https://pexels.com) — Diverse professional imagery

---

*Last updated: January 2, 2025*
*All priority fixes applied: January 2, 2025*
