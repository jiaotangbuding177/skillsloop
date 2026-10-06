# Variant Matching Runbook

1. Extract every customer constraint from the request and tag each as HARD (must match) or SOFT/PREFERENCE (ordered fallback).
2. Fetch product details and build a candidate list.
3. Filter by HARD constraints first (e.g. unchanged options such as zoom/storage kept identical, direction of change such as lower resolution).
4. Among matches, drop any variant with available == false.
5. Order remaining variants by SOFT preferences (e.g. preferred theme before alternate theme).
6. Present the best match, plus alternatives, and require explicit confirmation.
7. On any write error (e.g. 'Variant not found'), re-read product details to confirm current availability before re-attempting or re-proposing.

Common constraint patterns: larger/smaller size, higher/lower numeric spec, keep other options the same, theme preference order (animal before art), difficulty level preserved, N more/fewer pieces.
