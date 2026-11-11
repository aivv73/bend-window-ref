---
name: verify-export-bridge
description: Check the native and JavaScript export contract when changing WinRef.export, backend selection, XSync, or owner/result construction.
---

# Verify bridge

Property: Export returns the same owner on every outcome, publishes prior requests, and preserves queued events.

Harm: Losing the owner prevents later operations or cleanup; lost events or an unsynchronized ID break consumers.

## Run the check

From the repository root, run:

```sh
python3 verification/check.py bridge --mutations
```

Use Python 3, Clang, Node, Bend 2.0.40, and Java 11 or later. Set `JAVA` to a Java executable if needed. The runner downloads and checksum-checks TLC 1.7.4 into the user cache. See [verification setup](../../../verification/README.md).

Exit 0 means the checked contracts hold with no diagnostics; exit 1 means recorded diagnostic counterexamples remain; exit 2 means a contract, source-agreement check, probe, or tool failed. `--regression` accepts exactly the recorded diagnostic baseline while continuing to report every counterexample.

Read every TLA+ result with **/statechart**. Use `verification/models/ExportBridge.tla`, its `.cfg` (or `.findings.cfg` when present), and `ExportBridge.view.mjs`. Let /statechart supply its current commands and rendering procedure. Run charts in a scratch directory outside this repository.

## Coverage and interpretation

`winref.c`: `winref_export_run`; `winref.js`: `winref_export`; `winref.bend`: `WinRef.export`; `LAWS.bend`: native requirements.

Model: [models/ExportBridge.tla](../../../verification/models/ExportBridge.tla). Executable probes and counterexamples are described in [the verification guide](../../../verification/README.md).

Bounds and assumptions: One call on Bend's IO thread, six input classes, one queued event. The model uses symbolic ordinary/max IDs; C probes check actual U32 boundaries. No Xlib-fatal errors, allocation failure, foreign ABI proof, post-export rename visibility, or parallel Xlib calls.

No diagnostic counterexamples are expected.

Mutation rehearsal: False → True in XSync, replacement of the returned owner in C or JS. The real foreign implementations must fail their probes. The runner also breaks this model's contract in a temporary copy and requires TLC to find a counterexample. Production files are never mutated.

## Keep the model aligned

Last source synchronization: `912b48b42be76de4d5adb405917888fa450c1daa`. Per-file SHA-256 values live in [coverage.json](../../../verification/coverage.json), under `bridge`. A changed covered file fails the default check before the model can give a stale result.

Compare changed functions with the modeled actions, boundaries, and assumptions. Run with `--review-source` while reconciling an intentional change. This flag does not refresh the hashes. If a result differs, replay its steps against the real source before deciding whether the code or model is wrong. Keep an actual finding visible; do not weaken an invariant to obtain a pass.

After reviewing and rerunning the probes, mutations, and /statechart, update this skill's sync commit and the matching `coverage.json` hashes to the reviewed commit. Use /maintain-formal-verification-skill when later changes have bypassed these checks.
