# useEffect Circular Dependency Prevention

## Concept

Prevent infinite loops in React useEffect caused by circular dependencies between effect callbacks and state updates.

## Root Cause

When a useEffect's dependency array contains a **computed value** that depends on state modified **inside the effect itself**, it creates a circular dependency:

```
Effect runs → dispatch(SET_STATE) → state changes → computed dependency recalculates → effect re-runs → loop
```

### Example (Buggy Pattern)
```typescript
// ❌ WRONG: computed value depends on state.messages
const shouldReuse = sessionIdFromQuery === chatSessionId && state.messages.length > 0;

React.useEffect(() => {
  if (shouldReuse) return;
  // ... load session ...
  dispatch({ type: "SET_MESSAGES", payload: messages }); // ← changes state.messages
}, [shouldReuse, ...]); // ← shouldReuse recalculates when state.messages changes
```

## Anti-Patterns

| Pattern | Why It Fails |
|---------|--------------|
| Computed boolean in deps | Recalculates when underlying state changes |
| `chatSessionId` state in deps | `setChatSessionId()` inside effect triggers re-run |
| `state.messages` in deps | `dispatch(SET_MESSAGES)` inside effect triggers re-run |
| Object/array in deps | New reference on every render, even if content unchanged |

## Solutions

### Solution 1: Ref-Based Guard (Recommended)

Use a ref to track loading state. Refs don't trigger re-renders, so they don't cause effect re-runs.

```typescript
// ✅ CORRECT: ref tracks loading state without triggering re-renders
const loadingSessionIdRef = React.useRef<string | null>(null);

React.useEffect(() => {
  // Skip if already loading this session
  if (loadingSessionIdRef.current === sessionIdFromQuery) return;
  
  let alive = true;
  const load = async () => {
    loadingSessionIdRef.current = targetSessionId; // Mark as loading
    try {
      const detail = await getZclawSessionDetailApi(targetSessionId);
      // ... process detail ...
    } finally {
      // Only clear if still our session (prevents race on rapid session switch)
      if (loadingSessionIdRef.current === targetSessionId) {
        loadingSessionIdRef.current = null;
      }
    }
  };
  
  void load();
  return () => { alive = false; };
}, [sessionIdFromQuery]); // Only re-run when URL changes
```

**Key properties:**
- Ref is set **before** API call (synchronous)
- Ref is cleared in `finally` block (always executes)
- Race condition guard: only clear if `loadingSessionIdRef.current === targetSessionId` — prevents stale async completion from clearing another session's claim
- Effect re-runs during loading → guard prevents duplicate API call
- Effect re-runs after loading → guard is cleared, but `canReuse` check prevents reload

### Solution 2: Ref-Based Reuse Check

Replace state-dependent computed values with ref-based checks:

```typescript
// ✅ CORRECT: use refs instead of state for reuse check
const canReuse =
  Boolean(sessionIdFromQuery) &&
  sessionIdFromQuery === currentViewingSessionIdRef.current &&
  (messagesBySessionRef.current[sessionIdFromQuery]?.length ?? 0) > 0;

React.useEffect(() => {
  if (canReuse) return;
  // ... load session ...
}, [sessionIdFromQuery]); // No state dependencies
```

**Key properties:**
- `currentViewingSessionIdRef` is synced via separate effect
- `messagesBySessionRef` is updated during load
- Neither ref change triggers effect re-run

### Solution 3: Stable Dependency Array

Ensure all dependencies are stable (functions wrapped in `useCallback`, values wrapped in `useMemo`):

```typescript
// ✅ CORRECT: all deps are stable
const loadSessions = React.useCallback(async () => { ... }, []);
const syncViewingSessionStreaming = React.useCallback(() => { ... }, []);
const upsertGeneratingSession = React.useCallback((session) => { ... }, [persistGeneratingSessions]);

React.useEffect(() => {
  // ... load session ...
}, [
  dispatch,           // stable (useReducer)
  enabled,            // stable boolean
  isBootstrapping,    // stable boolean
  loadSessions,       // stable (useCallback)
  projectId,          // stable string
  sessionIdFromQuery, // stable string (URL param)
  syncViewingSessionStreaming, // stable (useCallback)
  upsertGeneratingSession,     // stable (useCallback)
]);
```

## Defense in Depth

Combine multiple guards for robustness:

```typescript
React.useEffect(() => {
  if (isBootstrapping) return;
  
  // Guard 1: Reuse check (ref-based)
  const canReuse = sessionIdFromQuery === currentViewingSessionIdRef.current &&
    (messagesBySessionRef.current[sessionIdFromQuery]?.length ?? 0) > 0;
  
  // Guard 2: Loading guard (ref-based)
  if (canReuse || loadingSessionIdRef.current === sessionIdFromQuery) {
    dispatch({ type: "SET_LOADING", payload: false });
    return;
  }
  
  let alive = true;
  const load = async () => {
    loadingSessionIdRef.current = targetSessionId;
    try {
      // ... API call ...
    } finally {
      loadingSessionIdRef.current = null;
    }
  };
  
  void load();
  return () => { alive = false; };
}, [sessionIdFromQuery]); // Minimal, stable deps only
```

## Lessons

- **L-01**: Never put computed values (that depend on effect-internal state changes) in useEffect dependency arrays
- **L-02**: Use refs for tracking transient state (loading, visited) that shouldn't trigger re-renders
- **L-03**: Set loading refs **before** async calls (synchronous), clear in `finally` blocks
- **L-04**: When clearing loading refs in finally, compare against the session ID to prevent stale completions from clearing another session's claim (race condition on rapid navigation)
- **L-05**: If effect must re-run during loading, use sequence numbers or alive flags to abort stale requests
- **L-06**: Test by checking Network tab: only 1 request per session load, no repeated `/api/zclaw/chat/sessions/{id}` calls
- **L-07**: React Strict Mode double-invokes effects in dev — this is normal and shouldn't cause duplicate API calls if guards are correct

## Related Files

- `apps/web/src/components/super-lobster/SuperLobsterPage.tsx` — Main effect with loading guard
- `apps/web/src/context/SuperLobsterContext.tsx` — Reducer and state management
- `apps/web/src/components/zclaw/ZclawChatProvider.tsx` — `upsertGeneratingSession` callback
