"""Experimental context reconstruction; no upstream source is modified.

The adapter exposes real pinned role prompts and persistent artifact receipts.
It dispatches no agents, model calls, scheduled runs, or experiment processes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from sibyl.orchestration.constants import PIPELINE_STAGES
from sibyl.orchestration.prompt_loader import load_prompt
from sibyl.evolution import normalize_action_plan

PIN = 'c30c2168843a9dea8404cde4bab639c9ff8fc8b9'
SCHEMA = 'evomind-openclaw-context-adapter-v1'
STAGES = {
    'literature_search': (['literature_researcher'], ['context/literature.md']),
    'idea_debate': (['innovator', 'pragmatist', 'theoretical', 'contrarian', 'interdisciplinary', 'empiricist', 'synthesizer'], ['idea/proposal.md', 'idea/references.json']),
    'planning': (['planner'], ['plan/methodology.md', 'plan/task_plan.json']),
    'pilot_experiments': (['experimenter'], ['exp/results/pilots/summary.json']),
    'idea_validation_decision': (['idea_validation_decision'], ['supervisor/idea_validation_decision.json']),
    'experiment_cycle': (['experimenter'], ['exp/results/full/summary.json']),
    'result_debate': (['comparativist', 'revisionist', 'methodologist', 'result_synthesizer'], ['idea/result_debate/analysis.md']),
    'experiment_decision': (['supervisor_decision'], ['supervisor/experiment_decision.json']),
    'writing_outline': (['outline_writer'], ['writing/outline.md']),
    'writing_sections': (['section_writer'], ['writing/paper.md']),
    'writing_integrate': (['section_critic', 'editor'], ['writing/critique/review.md', 'writing/paper.md']),
    'writing_final_review': (['final_critic'], ['writing/review.md']),
    'writing_latex': (['latex_writer'], ['writing/latex/paper.tex', 'writing/latex/paper.pdf']),
    'review': (['critic', 'supervisor'], ['supervisor/review.json']),
    'reflection': (['reflection'], ['reflection/action_plan.json']),
    'quality_gate': (['supervisor'], ['supervisor/quality_gate.json']),
}
DIRS = ('context', 'idea', 'idea/result_debate', 'plan', 'exp/code', 'exp/results/pilots', 'exp/results/full', 'writing/critique', 'writing/latex', 'logs', 'reflection', 'supervisor')


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def _state(workspace: Path) -> dict:
    path = workspace / 'status.json'
    if not path.exists():
        raise ValueError('Workspace not initialized; run init first.')
    state = json.loads(path.read_text(encoding='utf-8'))
    if state.get('adapter_schema') != SCHEMA:
        raise ValueError('Existing status is not this adapter schema; keep it intact and use a separate workspace.')
    if state['stage'] not in PIPELINE_STAGES:
        raise ValueError('Unknown stage in status.json')
    return state


def _relative(workspace: Path, raw: str) -> Path:
    candidate = (workspace / raw).resolve()
    if not candidate.is_relative_to(workspace.resolve()):
        raise ValueError('Artifact must remain inside its research workspace.')
    return candidate


def initialize(workspace: Path, topic: str) -> dict:
    if not topic.strip():
        raise ValueError('Research topic must be nonempty.')
    if (workspace / 'status.json').exists():
        state = _state(workspace)
        if (workspace / 'topic.txt').read_text(encoding='utf-8') != topic:
            raise ValueError('Existing workspace has a different topic; choose another workspace.')
        return {'status': 'existing', 'workspace': str(workspace), 'state': state}
    for folder in DIRS:
        (workspace / folder).mkdir(parents=True, exist_ok=True)
    (workspace / 'topic.txt').write_text(topic, encoding='utf-8')
    state = {'adapter_schema': SCHEMA, 'upstream_commit': PIN, 'stage': 'literature_search', 'iteration': 0, 'created_at': time.time(), 'updated_at': time.time(), 'completed': [], 'paused': False, 'stop_requested': False}
    _write(workspace / 'status.json', state)
    return {'status': 'initialized', 'workspace': str(workspace), 'state': state, 'research_executed': False}


def status(workspace: Path) -> dict:
    state = _state(workspace)
    required = STAGES.get(state['stage'], ([], []))[1]
    missing = [rel for rel in required if not (workspace / rel).is_file() or not (workspace / rel).stat().st_size]
    return {'workspace': str(workspace), 'state': state, 'required_artifacts': required, 'missing_artifacts': missing, 'historical_original_version_verified': False}


def next_action(workspace: Path) -> dict:
    view = status(workspace)
    state = view['state']
    if state['paused'] or state['stop_requested']:
        return {**view, 'action': 'stopped', 'roles': []}
    if state['stage'] == 'done':
        return {**view, 'action': 'done', 'roles': [], 'task_correctness_verified': False}
    roles = []
    for name in STAGES[state['stage']][0]:
        prompt = load_prompt(name, overlay_content='', workspace_path=workspace)
        if not prompt.strip():
            raise ValueError(f'Pinned upstream role prompt missing: {name}')
        roles.append({'name': name, 'upstream_commit': PIN, 'prompt': prompt})
    return {**view, 'action': 'execute_stage_with_available_actor_tools', 'topic': (workspace / 'topic.txt').read_text(encoding='utf-8'), 'roles': roles, 'automatically_dispatched_agents': 0, 'stage_routing_provenance': 'context_reconstructed_adapter_using_pinned_upstream_prompts'}


def record(workspace: Path, stage: str, artifacts: list[str]) -> dict:
    state = _state(workspace)
    if state['paused'] or state['stop_requested']:
        raise ValueError('Workspace is paused or stopped; no implicit resume.')
    if stage != state['stage'] or stage not in STAGES:
        raise ValueError('Record stage must equal the current active stage.')
    expected = STAGES[stage][1]
    paths = {_relative(workspace, rel).relative_to(workspace).as_posix(): _relative(workspace, rel) for rel in artifacts}
    if set(expected) - paths.keys():
        raise ValueError('Missing declared stage artifacts: ' + ', '.join(sorted(set(expected) - paths.keys())))
    receipts = []
    for rel, path in paths.items():
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'Artifact missing or empty: {rel}')
        data = path.read_bytes()
        if path.suffix.lower() == '.json':
            payload = json.loads(data)
            if not payload:
                raise ValueError(f'Empty structured artifact: {rel}')
        receipts.append({'path': rel, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    following = PIPELINE_STAGES[PIPELINE_STAGES.index(stage) + 1]
    if stage in {'idea_validation_decision', 'experiment_decision', 'quality_gate'}:
        payload = json.loads(paths[expected[0]].read_text(encoding='utf-8'))
        decision = str(payload.get('decision', '')).upper()
        allowed = {'ADVANCE', 'REFINE', 'PIVOT'} if stage == 'idea_validation_decision' else {'PROCEED', 'PIVOT'} if stage == 'experiment_decision' else {'DONE', 'ITERATE'}
        if decision not in allowed:
            raise ValueError(f'Decision stage requires decision in {sorted(allowed)}.')
        if decision in {'PIVOT', 'REFINE'}:
            following = 'idea_debate'
        if decision == 'ITERATE':
            following = 'literature_search'
            state['iteration'] += 1
    entry = {'stage': stage, 'recorded_at': time.time(), 'artifacts': receipts, 'following_stage': following, 'semantic_correctness_verified': False}
    (workspace / 'logs').mkdir(parents=True, exist_ok=True)
    with (workspace / 'logs' / 'stage_receipts.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + '\n')
    state['completed'].append(entry)
    state.update(stage=following, updated_at=time.time())
    _write(workspace / 'status.json', state)
    return {'status': 'recorded', 'state': state, 'receipt': entry, 'model_executed_by_adapter': False}


def evolve(workspace: Path) -> dict:
    state = _state(workspace)
    if state['paused'] or state['stop_requested']:
        raise ValueError('Workspace is paused or stopped; no implicit evolution.')
    path = workspace / 'reflection' / 'action_plan.json'
    if not path.is_file() or not path.stat().st_size:
        raise ValueError('Evolution requires the actual current reflection/action_plan.json.')
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict) or not any(data.get(k) for k in ('issues_classified', 'success_patterns', 'recommended_focus', 'systemic_patterns')):
        raise ValueError('Reflection must contain actual issues, patterns, or recommended focus.')
    proposal = normalize_action_plan(data)
    receipt = {'upstream_commit': PIN, 'source_path': 'reflection/action_plan.json', 'source_sha256': hashlib.sha256(raw).hexdigest(), 'normalized_action_plan': proposal, 'evolution_applied': False, 'skill_or_prompt_modified': False, 'scope': 'prepare_current_workspace_reflection_candidates', 'created_at': time.time()}
    _write(workspace / 'logs' / 'evolution_inputs.json', receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    for name in ('init', 'status', 'next', 'record', 'evolve'):
        sub = subs.add_parser(name)
        sub.add_argument('--workspace', required=True)
        if name == 'init':
            group = sub.add_mutually_exclusive_group(required=True)
            group.add_argument('--topic')
            group.add_argument('--topic-file')
        if name == 'record':
            sub.add_argument('--stage', required=True)
            sub.add_argument('--artifact', action='append', default=[])
    args = parser.parse_args(argv)
    workspace = Path(args.workspace).expanduser().resolve()
    try:
        if args.command == 'init':
            topic = Path(args.topic_file).read_text(encoding='utf-8') if args.topic_file else args.topic
            result = initialize(workspace, topic)
        elif args.command == 'status':
            result = status(workspace)
        elif args.command == 'next':
            result = next_action(workspace)
        elif args.command == 'record':
            result = record(workspace, args.stage, args.artifact)
        else:
            result = evolve(workspace)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'error', 'message': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
