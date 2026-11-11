"""Execute check_x11.py with controlled external APIs, including failure unwinding."""
import contextlib
import ctypes as c
import ctypes.util
import io
import json
import runpy
import subprocess
import sys
from unittest.mock import patch


def check(source, scenario):
    events = []
    resources = {"display": False, "name": False, "child": "running"}
    class Function:
        def __init__(self, fn): self.fn = fn
        def __call__(self, *args): return self.fn(*args)
    class Stream(io.StringIO):
        def readline(self, *args):
            events.append('readline')
            return super().readline(*args)
    class Child:
        stdout = Stream(':fixture\n' + ('bad' if scenario == 'parse' else '7') + '\n')
        def __enter__(self): events.append('spawn'); return self
        def __exit__(self, *args):
            # Popen.__exit__ also waits. A live child in an error case would hang.
            self.wait()
        def poll(self): return 0 if resources['child'] == 'reaped' else None
        def kill(self): events.append('kill'); resources['child'] = 'killed'
        def wait(self, timeout=None):
            events.append('wait' if timeout is None else 'timed-wait')
            if scenario == 'timeout' and timeout is not None:
                raise subprocess.TimeoutExpired('fixture', timeout)
            if resources['child'] == 'running' and scenario not in {'success', 'exit-code'}:
                raise AssertionError('unbounded wait on live child: missing kill')
            resources['child'] = 'reaped'
            return 1 if scenario == 'exit-code' else 0
    title = c.create_string_buffer(b'wrong' if scenario == 'title' else b'Window reference exported')
    def open_display(*args):
        events.append('connect')
        resources['display'] = scenario != 'connect'
        return 123 if resources['display'] else 0
    def fetch(display, xid, pointer):
        events.append('fetch-name')
        assert resources['display'] and xid == 7
        if scenario == 'fetch': return 0
        pointer._obj.value = c.addressof(title)
        resources['name'] = True
        return 1
    def free(*args): events.append('free-name'); resources['name'] = False
    def geometry(*args):
        events.append('geometry')
        assert resources['display'] and not resources['name']
        args[5]._obj.value = 64
        args[6]._obj.value = 47 if scenario == 'geometry-size' else 48
        return 0 if scenario == 'geometry' else 1
    def close(*args): events.append('disconnect'); resources['display'] = False
    class Xlib: pass
    xlib = Xlib()
    for name, fn in [('XOpenDisplay', open_display), ('XFetchName', fetch), ('XFree', free), ('XGetGeometry', geometry), ('XCloseDisplay', close)]:
        setattr(xlib, name, Function(fn))
    error = None
    with patch.object(c, 'CDLL', return_value=xlib), patch.object(ctypes.util, 'find_library', return_value='fixture'), patch.object(subprocess, 'Popen', return_value=Child()), patch.object(sys, 'argv', [str(source), 'fixture']), contextlib.redirect_stdout(io.StringIO()):
        try: runpy.run_path(str(source), run_name='__main__')
        except (AssertionError, ValueError, subprocess.TimeoutExpired) as exc: error = type(exc).__name__
    assert len(events) > 2 and events[0] == 'spawn', events
    assert resources == {'display': False, 'name': False, 'child': 'reaped'}, (scenario, resources, events)
    assert (error is None) == (scenario == 'success'), (scenario, error)
    if scenario == 'success':
        assert events.index('free-name') < events.index('disconnect') < events.index('timed-wait')
    print(json.dumps({'scenario': scenario, 'events': events, 'error': error}))

if __name__ == '__main__':
    for scenario in ['success','parse','connect','fetch','title','geometry','geometry-size','timeout','exit-code']:
        check(sys.argv[1], scenario)
