# bend-window-ref verification map

This map describes the local library and example as a user reaches them. Read the matching feature before driving it. The real X11 observer and native example are the primary evidence; formal models and mocked-boundary probes are complementary checks.

## Baseline preconditions

- Run from the repository root on Linux with Bend 2.0.40, Clang, Python 3, Node, and X11 development/runtime libraries.
- Install Xvfb or set `WINREF_XVFB` to its executable, as described in the skill.
- Run `scripts/control.py doctor` through its full path in the skill directory.
- Every native run starts its own Xvfb display. Do not point it at an existing desktop.
- No application data, migration, credentials, or seed records are needed.

## Driving conventions

The executable harness is `.agents/skills/verify-bend-window-ref/scripts/control.py`. Its `run` command includes launch, doctor, drive, evidence capture, and teardown. `run all` selects all three local journeys. Evidence defaults to a unique directory under `verification/results/live/`; `--evidence` must name a new directory.

## Proof and coverage

Capture commands, outputs, exit codes, source/build identity, independent X11 observations, and cleanup. Report a missing dependency as a failure with its reason. Report ID reuse as not observed when the server does not reuse the ID; do not weaken the reuse journey.

The export journey drives the compiled native executable. The JavaScript journey also checks `bend examples/export.bend`, which selects the unsupported JavaScript runtime in Bend 2.0.40. The README quickstart now explicitly builds and runs the native executable. The local example imports the checkout's `winref.bend`. The README also documents `bend-window-ref@0.1.0.3` from BendHub; installing or verifying that published artifact is outside these local journeys and remains unverified. Native macOS and desktop window-manager interactions are also unverified. The JavaScript example cannot reach export because opening its window fails first.

## Features

- [Export a reference and keep using its owner](export-reference.md): live identity, returned owner, title, geometry, and the native launch path.
- [Observe reference expiry and possible ID reuse](reference-lifetime.md): live lookup, post-close failure, and a conditional reuse observation.
- [Run the example on JavaScript](javascript-backend.md): actual unsupported-window failure, stdout, stderr, and exit status.
