# Export a Bend-owned window's X11 display name and resource ID without transferring ownership.
# Apache-2.0. Derived from aivv73/bend commit c1b8aae67d49342efe07c0581179f0f1de152bf7.
# Native bridge validated on Bend 2.0.37, Linux/X11. JS and macOS return ENOTSUP.
# BendWin is a runtime internal. Revalidate this bridge after compiler updates.
# Import bend-window-ref@0.1.0.0/winref.bend as W, then call W.WinRef.export(window).
# The same affine owner returns outside Result on success and failure.
# X11WindowRef is copyable data, owns no resource, and cannot recreate a Window.
# XSync publishes prior X11 requests without discarding queued events.
# References require access to the same X server and expire when the owner closes.
# IDs may be reused after close. No discovery, enumeration, or adoption is provided.
# Source: https://github.com/aivv73/bend/commit/c1b8aae67d49342efe07c0581179f0f1de152bf7
import Base

type WindowRef is Data:
  X11WindowRef{display: String, id: U32}

def WinRef.export(window: Window) ->
  IO(Window & Result<&1, &1, U32 & String, WindowRef>):
  import "./winref.c"
  import "./winref.js"
