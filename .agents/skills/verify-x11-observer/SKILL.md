---
name: verify-x11-observer
description: Check the observer's line protocol, resource cleanup, and blocking reads when changing scripts/check_x11.py.
---

# Verify observer

Property: After handled success or failure, the observer releases title memory and its display connection and reaps the producer.

Harm: Unhandled resource ownership can leave allocations or processes behind; a silent producer can block the check.

## Run the check

From the repository root, run:

```sh
python3 verification/check.py observer --mutations
```

Use Python 3, Clang, Node, Bend 2.0.40, and Java 11 or later. Set `JAVA` to a Java executable if needed. The runner downloads and checksum-checks TLC 1.7.4 into the user cache. See [verification setup](../../../verification/README.md).

Exit 0 means the checked contracts hold with no diagnostics; exit 1 means recorded diagnostic counterexamples remain; exit 2 means a contract, source-agreement check, probe, or tool failed. `--regression` accepts exactly the recorded diagnostic baseline while continuing to report every counterexample.

Read every TLA+ result with **/statechart**. Use `verification/models/Observer.tla`, its `.cfg` (or `.findings.cfg` when present), and `Observer.view.mjs`. Let /statechart supply its current commands and rendering procedure. Run charts in a scratch directory outside this repository.

## Coverage and interpretation

`scripts/check_x11.py`: Popen block, two readline calls, title/geometry lookup, and nested finally blocks; `examples/export.bend`: emitted line protocol.

Model: [models/Observer.tla](../../../verification/models/Observer.tla). Executable probes and counterexamples are described in [the verification guide](../../../verification/README.md).

Bounds and assumptions: One producer and one observer connection, one title allocation, ordinary Python failures at read/parse/connect/title/geometry/wait boundaries. Foreign calls and successful child termination are assumed to return. No fatal Xlib errors, SIGKILL cleanup, external Xlib hangs, or scheduler fairness proof. Blocked reads stutter, so NoDeadlock alone does not establish termination.

`ReadHasDeadline` fails when either line never arrives. The replay uses the actual observer, OS pipes, and an external watchdog; the ten-second process.wait timeout does not cover the reads.

Mutation rehearsal: Remove XFree or process.kill in disposable source copies. The real observer executed with controlled APIs must fail cleanup or detect an unbounded wait. The runner also breaks this model's contract in a temporary copy and requires TLC to find a counterexample. Production files are never mutated.

## Keep the model aligned

Last source synchronization: `912b48b42be76de4d5adb405917888fa450c1daa`. Per-file SHA-256 values live in [coverage.json](../../../verification/coverage.json), under `observer`. A changed covered file fails the default check before the model can give a stale result.

Compare changed functions with the modeled actions, boundaries, and assumptions. Run with `--review-source` while reconciling an intentional change. This flag does not refresh the hashes. If a result differs, replay its steps against the real source before deciding whether the code or model is wrong. Keep an actual finding visible; do not weaken an invariant to obtain a pass.

After reviewing and rerunning the probes, mutations, and /statechart, update this skill's sync commit and the matching `coverage.json` hashes to the reviewed commit. Use /maintain-formal-verification-skill when later changes have bypassed these checks.
