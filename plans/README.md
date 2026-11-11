# Implementation plans

| Plan | Status | Evidence |
|---|---|---|
| 001 Observer validation under Python optimization | DONE | Reproduced skipped Xlib calls at optimization level 1 before the fix. All 36 controlled scenarios pass at levels 0, 1, and 2. Real 65x48 windows are rejected at all three levels with cleanup preserved. Native integration and both Bend proofs pass with Bend 2.0.40. Observer verification with `--mutations --regression` passes and retains the known `ReadHasDeadline` counterexample. Reviewed cleanup against `Observer.tla` and refreshed only the observer source hash. |
