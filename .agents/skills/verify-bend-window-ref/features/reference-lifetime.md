# Observe reference expiry and possible ID reuse

An exported reference is borrowed data. It resolves while its owner lives, becomes invalid after close, and may later resolve to a different window if X11 reuses the ID.

## Sub-features

- `reference-live` resolves the exported ID from a separate X11 connection.
- `reference-expired` observes lookup failure after the owner exits and closes its window.
- `reference-reused` observes whether a new real window gets the same ID and the old reference then resolves to it.

## How to get to it (user POV)

- Export through the local example, retain the displayed display/ID, and query that ID from an X11 client.
- Query the same ID again after the example finishes.
- Open another window on the same server and compare IDs.

## Driving it with control.py

Preconditions:

- The baseline doctor passes and the helper can create a private Xvfb display.
- No preexisting window or seed data is needed.

- **Read the live reference.** Run `.agents/skills/verify-bend-window-ref/scripts/control.py run lifetime`. The existing live replay builds and runs the actual example, reads its display/ID, and queries it through Xlib.
- **Observe expiry.** Require exit 0 from the example, then lookup failure with X11 error 9 (`BadDrawable`) for the unchanged ID. Read the ordered path and actual ID in `lifetime.stdout`.
- **Observe reuse.** The replay opens a replacement window. If `id_reuse_observed` is true, require the replacement ID to equal the original ID and the old reference to resolve again. If false, report `reference-reused` as not observed; the helper records an incomplete journey and exits 1. Expiry alone does not prove reuse.
- **Retain proof.** Read `summary.json` and `lifetime.stdout` after the private server and temporary builds have been removed.

## Gotchas

- X11 does not promise immediate ID reuse. A missing reuse precondition is a limitation of that run, not permission to claim the reuse journey passed.
- `XGetGeometry` reports `BadDrawable` for an expired window ID. The replay installs a temporary nonfatal error handler in its own process so it can capture that result.
- A reference has no ownership or generation token. Do not use it to recreate a Bend `Window`.
- Xvfb is a real X server without the user's desktop window manager. This journey does not verify desktop compositor behavior.
