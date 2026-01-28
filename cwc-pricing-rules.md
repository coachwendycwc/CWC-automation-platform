# CWC Platform - Pricing Rules Document
## AI Invoice Extraction Reference

> **Purpose:** This document is referenced by the AI when analyzing call transcripts to generate draft invoices. Update this document as your pricing evolves - the AI will learn from your corrections over time.

---

## Service Categories

### 1. DISCOVERY CALLS

| Type | Duration | Price | Notes |
|------|----------|-------|-------|
| Initial Discovery (B2C) | 30-45 min | FREE | Individual coaching prospects |
| Initial Discovery (B2B) | 30-45 min | FREE | Organizational prospects |

**Trigger phrases in transcripts:**
- "discovery call", "intro call", "getting to know you"
- "learn more about your services", "exploring options"

---

### 2. EXECUTIVE COACHING (B2C)

| Package | Sessions | Duration | Price | Payment Terms |
|---------|----------|----------|-------|---------------|
| Executive Leadership Coaching Program | 12 sessions | 6 months | $9,900 total ($1,650/mo) | Paid in full OR monthly at start of each month |
| Leadership Clarity Session | 1 session | 90 min | $697 | Due on booking |
| Executive Coaching Lab | 10 months | Jan-Jun, Sep-Dec | $997 ($100/mo) | Monthly payments |

**Trigger phrases in transcripts:**
- "executive coaching", "leadership development", "career advancement"
- "promotion", "executive presence", "imposter syndrome"
- "1:1 coaching", "individual sessions"
- "leadership coaching", "executive leadership program"

**Included Assessments:**
- DiSC Assessment (included in 6-month program)
- Positive Intelligence Test (included in 6-month program)

**Notes:**
- No single session coaching offered
- No premium for senior executives (VP+)

---

### 3. GROUP COACHING (B2C/B2B)

| Program | Duration | Price | Payment Terms | Notes |
|---------|----------|-------|---------------|-------|
| Executive Coaching Lab | 10 months (Jan-Jun, Sep-Dec) | $997 | $100/month | Group format |

**Trigger phrases in transcripts:**
- "group program", "cohort", "coaching lab"
- "peer learning", "community", "accountability group"

---

### 4. CONSULTING (B2B)

| Type | Rate | Minimum | Notes |
|------|------|---------|-------|
| Hourly Consulting | $350/hr | TBD | Ad-hoc advisory |
| Project-Based | Custom | $5,000+ | Scoped per project |

**Trigger phrases in transcripts:**
- "consulting", "advisory", "strategy session"
- "audit", "assessment", "recommendations"
- "ongoing support", "project"

---

## Services NOT Offered

The following services are **NOT** offered - do not extract invoices for these:
- Life Coaching (personal/non-executive)
- DEI Workshops (currently not offered)
- Keynote Speaking (currently not offered)
- Leadership Development Programs for organizations (currently not offered)

---

## Pricing Modifiers

### Organization Type Adjustments

| Type | Modifier | Notes |
|------|----------|-------|
| Fortune 500 / Enterprise | Standard | No premium currently |
| Mid-Market | Standard | 500-5,000 employees |
| Small Business | Standard | < 500 employees |
| Nonprofit | Standard | No discount currently |
| Education | Standard | No discount currently |
| Government | Standard | No discount currently |

### Volume / Relationship Adjustments

| Scenario | Modifier |
|----------|----------|
| Repeat client | Case by case |
| Multi-service bundle | Case by case |
| Referral | Case by case |

---

## Payment Terms

### Standard Terms

| Client Type | Default Terms |
|-------------|---------------|
| Individual (B2C) | Due on booking OR monthly at start of month |
| Corporate (B2B) | Net 30 (standard) |

### Deposit Requirements

| Service Type | Deposit |
|--------------|---------|
| Coaching Programs | First month payment to hold spot |
| Consulting Projects | TBD |

---

## Invoice Line Item Templates

### For Executive Leadership Coaching Program:
```
Executive Leadership Coaching Program
12 sessions over 6 months
Includes: DiSC Assessment, Positive Intelligence Test
Start Date: [Date]
```

### For Leadership Clarity Session:
```
Leadership Clarity Session
Single 90-minute deep-dive session
Date: [Date]
```

### For Executive Coaching Lab:
```
Executive Coaching Lab - Group Program
10-month program ([Month] - [Month])
Monthly rate: $100/month
```

### For Consulting:
```
Consulting Services - [Description]
[X] hours @ $350/hour
OR
Project-Based: [Scope Description]
```

---

## AI Extraction Rules

### Confidence Thresholds

| Confidence Level | Action |
|------------------|--------|
| High (>85%) | Auto-populate, flag for review |
| Medium (60-85%) | Auto-populate, require confirmation |
| Low (<60%) | Leave blank, request manual input |

### Fields to Extract from Transcripts

1. **Client name/organization** - Look for introductions, company mentions
2. **Service type** - Match trigger phrases above
3. **Package selected** - Executive Leadership, Clarity Session, or Coaching Lab
4. **Timeline** - Start dates, duration discussed
5. **Payment preference** - Monthly vs paid in full

### Key Pricing Signals

- "6 month program" or "12 sessions" → Executive Leadership Coaching Program ($9,900)
- "quick session" or "one session" or "clarity" → Leadership Clarity Session ($697)
- "group" or "lab" or "cohort" → Executive Coaching Lab ($997)
- "consulting" or "project" or "hourly" → Consulting ($350/hr or $5,000+ project)

---

## Quick Reference

**Most Common Services:**
1. Executive Leadership Coaching Program ($9,900)

**Client Mix:**
- B2C (individuals): 50%
- B2B (organizations): 50%

**Average Deal Size:**
- B2C: $9,900
- B2B: $5,000 - $10,000

---

## Notes & Exceptions

<!-- Add any special pricing arrangements, grandfathered clients, or exceptions here -->

```
(No special arrangements currently documented)
```

---

*Last Updated: December 29, 2024*
*Version: 2.0 - Populated with actual pricing*
