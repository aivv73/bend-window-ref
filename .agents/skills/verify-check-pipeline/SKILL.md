---
name: verify-check-pipeline
description: Check proof/build/integration ordering and temporary-directory cleanup when changing scripts/check.sh or its CI invocation.
---

# Verify pipeline

Property: The integration check runs only after both builds succeed, and normal exit removes the temporary build directory.

Harm: Continuing after a failed build can report misleading checks; a missing trap leaves build artifacts.

## Run the check

From the repository root, run:

```sh
python3 verification/check.py pipeline --mutations
```

Use Python 3, Clang, Node, Bend 2.0.40, and Java 11 or later. Set `JAVA` to a Java executable if needed. The runner downloads and checksum-checks TLC 1.7.4 into the user cache. See [verification setup](../../../verification/README.md).

Exit 0 means the checked contracts hold with no diagnostics; exit 1 means recorded diagnostic counterexamples remain; exit 2 means a contract, source-agreement check, probe, or tool failed. `--regression` accepts exactly the recorded diagnostic baseline while continuing to report every counterexample.

Read every TLA+ result with **/statechart**. Use `verification/models/CheckPipeline.tla`, its `.cfg` (or `.findings.cfg` when present), and `CheckPipeline.view.mjs`. Let /statechart supply its current commands and rendering procedure. Run charts in a scratch directory outside this repository.

## Coverage and interpretation

`scripts/check.sh`: entire script; `.github/workflows/check.yml`: invocation and compiler pin reviewed as context.

Model: [models/CheckPipeline.tla](../../../verification/models/CheckPipeline.tla). Executable probes and counterexamples are described in [the verification guide](../../../verification/README.md).

Bounds and assumptions: One shell invocation; success/failure at proof, mktemp, native build, JavaScript build, and observer boundaries. Trap installation and rm are assumed to succeed. SIGKILL, disk faults during cleanup, CI infrastructure, package authenticity, network installation, and the pre-trap interruption gap are outside this model. JavaScript is built but not executed by check.sh.

No diagnostic counterexamples are expected.

Mutation rehearsal: Remove the EXIT cleanup or errexit from a scratch copy of the real shell script. Failure injection must catch leaked directories or execution after failure. The runner also breaks this model's contract in a temporary copy and requires TLC to find a counterexample. Production files are never mutated.

## Keep the model aligned

Last source synchronization: `912b48b42be76de4d5adb405917888fa450c1daa`. Per-file SHA-256 values live in [coverage.json](../../../verification/coverage.json), under `pipeline`. A changed covered file fails the default check before the model can give a stale result.

Compare changed functions with the modeled actions, boundaries, and assumptions. Run with `--review-source` while reconciling an intentional change. This flag does not refresh the hashes. If a result differs, replay its steps against the real source before deciding whether the code or model is wrong. Keep an actual finding visible; do not weaken an invariant to obtain a pass.

After reviewing and rerunning the probes, mutations, and /statechart, update this skill's sync commit and the matching `coverage.json` hashes to the reviewed commit. Use /maintain-formal-verification-skill when later changes have bypassed these checks.
