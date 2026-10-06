# Address-Change Runbook

## Pre-write checklist
- [ ] Identity resolved to a tool-returned user_id (no invented ids).
- [ ] Full target address captured: address1, address2, city, state, country, zip.
- [ ] Scope clarified: account only, or account + all order addresses.
- [ ] Customer explicitly confirmed the exact address string.

## Post-write verification
- [ ] Tool returned the updated user record.
- [ ] Returned address matches the confirmed target field-by-field.
- [ ] Any missing/blank fields disclosed to the customer.

## Fallback identifiers when lookup fails
- email -> alternate zip -> jointly held order id -> escalate.

## Never do
- Fabricate order ids, user ids, or success confirmations.
- Claim a change before the tool result confirms it.
