-- Provider-side, schema-verified export template; not executed by researchers.
-- PostgreSQL insight_weaver_prod. Run via authorized read-only connection.
-- Import the exact supplied 1466 IDs into a LOCAL TEMP table (not production state).
-- psql:
-- CREATE TEMP TABLE requested_sessions(session_id text PRIMARY KEY);
-- \copy requested_sessions(session_id) FROM 'session_ids.csv' WITH (FORMAT csv, HEADER true);
-- All SELECT results should be exported as real JSONL, with ISO date strings.
-- Do not mistake stable SQL sort order for true native event order.

SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema='public'
  AND table_name IN ('zclaw_sessions','zclaw_messages','zclaw_agent_instances',
    'enterprise_openclaw_instances',
    'zclaw_chat_bindings','enterprise_memberships','generated_artifacts',
    'skill_inventory_snapshots','skill_usage_events','human_efficiency_events',
    'personal_skill_configs','enterprise_skill_configs','skill_submissions',
    'skill_submission_versions','skill_emergence_observations',
    'skill_emergence_analysis_snapshots','ragflow_datasets','ragflow_documents',
    'ragflow_file_blobs','billing_tasks','billing_task_events',
    'zclaw_enterprise_token_usage_settlements')
ORDER BY table_name, ordinal_position;

-- Keep all original session metadata, including production-only columns.
SELECT s.*, ai.scope, ai."enterpriseId" AS "instanceEnterpriseId",
       ai."enterpriseOpenClawInstanceId", ai."workspacePath", ai."agentDir",
       b."openclawSessionKey", ei."kmAgentBaseUrl"
FROM requested_sessions r
LEFT JOIN zclaw_sessions s ON s.id=r.session_id
LEFT JOIN zclaw_agent_instances ai ON ai.id=s."agentInstanceId"
LEFT JOIN zclaw_chat_bindings b ON b."sessionId"=s.id AND b."isDeleted"=false
LEFT JOIN enterprise_openclaw_instances ei ON ei.id=ai."enterpriseOpenClawInstanceId";
-- No gatewayTokenEncrypted, gateway token or credentials are selected.

-- Complete messages, NOT just user+assistant; failures and retries preserved.
SELECT m.*, s."userId"
FROM requested_sessions r
JOIN zclaw_messages m ON m."sessionId"=r.session_id
JOIN zclaw_sessions s ON s.id=m."sessionId"
WHERE m."isDeleted"=false
ORDER BY m."sessionId", m."createdAt", m.id;

-- Exact per-reference input/output metadata; still not file bytes.
SELECT s."userId", m."sessionId", m.id AS "messageId", m.role,
       m."createdAt", f.ordinality AS "fileIndex", f.value AS "fileMetadata"
FROM requested_sessions r
JOIN zclaw_messages m ON m."sessionId"=r.session_id
JOIN zclaw_sessions s ON s.id=m."sessionId"
CROSS JOIN LATERAL jsonb_array_elements(
  CASE WHEN jsonb_typeof(m."rawPayload"::jsonb->'files')='array'
       THEN m."rawPayload"::jsonb->'files' ELSE '[]'::jsonb END
) WITH ORDINALITY AS f(value,ordinality)
WHERE m."isDeleted"=false;

-- Artifact metadata within known sessions; same paths can have been upserted.
SELECT g.* FROM generated_artifacts g
JOIN requested_sessions r ON r.session_id=g."sessionId";

-- Complementary current-row lookup: a later upsert can overwrite sessionId.
-- psql: CREATE TEMP TABLE requested_file_paths(user_id text, file_path text, source_session_ids text);
-- psql: \copy requested_file_paths FROM 'artifact_path_lookup.csv' WITH (FORMAT csv, HEADER true);
-- psql: \set verified_enterprise_id 'DATA_PROVIDER_CONFIRMED_ENTERPRISE_ID'
-- Run separately for each confirmed, authorized enterprise scope.
SELECT g.*, r.source_session_ids AS "originalReferencedSessions"
FROM generated_artifacts g
JOIN requested_file_paths r ON r.user_id=g."userId" AND r.file_path=g."filePath"
WHERE g."enterpriseId"=:'verified_enterprise_id';
-- Exact-path candidates only: compare user/instance and logged path conventions.
-- A current matching row still cannot prove historical bytes or revisions.

-- Selection events are not file-read/application proof.
SELECT e.* FROM skill_usage_events e
JOIN requested_sessions r ON r.session_id=e."sessionId";
SELECT e.* FROM human_efficiency_events e
JOIN requested_sessions r ON r.session_id=e."sessionId";

-- Cross-session inventories, revisions, RAG and billing require an independently
-- verified enterprise/user/time scope. See data_supply_source_audit.md section 3.
-- No made-up KM internal table names, replyTo/sequence columns, or JSON join keys.
