"""Synthetic, offline proof: does no-auto-learn stop stage-2/3 dispatch?"""
import json
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[3]
DEMO = PROJECT / 'enginering/demo'
sys.path[:0] = [str(DEMO), str(DEMO / 'tests')]
from skilldemo.core import Loop
from skilldemo.server import serve
from test_front_stages import StructuredFixture, messages


class OfflineServer:
    def __init__(self, *args, **kwargs):
        pass

    def serve_forever(self):
        time.sleep(2.8)

    def server_close(self):
        pass


def main():
    with tempfile.TemporaryDirectory(prefix='skillsloop-review050-') as root:
        agent = StructuredFixture()
        loop = Loop(root, agent, settle_seconds=0, stage_pipeline=True)
        loop.import_events('alice', messages(), initialization={
            'status': 'KNOWN_NONE', 'basis': 'Synthetic offline review fixture.'})
        with patch('skilldemo.server.ThreadingHTTPServer', OfflineServer):
            serve(loop, port=0, auto_learn=False)
        result = {
            'probe': 'no-auto-learn scheduler with pending synthetic input',
            'externalModelCalls': 0,
            'applicationCodeModified': False,
            'autoLearn': False,
            'observedAgentPurposes': agent.calls,
            'unexpectedFrontStageDispatch': bool(agent.calls),
            'scope': 'Fixture proves scheduler control flow only; no model accuracy claim.'
        }
        destination = Path(__file__).with_name('scheduler-result.json')
        destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
