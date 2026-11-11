---
name: verify-bend-window-ref
description: Launch and drive the real bend-window-ref Bend library example on Linux/X11, verify exported references and lifetime, and capture native and JavaScript CLI evidence after changes.
---

# Verify bend-window-ref

The primary surface is `W.WinRef.export(window)` in a Bend program. The local example is the user journey: open a 64x48 window, export its reference, rename the returned owner, print display and ID, then close after three seconds. This skill drives real compiled code and X11; use the existing `verify-*` subsystem skills for formal models and injected foreign failures.

Read [the feature map](features/README.md) before choosing a journey. `all` covers the three automated local journeys, not the published BendHub package or other native platforms.

## Launch

Run commands from the repository root. Required: Linux, Python 3, Bend **2.0.40**, Clang, Node, X11 development headers/runtime, and Xvfb. No credentials, ports, database, seed records, or application data directory are needed. The bridge depends on Bend's internal window representation; stop and revalidate before changing compiler versions.

On a machine with Xvfb on PATH, launch and drive all mapped local journeys with:

```sh
.agents/skills/verify-bend-window-ref/scripts/control.py run all
```

On this workspace Xvfb is available as an extracted executable, not on PATH. Configure its observed location before running the same commands:

```sh
export WINREF_XVFB=/home/aivv/.cache/bend-window-capture-live/usr/bin/Xvfb
```

Alternatively pass `--xvfb /home/aivv/.cache/bend-window-capture-live/usr/bin/Xvfb` to `doctor` or `run`. A fresh host must install Xvfb and X11 dependencies; this cached path is not a portable installation step. The helper installs nothing.

The helper creates a new build directory and starts its own Xvfb with `-displayfd 1 -screen 0 800x600x24 -nolisten tcp`. It waits for the assigned display and proves it can connect. Each native drive then starts the real example. A usable example publishes two stdout lines that an independent X11 connection resolves to the expected title and geometry; a running process alone is not readiness.

The compiled native example runs through the existing observer. The direct `bend examples/export.bend` command is checked in the unsupported-runtime journey: it selects JavaScript under Bend 2.0.40. Each short-lived process has its own process group. No PTY is needed: stdout is a two-line protocol consumed through pipes, not an interactive terminal UI.

The run tears down its processes and build directory before returning. Independent runs get separate displays, scratch directories, and evidence directories. Never attach this helper to a user's existing display.

## Doctor

Run this read-only check first whenever a run looks wrong:

```sh
.agents/skills/verify-bend-window-ref/scripts/control.py doctor
```

It checks the compiler version, executable paths, X11 headers/runtime, and covered source hashes. It does not start Xvfb or alter source. Use `doctor --javascript-only` when checking only the JavaScript path. During a native run, the same doctor also verifies that the Xvfb process this run started is alive and that its assigned display accepts a connection. `doctor-live.json` records the PID and display.

Missing dependencies or the wrong compiler are failures, not skipped assertions. Inspect the doctor result before retrying.

## Drive

```sh
.agents/skills/verify-bend-window-ref/scripts/control.py run export
.agents/skills/verify-bend-window-ref/scripts/control.py run lifetime
.agents/skills/verify-bend-window-ref/scripts/control.py run javascript
```

- `export` builds the actual example and runs `scripts/check_x11.py` against it. The observer checks the emitted display/ID, the owner's renamed title, 64x48 geometry, and clean exit.
- `lifetime` runs the existing real-X11 replay in `verification/probes/live_reference.py`. It checks live resolution, expiry after close, and reports whether this server reused the ID for a replacement window.
- `javascript` compiles the actual example to JavaScript and runs it with Node, then also runs `bend examples/export.bend` directly. On Linux the expected result is exit 95, no reference on stdout, and `Window.open: no display` on stderr. Opening fails before `WinRef.export`; do not claim this journey proves the JavaScript export function's ownership behavior.

No internal setters, mock Xlib, synthetic owner handles, or test-only endpoints are used. The lifetime replay's replacement window is verification scaffolding for observing real server ID reuse.

## Evidence

The helper prints its evidence directory before launching anything. By default it is a unique directory under `verification/results/live/`. Select a new destination with:

```sh
.agents/skills/verify-bend-window-ref/scripts/control.py run export --evidence /tmp/bend-window-ref-export-proof
```

An existing destination is refused, so earlier evidence is not overwritten. Evidence contains:

- `summary.json`: selected feature IDs, exact commands, exit codes, executable hashes, findings, uncovered surfaces, and cleanup results.
- `doctor-before.json` and, for native runs, `doctor-live.json`: source hashes, dependency versions, owned server PID, and display.
- A `.stdout` and `.stderr` file per build/drive, plus `xvfb.stderr`.
- For lifetime, the actual exported ID, post-close X11 error, replacement ID, and whether reuse was observed.

A proof includes the action and observed result: the observer's independent X11 assertions establish title and geometry, and the lifetime replay reads the server before and after close. Do not substitute a screenshot of an empty window or a successful compile. There is no dry-run mode. Runs create real windows and connections only on their own display; no application records or network services are involved.

If reuse is not observed, report that sub-feature as **not observed**, even when expiry passes. The helper records the lifetime journey as incomplete and exits 1; this is an unmet runtime precondition, not proof of a library defect. Never manufacture reuse or count the model's counterexample as runtime evidence.

## Cleanup

Cleanup is automatic on success, ordinary failure, Ctrl-C, or SIGTERM. The helper terminates only process groups it started, waits for them, and removes its temporary build directory. Child tools inherit that directory as `TMPDIR`, so their nested temporary builds are removed too. It keeps the evidence directory. Xvfb teardown also releases windows and connections left by a timed-out client.

After every attempt, read `summary.json`: native runs must record `xvfb_reaped: true`, launched builds must record `scratch_removed: true`, and evidence must remain readable. A failed preflight has no server/build directory to remove. Do not kill processes by name or reuse a different run's PID. SIGKILL or machine failure cannot execute Python cleanup; do not claim cleanup succeeded without evidence.

## Helpers

The only shipped helper is executable `scripts/control.py`. Its public commands are `doctor` and `run`; invoke them as shown above. `--help` and `run --help` list the supported selectors and options. The helper reuses the repository's X11 observer and lifetime replay rather than replacing them.

Child processes do not inherit `PYTHONOPTIMIZE`, because the observers rely on Python assertions. To check that wrong geometry is still rejected at optimization levels 0, 1, and 2, run `python3 verification/probes/optimized_observer.py` with Xvfb on PATH or `WINREF_XVFB` configured. The probe changes only a disposable copy of the example and keeps evidence under `verification/results/optimized-observer/`.

For maintenance, use `/maintain-verification-skill` to keep the feature map aligned with the app. Keep formal-model maintenance separate from these real-user journeys.
