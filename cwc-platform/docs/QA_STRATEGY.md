# CWC Platform QA Strategy

## Purpose

Define the quality bar for a platform that CWC will use directly in live business operations and later productize for other coaches.

## Quality Principle

Pilot reliability is more important than raw feature volume.

## Team Model

- Wendy validates real business workflows
- Engineering implements and stabilizes platform behavior
- AI-assisted development follows project docs, architecture constraints, and testing expectations

## Testing Pyramid

### Unit Tests
- business logic
- schema validation
- service behavior
- transformation and classification logic

### Integration Tests
- API endpoint behavior
- database persistence
- auth flows
- scheduling logic
- Stripe/Zoom/Fathom/calendar integration boundaries

### End-to-End / Manual Verification
- Wendy pilot workflows
- booking flow
- contract flow
- invoice/payment flow
- client portal flow
- session delivery flow

## Quality Gates

### Must Pass Before Merging Significant Backend Work
- relevant unit/integration coverage for new domain logic
- no syntax/import/runtime errors in touched modules
- no obvious auth or data integrity regressions

### Must Pass Before Wendy Pilot Use
- login works
- dashboard loads
- core client records are accessible
- invoices/contracts work for intended pilot path
- scheduling behaves predictably
- fallback path exists if one module fails

### Must Pass Before White-Label Expansion
- tenant isolation model is defined
- branding/data boundaries are explicit
- key workflows are stable under current CWC usage

## Workflow Cadence

### Daily
- verify active build slice
- review open regressions
- confirm no new blocker for Wendy’s workflows

### Weekly
- review pilot readiness
- review open bugs vs roadmap items
- re-rank backlog using real usage feedback

### Before Releasing New Core Workflow
- test in seeded/local environment
- do manual walkthrough
- verify error states and fallbacks
- confirm docs updated if workflow meaning changed

## Security and Privacy Checks

- auth-protected routes must enforce access correctly
- client-visible assets must respect sharing permissions
- coach-only notes must not leak to client portal
- integration tokens must be stored and used safely
- financial exports must avoid exposing unrelated tenant/user data

## Integration QA Focus

### Scheduling
- multiple connected calendars
- conflict detection
- availability calculation
- primary calendar write-back

### Session Intelligence
- Zoom ingestion
- Fathom notes/transcripts
- client matching
- permission-controlled publishing to client portal

### Finance
- ledger integrity
- export correctness
- reconciliation workflow accuracy

## Pilot Readiness Checklist

- [ ] Wendy login verified
- [ ] active client records loaded
- [ ] booking flow verified
- [ ] contract flow verified
- [ ] invoice flow verified
- [ ] note/task workflow verified
- [ ] fallback process documented
