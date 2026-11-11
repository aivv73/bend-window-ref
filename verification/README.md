# Verify window-reference state machines

Five project-local skills cover the bridge, reference lifetime, example, observer, and check pipeline. Their TLA+ models explore finite state spaces because the important questions concern lifetime and operation order. Executable probes check the corresponding real code at controlled external boundaries. Source hashes prevent a changed implementation from silently reusing an unreviewed model.

## Run verification

Install Python 3, Clang, Node, Bend 2.0.40, and Java 11 or later. Java was validated with Temurin 21.0.8+9. Set `JAVA` to its executable if Java is not on PATH. This workspace also has a private Java copy in `~/.cache/bend-window-ref-verification/java`, which the runner detects automatically. The runner downloads TLC 1.7.4, verifies SHA-256 `936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88`, and caches the jar outside the repository. Set `TLA2TOOLS` to an existing copy of that exact jar to work offline.

```sh
python3 verification/check.py all --mutations
```

Choose `bridge`, `references`, `example`, `observer`, or `pipeline` instead of `all` to run one subsystem. Logs and `results.json` go to the ignored `verification/results/` directory; `--out` selects another directory.

Exit codes are:

- **0:** contracts verified and no diagnostic counterexamples.
- **1:** contracts verified, but the recorded diagnostic counterexamples remain.
- **2:** a contract, probe, source agreement, tool, or diagnostic baseline changed and needs review.

For a regression gate that accepts the documented findings, run:

```sh
python3 verification/check.py all --mutations --regression
```

This still checks and reports every diagnostic. It returns 0 only when all contracts pass and every expected counterexample is reproduced. A passing regression gate does not mean every rule holds.

Read each TLA+ result with **/statechart**. Use the model, its `.findings.cfg` when present (otherwise `.cfg`), and the adjacent `.view.mjs`. Work in a scratch directory outside the repo. The generated Mermaid charts and reports in `charts/` record the reviewed run. No semantic transitions are intentionally hidden; chart rendering omits stutters and merges equivalent labels.

## Render the charts

Use /statechart to regenerate Mermaid and reports from the models. To regenerate the SVGs and the interactive HTML from the reviewed Mermaid files, install the pinned renderer outside the repo:

```sh
npm install --prefix /tmp/winref-pele pele@1.9.0
node verification/render.mjs /tmp/winref-pele/node_modules/pele/dist/pele.js
```

Open `verification/charts/index.html`. Each tab includes the rendered SVG, Mermaid source, and checker report. The complete SVGs are also saved beside their `.mmd` files.

## Recorded validation

At source commit `912b48b42be76de4d5adb405917888fa450c1daa`, all five central model contracts passed. Ten deliberate source mutations and five model mutations were detected. The strict command returned 1 for the four documented diagnostics; the regression command returned 0. Both Bend proof files passed, and all five skill frontmatters validated.

The existing native integration check passed under Xvfb. The live lifetime replay resolved ID `2097153`, observed `BadDrawable` after the original owner closed, then observed Xvfb reuse ID `2097153` for a replacement window. The unchanged reference then resolved to that replacement. This confirms one real reuse execution, not a guarantee that every server reuses the ID immediately.

The example failure trace came from its compiled Bend continuations with an injected export failure. Both read-blocking traces used the actual observer and OS pipes. Other foreign failures were checked with controlled external APIs. No production behavior was changed.

## Coverage

| Skill | Model and central contract | Executable evidence |
|---|---|---|
| [Export bridge](../.agents/skills/verify-export-bridge/SKILL.md) | `ExportBridge`: same owner, correct outcome/identity, prior requests synchronized, queued event preserved | Compile actual `winref.c` with instrumented Bend/Xlib boundaries; execute actual `winref.js` |
| [Reference lifetime](../.agents/skills/verify-reference-lifetime/SKILL.md) | `ReferenceLifetime`: copied borrowed identity never becomes an owner | Type-check actual reference declaration, Bend structural proof, C identity check; optional live X11 replay |
| [Example](../.agents/skills/verify-example-lifecycle/SKILL.md) | `ExampleFlow`: successful flow prints both lines and closes | Compile actual Bend program to JS, execute its continuations with controlled external effects |
| [Observer](../.agents/skills/verify-x11-observer/SKILL.md) | `Observer`: handled exits release memory/connection and reap child | Execute actual Python script with controlled failure boundaries; real pipes reproduce blocking reads |
| [Check pipeline](../.agents/skills/verify-check-pipeline/SKILL.md) | `CheckPipeline`: builds precede integration; normal exits clean temporary files | Execute actual shell script with injected command failures and real temporary directories |

Models contain source mappings. The skills record bounds and exclusions. `coverage.json` records the reviewed source commit and hashes. Review a source change with `--review-source`, then update the hashes and sync commit only after confirming that the model still describes the code. The runner never updates them automatically.

`--mutations` modifies disposable copies of the real source and confirms the behavioral probes fail. It separately breaks each model's central invariant and requires TLC to reject it. This establishes sensitivity; it does not prove the model refines the implementation for every possible input.

## Interpret the counterexamples

The strict check deliberately remains nonzero for these diagnostics:

- `UnchangedReferenceIsLive`: export → close. The reference retains its bytes after the server resource disappears. This is documented borrowed-reference behavior.
- `UnchangedReferenceNeverAliases`: export → close → ID reuse. An old reference can identify another window. Reuse is an allowed environment event, not a promise about when X11 chooses an ID.
- `EveryExitExplicitlyCloses`: open → export failure → rename → report error and halt. The explicit close is skipped. Process termination may still reclaim the X11 resource; this is not a demonstrated persistent leak.
- `ReadHasDeadline`: wait for a line → producer remains silent. The observer's timeout covers final process exit, not either `readline`.

## Replay on X11

With a live display, run the existing integration check and the additional lifetime replay:

```sh
./scripts/check.sh
python3 verification/probes/live_reference.py examples/export.bend
```

For headless runs, prefix either command with `xvfb-run -a`. The replay checks that the reference resolves while the owner lives and gives `BadDrawable` after close. It opens a replacement window and reports whether the server reused the ID; reuse is not required for the test to pass. It installs a temporary nonfatal Xlib error handler in its own process.

## Limits

This is bounded verification of explicit models, supported by executable probes, not a proof of the foreign ABI or X11 server. The bridge model treats an export as one effect on Bend's IO thread. It models six input classes and one queued event. The reference model has one original window, at most one copy, one close, and one ID reuse. The example and pipeline model one invocation. The observer models one producer and ordinary Python failures, not fatal Xlib errors or arbitrary external-call hangs.

The export barrier covers requests issued before export. It does not establish visibility of the example's later rename. Live integration checks one successful scheduling of that rename; it does not prove all schedules.

The original root `LAWS.bend` remains unchanged. `verification/LAWS.bend` adds the structural copying rule, and `verification/PROOF.bend` proves it. Bend rejects proof imports containing foreign effects, so the reference probe checks the actual extracted type declaration separately.
