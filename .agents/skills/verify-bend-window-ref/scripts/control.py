#!/usr/bin/env python3
"""Drive the real bend-window-ref example and retain evidence after cleanup."""
import argparse
import ctypes as c
import ctypes.util
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
FEATURES = ('export', 'lifetime', 'javascript')
SOURCE_FILES = ('winref.bend', 'winref.c', 'winref.js', 'examples/export.bend',
                'scripts/check_x11.py', 'verification/probes/live_reference.py')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def xlib():
    library = ctypes.util.find_library('X11')
    require(library, 'libX11 is unavailable; install the X11 runtime and development headers')
    api = c.CDLL(library)
    api.XOpenDisplay.argtypes = [c.c_char_p]
    api.XOpenDisplay.restype = c.c_void_p
    api.XCloseDisplay.argtypes = [c.c_void_p]
    return api


def doctor(xvfb=None, native=True, display=None, server=None):
    """Read-only dependency checks and, after launch, a connection to our display."""
    require(sys.platform == 'linux', 'This driver verifies the supported Linux/X11 backend')
    commands = {name: shutil.which(name) for name in ['bend', 'clang', 'node']}
    if native:
        commands['Xvfb'] = shutil.which(xvfb or os.environ.get('WINREF_XVFB', 'Xvfb'))
    for name, executable in commands.items():
        require(executable, f'{name} is unavailable; install it or pass --xvfb for a local Xvfb executable')
    version = subprocess.check_output([commands['bend'], 'version'], text=True, timeout=5).strip()
    require(version == 'bend 2.0.40', f'Expected bend 2.0.40, got {version}; revalidate the internal BendWin bridge before using another version')
    report = {'ok': True, 'root': str(ROOT), 'bend_version': version, 'commands': commands}
    if native:
        result = subprocess.run([commands['clang'], '-x', 'c', '-fsyntax-only', '-'],
                                input='#include <X11/Xlib.h>\n', text=True, capture_output=True, timeout=5)
        require(result.returncode == 0, 'X11 headers unavailable: ' + result.stderr)
        api = xlib()
        if display is not None:
            require(server is not None and server.poll() is None, 'The Xvfb process started by this run is not alive')
            connection = api.XOpenDisplay(display.encode())
            require(connection, f'Cannot connect to the isolated display {display}')
            api.XCloseDisplay(connection)
            report.update(display=display, xvfb_pid=server.pid, connected=True)
    report['source_sha256'] = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCE_FILES}
    return report


def stop_group(process):
    """Only target a process group created by this helper; never search by name."""
    # Also stop descendants after a parent exits (for example, after a timed-out probe).
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=2)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def command(args, name, evidence, env, records, expected=0, timeout=30):
    argv = [str(arg) for arg in args]
    record = {'action': name, 'argv': argv, 'cwd': str(ROOT), 'expected_exit': expected}
    records.append(record)
    with (evidence/f'{name}.stdout').open('w') as stdout, (evidence/f'{name}.stderr').open('w') as stderr:
        process = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        record['pid'] = process.pid
        try:
            record['exit_code'] = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            record['timed_out'] = True
            raise
        finally:
            stop_group(process)
            record['reaped'] = process.poll() is not None
    require(record['exit_code'] == expected, f'{name}: expected exit {expected}, got {record["exit_code"]}; inspect {evidence/name}.stderr')
    return (evidence/f'{name}.stdout').read_text(), (evidence/f'{name}.stderr').read_text()


def verify(feature, xvfb, destination):
    selected = FEATURES if feature == 'all' else (feature,)
    native = any(name != 'javascript' for name in selected)
    if destination:
        evidence = destination.resolve()
        evidence.mkdir(parents=True, exist_ok=False)
    else:
        parent = ROOT/'verification/results/live'
        parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')
        evidence = Path(tempfile.mkdtemp(prefix=stamp, dir=parent))
    print(f'Evidence: {evidence}', flush=True)
    report = {'requested': list(selected), 'status': 'failed', 'commands': [], 'features': {}, 'cleanup': {}, 'not_covered':['BendHub package installation or published artifact', 'native macOS backend', 'desktop window-manager behavior', 'direct WinRef.export on JavaScript (Window.open fails first)']}
    server = None
    work = None
    server_log = None
    try:
        health = doctor(xvfb, native)
        (evidence/'doctor-before.json').write_text(json.dumps(health, indent=2)+'\n')
        work = tempfile.TemporaryDirectory(prefix='bend-window-ref-drive-')
        scratch = Path(work.name)
        report['scratch'] = str(scratch)
        env = dict(os.environ, TMPDIR=str(scratch))
        # Readiness is checked on a server we started; the caller's DISPLAY is never driven.
        if native:
            server_log = (evidence/'xvfb.stderr').open('w')
            server_args = [health['commands']['Xvfb'], '-displayfd', '1', '-screen', '0', '800x600x24', '-nolisten', 'tcp']
            server = subprocess.Popen(server_args, stdout=subprocess.PIPE, stderr=server_log, start_new_session=True)
            report['xvfb'] = {'pid': server.pid, 'argv': server_args}
            with selectors.DefaultSelector() as selector:
                selector.register(server.stdout, selectors.EVENT_READ)
                require(selector.select(5), 'Xvfb did not announce a display within five seconds')
                number = os.read(server.stdout.fileno(), 128).decode().strip()
            require(number.isdecimal(), 'Xvfb did not return a valid display number; inspect xvfb.stderr')
            env['DISPLAY'] = ':' + number
            health = doctor(xvfb, native, env['DISPLAY'], server)
            (evidence/'doctor-live.json').write_text(json.dumps(health, indent=2)+'\n')
            report['xvfb']['display'] = env['DISPLAY']
        commands = report['commands']
        command(['bend', 'PROOF.bend'], 'proof', evidence, env, commands)
        if 'export' in selected:
            binary = scratch/'export'
            command(['bend', 'examples/export.bend', '-o', binary], 'build-native', evidence, env, commands)
            report['native_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
            output, _ = command([sys.executable, 'scripts/check_x11.py', binary], 'export', evidence, env, commands, timeout=15)
            require("PASS: exported display and ID resolve to the owner's renamed 64x48 window" in output, 'Observer did not confirm the live reference, returned owner, title, and geometry')
            report['features']['export'] = {'entry_points':['compiled native executable'], 'status': 'passed', 'observed_title': 'Window reference exported', 'observed_geometry': [64,48], 'producer_exit': 0, 'evidence': 'export.stdout', 'observations_checked_by': 'scripts/check_x11.py'}
        if 'lifetime' in selected:
            # Reuse the existing real-X11 driver, including its own native compilation.
            output, _ = command([sys.executable, 'verification/probes/live_reference.py', 'examples/export.bend'], 'lifetime', evidence, env, commands, timeout=20)
            observation = json.loads(output.strip().splitlines()[-1])
            require(9 in observation['errors'], 'Expected BadDrawable after the owner closes')
            report['features']['lifetime'] = {'status':'passed' if observation['id_reuse_observed'] else 'incomplete', 'observation':observation, 'reuse_status':'observed' if observation['id_reuse_observed'] else 'not-observed', 'evidence':'lifetime.stdout'}
        if 'javascript' in selected:
            binary = scratch/'export.js'
            command(['bend', 'examples/export.bend', '-o', binary], 'build-javascript', evidence, env, commands)
            report['javascript_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
            output, errors = command(['node', binary], 'javascript', evidence, env, commands, expected=95)
            require(not output.strip() and 'Window.open: no display' in errors, 'Expected the real JS example to report unsupported Window.open without publishing a reference')
            direct_output, direct_errors = command(['bend', 'examples/export.bend'], 'javascript-direct', evidence, env, commands, expected=95)
            require(not direct_output.strip() and 'Window.open: no display' in direct_errors, 'Direct Bend launch unexpectedly differed from the unsupported-window path')
            report['features']['javascript'] = {'entry_points':['compiled JavaScript under Node','bend examples/export.bend'], 'status':'passed', 'expected_failure':'Window.open returns ENOTSUP on Linux', 'exit_code':95, 'evidence':'javascript.stderr', 'export_called':False}
        require(all(item['status'] == 'passed' for item in report['features'].values()), 'reference-reused not observed: this X11 server did not reuse the ID; expiry passed but the mapped reuse journey remains incomplete')
        report['status'] = 'passed'
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        try:
            if server is not None:
                stop_group(server)
                if server.stdout: server.stdout.close()
                report['cleanup']['xvfb_reaped'] = server.poll() is not None
            if server_log is not None: server_log.close()
            if work is not None:
                directory = Path(work.name)
                work.cleanup()
                report['cleanup']['scratch_removed'] = not directory.exists()
        except Exception as cleanup_error:
            report['status'] = 'failed'
            report['cleanup']['error'] = str(cleanup_error)
            raise
        finally:
            (evidence/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
            report['cleanup']['evidence_preserved'] = (evidence/'summary.json').is_file()
            (evidence/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status':report['status'], 'features':list(report['features']), 'evidence':str(evidence), 'cleanup':report['cleanup']}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    inspect = sub.add_parser('doctor', help='read-only dependency/source check; does not start a display')
    inspect.add_argument('--xvfb', help='path to Xvfb if it is not on PATH')
    inspect.add_argument('--javascript-only', action='store_true')
    drive = sub.add_parser('run', help='launch, check readiness, drive, save evidence, and clean up')
    drive.add_argument('feature', choices=['all',*FEATURES], nargs='?', default='all')
    drive.add_argument('--xvfb', help='path to Xvfb if it is not on PATH')
    drive.add_argument('--evidence', type=Path, help='new directory to retain proof; existing directories are refused')
    args = parser.parse_args()
    if args.action == 'doctor':
        print(json.dumps(doctor(args.xvfb, not args.javascript_only), indent=2))
    else:
        verify(args.feature, args.xvfb, args.evidence)


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f'Received signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
