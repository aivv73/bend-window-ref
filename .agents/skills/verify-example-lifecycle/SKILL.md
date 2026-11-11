---
name: verify-example-lifecycle
description: Check the example's open/export/report/close flow when changing examples/export.bend or its error handling.
---

# Verify example

Property: A successful example prints display and ID, waits, and explicitly closes the returned owner.

Harm: Moving or removing cleanup changes resource lifetime; a failure can bypass explicit close.

## Run the check

From the repository root, run:

```sh
python3 verification/check.py example --mutations
```

Use Python 3, Clang, Node, Bend 2.0.40, and Java 11 or later. Set `JAVA` to a Java executable if needed. The runner downloads and checksum-checks TLC 1.7.4 into the user cache. See [verification setup](../../../verification/README.md).

Exit 0 means the checked contracts hold with no diagnostics; exit 1 means recorded diagnostic counterexamples remain; exit 2 means a contract, source-agreement check, probe, or tool failed. `--regression` accepts exactly the recorded diagnostic baseline while continuing to report every counterexample.

Read every TLA+ result with **/statechart**. Use `verification/models/ExampleFlow.tla`, its `.cfg` (or `.findings.cfg` when present), and `ExampleFlow.view.mjs`. Let /statechart supply its current commands and rendering procedure. Run charts in a scratch directory outside this repository.

## Coverage and interpretation

`examples/export.bend`: `main`, `opened`, `exported`, `report`, and `show_ref`.

Model: [models/ExampleFlow.tla](../../../verification/models/ExampleFlow.tla). Executable probes and counterexamples are described in [the verification guide](../../../verification/README.md).

Bounds and assumptions: One execution with open success/failure and export success/failure. Each modeled effect follows the compiled Bend continuations. The probe controls external Window/print/sleep effects; it does not emulate time, window events, title visibility, or allocation failure. Process exit may release X11 resources: missing explicit close is not proof of a persistent resource leak.

`EveryExitExplicitlyCloses` fails on open → export failure → rename → IO.die. Preserve this finding until the source behavior is intentionally changed.

Mutation rehearsal: Remove Window.close from a scratch copy of the actual Bend program. The compiled continuation probe must detect the missing close. The runner also breaks this model's contract in a temporary copy and requires TLC to find a counterexample. Production files are never mutated.

## Keep the model aligned

Last source synchronization: `912b48b42be76de4d5adb405917888fa450c1daa`. Per-file SHA-256 values live in [coverage.json](../../../verification/coverage.json), under `example`. A changed covered file fails the default check before the model can give a stale result.

Compare changed functions with the modeled actions, boundaries, and assumptions. Run with `--review-source` while reconciling an intentional change. This flag does not refresh the hashes. If a result differs, replay its steps against the real source before deciding whether the code or model is wrong. Keep an actual finding visible; do not weaken an invariant to obtain a pass.

After reviewing and rerunning the probes, mutations, and /statechart, update this skill's sync commit and the matching `coverage.json` hashes to the reviewed commit. Use /maintain-formal-verification-skill when later changes have bypassed these checks.
