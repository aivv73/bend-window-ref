# Export a reference and keep using its owner

A Bend caller exports a display name and window ID, then continues to use the returned window owner. An independent X11 client can resolve the reference while the window lives.

## Sub-features

- `export-native` publishes a reference from the compiled native example.
- `owner-after-export` renames the returned owner to `Window reference exported`.
- `reference-resolves` exposes a 64x48 window on the emitted display with the emitted ID.
- `example-exits` closes and exits successfully after its three-second wait.

## How to get to it (user POV)

- Import the local `winref.bend` and call `W.WinRef.export(window)`; the example demonstrates this public API.
- Build with `bend examples/export.bend -o /tmp/winref-export` and run the resulting executable.

## Driving it with control.py

Preconditions:

- The baseline doctor passes, and Xvfb is installed or configured.
- The helper creates a private display; an existing user display is not required.

- **Export and reuse the owner.** Run `.agents/skills/verify-bend-window-ref/scripts/control.py run export`. The helper builds and drives the real native example, using the native launch path documented in the README.
- **Observe independently.** The existing observer consumes the example's two stdout lines and queries that X11 display/ID. `export.stdout` must confirm the renamed 64x48 window, and the command must exit 0.
- **Capture proof.** Read the printed evidence directory's `summary.json`, the observer transcript, the source hashes, and the live doctor. Require successful cleanup after the short-lived example exits.

## Gotchas

- Running `bend examples/export.bend` directly does not select native execution in Bend 2.0.40. That unsupported path is checked by the JavaScript feature.
- A compile alone proves neither X11 publication nor continued ownership.
- The window title is changed after export. A live success confirms this execution's visibility, not every possible X11 scheduling order.
- The example lives for about three seconds. Never depend on a human clicking it in time.
- `scripts/check_x11.py` has unbounded initial reads; the outer helper imposes a 15-second watchdog and tears down its own process group on failure.
- This journey uses the local checkout, not the independently published BendHub artifact.
