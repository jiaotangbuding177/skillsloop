# Order Not Found - Handling Runbook

1. Record the exact ID and the error returned by the write tool.
2. Do NOT retry the same ID with the same tool; switch to the read-only details tool.
3. If details also returns not-found:
   - State clearly that the order could not be located.
   - Offer plausible reasons: already processed, already cancelled, or never existed.
   - Ask for an alternative identifier (email, account, another order ID).
4. If details returns a status (e.g. pending/delivered):
   - Pending -> proceed with cancellation using the write tool.
   - Delivered/processed -> explain ineligibility and offer next steps.
5. Never assert that a cancellation completed unless the write tool returned success.
6. Close by asking if anything else is needed.
