# bend-window-ref

Export a Bend-owned window's X11 display name and resource ID without transferring ownership.

Validated with Bend 2.0.39 on Linux with X11. JavaScript and unsupported native backends return `ENOTSUP`.
The bridge uses Bend's internal `BendWin` representation, so revalidate it after compiler updates.

## Run the example

Install [Bend](https://bend-lang.com), Clang, and the X11 development headers.
On Debian or Ubuntu, install the native dependencies with `sudo apt-get install clang libx11-dev`.
Run this from a graphical X11 session with `DISPLAY` set:

```sh
git clone https://github.com/aivv73/bend-window-ref.git
cd bend-window-ref
bend examples/export.bend
```

The example opens a 64x48 window, draws an initial frame, exports its reference, then renames the window using the returned owner.
It prints the display name and decimal window ID on separate lines, waits three seconds, and closes the window.
The printed values depend on your X server.

## Use the library

Import the published package from [BendHub](https://hub.bend-lang.com/n/bend-window-ref):

```python
import Base
import bend-window-ref@0.1.0.1/winref.bend as W
```

For local use, keep `winref.bend`, `winref.c`, and `winref.js` together and import the local module:

```python
import Base
import ./winref.bend as W
```

`W.WinRef.export(window)` returns an action of this type:

```python
IO(Window & Result<&1, &1, U32 & String, W.WindowRef>)
```

Use `IO.bind` to receive the window alongside the result. The same affine owner returns on success and failure.
The result contains either `Done{W.X11WindowRef{display, id}}` or `Fail{(code, message)}`.
See [the example](examples/export.bend) for a complete program.

Bend 2.0.39's native window runtime requires event constructors that are omitted when a program only opens and closes a window.
Use `Window.frame` in window programs to include them; the example draws one frame before exporting.

`WindowRef` is copyable data. It owns no resource and cannot recreate a Bend `Window`.
A consumer needs access to the same X server. The reference expires when its owner closes the window, and X11 can reuse its ID afterward.
Export synchronizes prior requests without discarding queued events.
The library provides no window discovery, enumeration, or adoption.

## Check the project

```sh
bend PROOF.bend
./scripts/check.sh
```

The integration check also requires Python 3. It opens a separate X11 connection using Python's standard-library `ctypes` module.
It verifies that the exported display and ID resolve to the expected window, including the title changed after export and its 64x48 geometry.

For a headless Linux check, install `xvfb` and `xauth`, then run:

```sh
xvfb-run -a ./scripts/check.sh
```

`LAWS.bend` records the ownership rule and native requirements.
`PROOF.bend` proves the structural rule for returning an affine window beside either result.
It does not prove the foreign C implementation. Compilation and the X11 integration check validate the native bridge separately.
Event preservation, ID reuse, and all error paths still require further runtime validation.
Window effects share Xlib state and run on Bend's IO thread.
CI uses Bend 2.0.39 with a verified release checksum.

## Source and license

Imported from [bend-window-ref 0.1.0.0 on BendHub](https://hub.bend-lang.com/n/bend-window-ref),
package `0x8cc463a65f479c5af6b3080035eb0836`.
The bridge derives from [aivv73/bend at c1b8aae](https://github.com/aivv73/bend/commit/c1b8aae67d49342efe07c0581179f0f1de152bf7).

Licensed under [Apache-2.0](LICENSE). The original source attribution and license are preserved.
