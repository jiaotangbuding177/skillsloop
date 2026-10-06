# Retail Write-Safety Checklist

Before every write tool call, confirm:
- [ ] Customer identity resolved to a user_id (name+zip or email).
- [ ] Order retrieved and confirmed to belong to this user.
- [ ] Order status checked for eligibility (pending vs delivered vs cancelled).
- [ ] order_id / item_ids copied from retrieved data, not invented.
- [ ] Customer gave explicit confirmation of the change.

After every write tool call, confirm:
- [ ] Tool returned a success result (not an error).
- [ ] Only tool-confirmed actions reported to the customer.
- [ ] Any tracking/confirmation number surfaced exactly as returned.
- [ ] On error: report the failed step honestly, keep other actions intact, and retry with corrected identifiers or ask the user.

Never:
- Fabricate order ids or placeholder ids.
- Claim an action completed before a successful tool response.
