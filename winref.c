// SPDX-License-Identifier: Apache-2.0
// Adapted from aivv73/bend c1b8aae; Base's window.c defines BendWin.
Term winref_export_run(Env e, Term* f, IoWork* w) {
#if defined(__linux__) && !defined(__OBJC__)
  BendWin* win = (BendWin*)(intptr_t)io_hand_v(f[0]);
  const char* display = DisplayString(win->dpy);
  if (display == NULL || display[0] == 0 || win->win == 0) {
    return io_tup(e, f[0], io_fail(e, EIO,
      "WinRef.export: missing X11 display or window"));
  }
  if (win->win > UINT32_MAX) {
    return io_tup(e, f[0], io_fail(e, EOVERFLOW,
      "WinRef.export: X11 ID exceeds U32"));
  }
  XSync(win->dpy, False);
  Term ref = io_node(e, CID(X11WindowRef),
    io_str(e, display, strlen(display)), (u32)win->win);
  return io_tup(e, f[0], io_done(e, ref));
#else
  return io_tup(e, f[0], io_fail(e, ENOTSUP,
    "WinRef.export: external reference is unavailable on this backend"));
#endif
}

static void __attribute__((constructor)) winref_export_use(void) {
  io_eff(CID(WinRef.export), winref_export_run);
}
