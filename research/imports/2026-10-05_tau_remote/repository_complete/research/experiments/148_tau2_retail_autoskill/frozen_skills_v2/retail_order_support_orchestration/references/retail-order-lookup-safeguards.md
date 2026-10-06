# Retail Order Lookup & Write Safeguards

## Identity resolution
- Primary: email-based user lookup.
- Alternate: first name + last name + ZIP lookup.
- If both fail, request an alternative identifier before concluding.

## Order resolution
- Only query order details with a valid order_id (from lookup or user-stated).
- NEVER fabricate or guess order_id / placeholder IDs.

## Eligibility gate
- Check order status (e.g., pending vs. delivered) against the requested modification before offering to proceed.

## Write gate
- Always obtain explicit customer confirmation of the exact changes before any write call.
- Report success only on a successful write tool result; otherwise state the request could not be completed.

## Fallback
- If information is insufficient or the customer declines to share details, explain the gap, offer alternative paths, and do not claim any change was made.