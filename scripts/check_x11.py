"""Resolve an exported reference using a separate X11 connection."""
import ctypes as c
import ctypes.util
import subprocess
import sys


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


x11 = c.CDLL(ctypes.util.find_library("X11"))
x11.XOpenDisplay.argtypes = [c.c_char_p]
x11.XOpenDisplay.restype = c.c_void_p
x11.XCloseDisplay.argtypes = [c.c_void_p]
x11.XFetchName.argtypes = [c.c_void_p, c.c_ulong, c.POINTER(c.c_void_p)]
x11.XFree.argtypes = [c.c_void_p]
x11.XGetGeometry.argtypes = [
    c.c_void_p, c.c_ulong, c.POINTER(c.c_ulong),
    c.POINTER(c.c_int), c.POINTER(c.c_int),
    c.POINTER(c.c_uint), c.POINTER(c.c_uint),
    c.POINTER(c.c_uint), c.POINTER(c.c_uint),
]

with subprocess.Popen([sys.argv[1]], stdout=subprocess.PIPE, text=True) as process:
    try:
        display_name = process.stdout.readline().strip()
        window_id = int(process.stdout.readline().strip())
        require(display_name, "Exported display name is empty")
        require(window_id > 0, f"Invalid exported window ID {window_id}")
        display = x11.XOpenDisplay(display_name.encode())
        require(display, f"Cannot connect to exported display {display_name}")
        try:
            name = c.c_void_p()
            fetched = x11.XFetchName(display, window_id, c.byref(name))
            require(fetched, "Cannot fetch exported window title")
            try:
                require(c.string_at(name) == b"Window reference exported",
                        "Unexpected exported window title")
            finally:
                x11.XFree(name)
            root, x, y = c.c_ulong(), c.c_int(), c.c_int()
            width, height, border, depth = (c.c_uint() for _ in range(4))
            geometry = x11.XGetGeometry(
                display, window_id, c.byref(root), c.byref(x), c.byref(y),
                c.byref(width), c.byref(height), c.byref(border), c.byref(depth),
            )
            require(geometry, "Cannot fetch exported window geometry")
            require((width.value, height.value) == (64, 48),
                    f"Unexpected window dimensions: expected 64x48, got {width.value}x{height.value}")
        finally:
            x11.XCloseDisplay(display)
        status = process.wait(timeout=10)
        require(status == 0, f"Window producer exited with status {status}")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
print("PASS: exported display and ID resolve to the owner's renamed 64x48 window")
