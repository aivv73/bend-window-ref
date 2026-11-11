# Run the example on JavaScript

A user can compile the example to JavaScript, but that runtime cannot open the native window. The program must report the unsupported operation and exit without printing a usable reference.

## Sub-features

- `javascript-direct` checks `bend examples/export.bend`, which selects the JavaScript runtime in Bend 2.0.40.
- `javascript-build` compiles the actual local example to JavaScript.
- `javascript-open-unsupported` reports `Window.open: no display` and exits with Linux ENOTSUP (95).
- `javascript-no-reference` emits no display/ID pair on stdout.

## How to get to it (user POV)

- Build with `bend examples/export.bend -o /tmp/winref-export.js`.
- Run the generated file with Node.
- Running `bend examples/export.bend` without native compilation reaches the same unsupported operation.

## Driving it with control.py

Preconditions:

- Linux, Python 3, Bend 2.0.40, Clang, and Node are available.
- `control.py doctor --javascript-only` passes. Xvfb and a display are not needed for this journey.

- **Build and run.** Run `.agents/skills/verify-bend-window-ref/scripts/control.py run javascript`. The helper compiles the actual example and runs it with Node, then invokes `bend examples/export.bend` directly, without replacing effects.
- **Check the result.** Both `javascript.stderr` and `javascript-direct.stderr` must contain `Window.open: no display`. Both stdout files must be empty, and both command records must show expected and actual exit 95. The helper itself exits 0 when this expected failure is verified.
- **Capture evidence.** Retain the build transcript, JavaScript executable hash, stdout, stderr, and `summary.json` after the temporary build directory is removed.

## Gotchas

- `Window.open` fails before `WinRef.export` is called. This journey does not prove direct JavaScript export behavior or owner preservation; use the export-bridge verification skill for that boundary check.
- Native macOS and browser execution are separate surfaces and remain unverified by this Linux Node journey.
- A nonzero exit is only a pass when the expected code and message match and no reference was published.
