"""Replay both unbounded pipe reads against the actual observer and OS pipes."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

for first_line in [False, True]:
    with tempfile.TemporaryDirectory(prefix='winref-silence-') as tmp:
        root = Path(tmp)
        marker = root / 'started'
        child = root / 'silent'
        child.write_text(f'#!{sys.executable}\nimport time\nfrom pathlib import Path\n' + ('print(":fixture", flush=True)\n' if first_line else '') + f'Path({str(marker)!r}).touch()\ntime.sleep(60)\n')
        child.chmod(0o755)
        observer = subprocess.Popen([sys.executable,sys.argv[1],str(child)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            deadline = time.monotonic()+5
            while not marker.exists() and observer.poll() is None and time.monotonic()<deadline:
                time.sleep(.01)
            assert marker.exists(), ('fixture did not start', observer.communicate(timeout=1) if observer.poll() is not None else '')
            try:
                observer.wait(timeout=.3)
                raise AssertionError('observer unexpectedly returned from silent pipe')
            except subprocess.TimeoutExpired:
                print(json.dumps({'finding':'ReadHasDeadline','blocked_on':'id' if first_line else 'display','external_watchdog_required':True}))
        finally:
            os.killpg(observer.pid, signal.SIGKILL)
            observer.communicate(timeout=5)
