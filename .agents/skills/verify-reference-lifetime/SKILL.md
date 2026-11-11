---
name: verify-reference-lifetime
description: Check WindowRef copyability, borrowed lifetime, and ID reuse when changing the reference type or exported identity.
---

# Verify references

Property: Copying a reference preserves its identity without copying or recreating the window owner.

Harm: A stale reference can stop resolving or identify a different window after ID reuse.

## Run the check

From the repository root, run:

```sh
python3 verification/check.py references --mutations
```

Use Python 3, Clang, Node, Bend 2.0.40, and Java 11 or later. Set `JAVA` to a Java executable if needed. The runner downloads and checksum-checks TLC 1.7.4 into the user cache. See [verification setup](../../../verification/README.md).

Exit 0 means the checked contracts hold with no diagnostics; exit 1 means recorded diagnostic counterexamples remain; exit 2 means a contract, source-agreement check, probe, or tool failed. `--regression` accepts exactly the recorded diagnostic baseline while continuing to report every counterexample.

Read every TLA+ result with **/statechart**. Use `verification/models/ReferenceLifetime.tla`, its `.cfg` (or `.findings.cfg` when present), and `ReferenceLifetime.view.mjs`. Let /statechart supply its current commands and rendering procedure. Run charts in a scratch directory outside this repository.

## Coverage and interpretation

`winref.bend`: `WindowRef`; `winref.c`: reference construction; `LAWS.bend`: expiry and reuse requirements; `verification/LAWS.bend` and `verification/PROOF.bend`: structural copying.

Model: [models/ReferenceLifetime.tla](../../../verification/models/ReferenceLifetime.tla). Executable probes and counterexamples are described in [the verification guide](../../../verification/README.md).

Bounds and assumptions: One original window, at most one copy, one close, and one possible ID reuse. Server generation is ghost state absent from WindowRef. Close may occur before or after copying. No access-control, cross-server identity, disconnect recovery, or generation-based mitigation is modeled.

`UnchangedReferenceIsLive` and `UnchangedReferenceNeverAliases` fail by design. They disprove unsafe consumer assumptions; they are not library contract failures. Optional live replay: `python3 verification/probes/live_reference.py examples/export.bend` with DISPLAY set. It reports whether this server reused the ID.

Mutation rehearsal: Change WindowRef from Data to Type; shift the exported ID by one. The actual declaration must fail copy checking, and the C bridge must fail the identity check. The runner also breaks this model's contract in a temporary copy and requires TLC to find a counterexample. Production files are never mutated.

## Keep the model aligned

Last source synchronization: `912b48b42be76de4d5adb405917888fa450c1daa`. Per-file SHA-256 values live in [coverage.json](../../../verification/coverage.json), under `references`. A changed covered file fails the default check before the model can give a stale result.

Compare changed functions with the modeled actions, boundaries, and assumptions. Run with `--review-source` while reconciling an intentional change. This flag does not refresh the hashes. If a result differs, replay its steps against the real source before deciding whether the code or model is wrong. Keep an actual finding visible; do not weaken an invariant to obtain a pass.

After reviewing and rerunning the probes, mutations, and /statechart, update this skill's sync commit and the matching `coverage.json` hashes to the reviewed commit. Use /maintain-formal-verification-skill when later changes have bypassed these checks.
