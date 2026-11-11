"""Run the real shell script with controlled compiler/observer failures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def check(source, failure):
    with tempfile.TemporaryDirectory(prefix='winref-pipeline-') as tmp:
        root = Path(tmp)
        bin_dir = root / 'bin'
        bin_dir.mkdir()
        temp = root / 'temporary'
        temp.mkdir()
        log = root / 'calls.jsonl'
        stub = f'''#!{sys.executable}
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
stage = 'observer' if name == 'python3' else 'proof' if sys.argv[1] == 'PROOF.bend' else 'javascript' if sys.argv[-1].endswith('.js') else 'native'
with open(os.environ['PROBE_LOG'], 'a') as log: log.write(json.dumps(stage)+'\\n')
sys.exit(17 if stage == os.environ['PROBE_FAILURE'] else 0)
'''
        for name in ['bend','python3']:
            path = bin_dir / name
            path.write_text(stub)
            path.chmod(0o755)
        if failure == 'allocate':
            path = bin_dir / 'mktemp'
            path.write_text('#!/bin/sh\nexit 17\n')
            path.chmod(0o755)
        env = dict(os.environ, PATH=str(bin_dir)+os.pathsep+os.environ['PATH'], TMPDIR=str(temp), PROBE_LOG=str(log), PROBE_FAILURE=failure)
        result = subprocess.run(['bash',str(source)], env=env, capture_output=True, text=True, timeout=5)
        stages = [json.loads(line) for line in log.read_text().splitlines()]
        all_stages = ['proof','native','javascript','observer']
        expected = all_stages if failure == 'none' else ['proof'] if failure == 'allocate' else all_stages[:all_stages.index(failure)+1]
        assert stages == expected, (failure, stages, expected)
        assert result.returncode == (0 if failure == 'none' else 17), (failure,result.returncode,result.stderr)
        assert not list(temp.iterdir()), ('temporary build directory leaked',failure)
        print(json.dumps({'scenario':failure,'stages':stages,'cleanup':True}))

if __name__ == '__main__':
    for failure in ['none','proof','allocate','native','javascript','observer']:
        check(Path(sys.argv[1]).resolve(), failure)
