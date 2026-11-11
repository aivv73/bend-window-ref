"""Optional live X11 replay: export -> resolve -> owner closes -> BadDrawable."""
import ctypes as c
import ctypes.util
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile

x11 = c.CDLL(ctypes.util.find_library('X11'))
x11.XOpenDisplay.argtypes = [c.c_char_p]
x11.XOpenDisplay.restype = c.c_void_p
x11.XCloseDisplay.argtypes = [c.c_void_p]
x11.XSync.argtypes = [c.c_void_p,c.c_int]
x11.XDefaultRootWindow.argtypes = [c.c_void_p]
x11.XDefaultRootWindow.restype = c.c_ulong
x11.XCreateSimpleWindow.argtypes = [c.c_void_p,c.c_ulong,c.c_int,c.c_int,c.c_uint,c.c_uint,c.c_uint,c.c_ulong,c.c_ulong]
x11.XCreateSimpleWindow.restype = c.c_ulong
x11.XGetGeometry.argtypes = [c.c_void_p,c.c_ulong,c.POINTER(c.c_ulong),c.POINTER(c.c_int),c.POINTER(c.c_int),c.POINTER(c.c_uint),c.POINTER(c.c_uint),c.POINTER(c.c_uint),c.POINTER(c.c_uint)]
class Error(c.Structure):
    _fields_ = [('type',c.c_int),('display',c.c_void_p),('resourceid',c.c_ulong),('serial',c.c_ulong),('error_code',c.c_ubyte),('request_code',c.c_ubyte),('minor_code',c.c_ubyte)]
errors = []
@c.CFUNCTYPE(c.c_int,c.c_void_p,c.POINTER(Error))
def on_error(display,event):
    errors.append(event.contents.error_code)
    return 0
x11.XSetErrorHandler.argtypes = [c.c_void_p]
x11.XSetErrorHandler.restype = c.c_void_p

def geometry(display,xid):
    root,x,y = c.c_ulong(),c.c_int(),c.c_int()
    width,height,border,depth = (c.c_uint() for _ in range(4))
    return x11.XGetGeometry(display,xid,c.byref(root),c.byref(x),c.byref(y),c.byref(width),c.byref(height),c.byref(border),c.byref(depth))

with tempfile.TemporaryDirectory(prefix='winref-live-') as tmp:
    executable = Path(tmp)/'export'
    subprocess.run(['bend',str(Path(sys.argv[1]).resolve()),'-o',str(executable)],check=True)
    with subprocess.Popen([str(executable)],stdout=subprocess.PIPE,stderr=subprocess.PIPE) as child:
        display = None
        old_handler = x11.XSetErrorHandler(on_error)
        try:
            selector = selectors.DefaultSelector()
            selector.register(child.stdout,selectors.EVENT_READ)
            data = b''
            while data.count(b'\n') < 2:
                assert selector.select(5), 'producer did not publish its reference'
                chunk = os.read(child.stdout.fileno(),1024)
                assert chunk, 'producer exited before publishing its reference'
                data += chunk
            selector.close()
            display_name,id_text = data.splitlines()[:2]
            xid = int(id_text)
            display = x11.XOpenDisplay(display_name)
            assert display and geometry(display,xid), 'reference did not resolve while owner was live'
            assert child.wait(timeout=6) == 0
            assert geometry(display,xid) == 0, 'reference unexpectedly remained live after close'
            x11.XSync(display,0)
            assert 9 in errors, ('expected BadDrawable',errors)
            replacement = x11.XOpenDisplay(display_name)
            assert replacement
            try:
                replacement_id = x11.XCreateSimpleWindow(replacement,x11.XDefaultRootWindow(replacement),0,0,32,24,0,0,0)
                x11.XSync(replacement,0)
                reused = replacement_id == xid
                if reused:
                    assert geometry(display,xid), 'reused ID did not resolve to replacement'
                print(json.dumps({'path':['export','resolve live ID','owner closes','same ID produces BadDrawable'],'id':xid,'errors':errors,'replacement_id':replacement_id,'id_reuse_observed':reused}))
            finally:
                x11.XCloseDisplay(replacement)
        finally:
            if display: x11.XCloseDisplay(display)
            x11.XSetErrorHandler(old_handler)
            if child.poll() is None: child.kill(); child.wait()
