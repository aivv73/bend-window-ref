"""Type-check the actual WindowRef declaration, without importing foreign effects."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
source = Path(sys.argv[1]).read_text()
match = re.search(r'^type WindowRef[^\n]*\n(?:[ \t]+[^\n]*\n)+', source, re.M)
if not match:
    raise SystemExit('WindowRef declaration changed; review reference proof extraction')
with tempfile.TemporaryDirectory(prefix='winref-type-') as tmp:
    path = Path(tmp) / 'copy.bend'
    path.write_text('import Base\n\n' + match.group() + '\ndef copy_reference(+ref: WindowRef) -> WindowRef & WindowRef:\n  (ref, ref)\n')
    subprocess.run(['bend',str(path)], check=True)
