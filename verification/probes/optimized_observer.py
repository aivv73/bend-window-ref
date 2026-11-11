#!/usr/bin/env python3
"""Require the real driver to reject wrong geometry under PYTHONOPTIMIZE."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--xvfb', default=os.environ.get('WINREF_XVFB', 'Xvfb'))
parser.add_argument('--out', type=Path, default=ROOT/'verification/results/optimized-observer')
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)

with tempfile.TemporaryDirectory(prefix='winref-wrong-geometry-') as tmp:
    source = Path(tmp)
    files = ['winref.bend', 'winref.c', 'winref.js', 'LAWS.bend', 'PROOF.bend',
             'examples/export.bend', 'scripts/check_x11.py', 'verification/probes/live_reference.py']
    for name in files:
        target = source/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, target)
    example = source/'examples/export.bend'
    original = example.read_text()
    if ', 64, 48)' not in original:
        raise SystemExit('Example geometry changed; review the regression fixture')
    example.write_text(original.replace(', 64, 48)', ', 65, 48)'))
    # The helper runs unchanged against a disposable checkout with a real wrong-sized window.
    driver = ROOT/'.agents/skills/verify-bend-window-ref/scripts/control.py'
    entry = '''import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location('control', sys.argv[1])
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)
control.ROOT = pathlib.Path(sys.argv[2])
control.verify('export', sys.argv[3], pathlib.Path(sys.argv[4]))
'''
    for optimization in ['0', '1', '2']:
        evidence = Path(tempfile.mkdtemp(prefix=f'opt-{optimization}-', dir=args.out.resolve()))
        # verify() owns a fresh evidence directory and refuses an existing one.
        evidence = evidence/'run'
        result = subprocess.run([sys.executable, '-c', entry, str(driver), str(source), args.xvfb, str(evidence)],
                                env=dict(os.environ, PYTHONOPTIMIZE=optimization), capture_output=True, text=True, timeout=25)
        (evidence.parent/'driver.stdout').write_text(result.stdout)
        (evidence.parent/'driver.stderr').write_text(result.stderr)
        report = json.loads((evidence/'summary.json').read_text())
        if result.returncode == 0:
            raise SystemExit(f'FAIL: PYTHONOPTIMIZE={optimization} accepted a real 65x48 window as 64x48; evidence: {evidence}')
        errors = (evidence/'export.stderr').read_text()
        if 'RuntimeError: Unexpected window dimensions: expected 64x48, got 65x48' not in errors:
            raise SystemExit(f'Wrong failure under PYTHONOPTIMIZE={optimization}: {errors}')
        if report['status'] != 'failed' or not all(report['cleanup'].values()):
            raise SystemExit(f'Failure cleanup or evidence preservation broke: {report}')
        print(f'PASS: PYTHONOPTIMIZE={optimization} rejected wrong geometry; evidence: {evidence}', flush=True)
