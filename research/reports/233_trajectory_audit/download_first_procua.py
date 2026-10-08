"""Read one public compressed-shard trajectory, without extracting archive paths."""
import hashlib
import json
import tarfile
import urllib.request
import sys
from pathlib import Path
import zstandard

OUT = Path('/mnt/d/skillloop/research/reports/233_trajectory_audit')
REV = '120de7e954f851c2d24399230367f2b01ff815f9'
URL = f'https://huggingface.co/datasets/nvidia/ProCUA-SFT/resolve/{REV}/shards/procua_sft_00000.tar.zst'

class CountReader:
    def __init__(self, source):
        self.source = source
        self.bytes = 0
    def read(self, n=-1):
        data = self.source.read(n)
        self.bytes += len(data)
        return data

source = open(sys.argv[1], 'rb') if len(sys.argv) > 1 else urllib.request.urlopen(URL, timeout=60)
with source as response:
    counted = CountReader(response)
    with zstandard.ZstdDecompressor().stream_reader(counted) as decoded:
        with tarfile.open(fileobj=decoded, mode='r|') as archive:
            for member in archive:
                if member.isfile() and member.name.endswith('/trajectory.json'):
                    raw = archive.extractfile(member).read()
                    data = json.loads(raw)
                    (OUT / 'procua_first_trajectory.json').write_bytes(raw)
                    evidence = {'source_url': URL, 'revision': REV,
                                'member': member.name, 'downloaded_compressed_bytes': counted.bytes,
                                'trajectory_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                                'top_level_keys': list(data)}
                    (OUT / 'procua_download_evidence.json').write_text(json.dumps(evidence, indent=2))
                    print(json.dumps(evidence))
                    break
            else:
                raise RuntimeError('No trajectory JSON in archive')
