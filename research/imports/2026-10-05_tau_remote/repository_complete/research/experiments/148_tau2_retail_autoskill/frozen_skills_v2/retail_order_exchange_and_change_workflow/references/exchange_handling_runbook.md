# Retail Exchange Handling Runbook

## Required inputs
- Verifiable identifier: name + zip, or email
- Target items + desired replacements (with preferences)
- Order ID or item ID(s)
- Payment method for any price difference

## Identity lookup contract
- Tool args: {first_name, last_name, zip} OR {email}
- Returns: internal customer/user identifier
- On failure: request the alternate identifier and retry once before falling back to guidance mode.

## Eligibility checks (after IDs known)
1. Order/item status (e.g., pending vs. delivered)
2. Item condition and original packaging
3. Stock availability of requested replacements
4. Price difference and payment method
5. If replacement unavailable: return original and place a new order

## Missing-identifier fallback (guidance mode)
1. Check email for order confirmations
2. Log into account to view order history
3. Contact customer service

## Hard rules
- Never invent order/item IDs.
- Never claim completion before a tool returns success.
- Always confirm with the customer before any write/exchange action.
- Always end with a concrete next step.