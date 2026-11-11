---------------------------- MODULE CheckPipeline ----------------------------
EXTENDS Naturals
\* scripts/check.sh:2-9; CI invokes it only after install/version steps succeed.
\* One invocation; failures at each command boundary; normal shell exit trap.
VARIABLES phase, temporary, trapped, nativeBuilt, jsBuilt, checked
vars == <<phase, temporary, trapped, nativeBuilt, jsBuilt, checked>>
Init == /\ phase = "proof" /\ temporary = FALSE /\ trapped = FALSE
        /\ nativeBuilt = FALSE /\ jsBuilt = FALSE /\ checked = FALSE
Proof == /\ phase = "proof" /\ phase' = "allocate" /\ UNCHANGED <<temporary, trapped, nativeBuilt, jsBuilt, checked>>
Allocate == /\ phase = "allocate" /\ phase' = "trap" /\ temporary' = TRUE /\ UNCHANGED <<trapped, nativeBuilt, jsBuilt, checked>>
InstallTrap == /\ phase = "trap" /\ phase' = "native" /\ trapped' = TRUE /\ UNCHANGED <<temporary, nativeBuilt, jsBuilt, checked>>
NativeBuild == /\ phase = "native" /\ phase' = "javascript" /\ nativeBuilt' = TRUE /\ UNCHANGED <<temporary, trapped, jsBuilt, checked>>
JsBuild == /\ phase = "javascript" /\ phase' = "check" /\ jsBuilt' = TRUE /\ UNCHANGED <<temporary, trapped, nativeBuilt, checked>>
Check == /\ phase = "check" /\ phase' = "cleanup" /\ checked' = TRUE /\ UNCHANGED <<temporary, trapped, nativeBuilt, jsBuilt>>
Fail == /\ phase \in {"proof", "allocate", "native", "javascript", "check"}
        /\ phase' = IF trapped THEN "cleanup" ELSE "finished"
        /\ UNCHANGED <<temporary, trapped, nativeBuilt, jsBuilt, checked>>
Cleanup == /\ phase = "cleanup" /\ phase' = "finished" /\ temporary' = FALSE /\ UNCHANGED <<trapped, nativeBuilt, jsBuilt, checked>>
Finished == /\ phase = "finished" /\ UNCHANGED vars
Next == Proof \/ Allocate \/ InstallTrap \/ NativeBuild \/ JsBuild \/ Check \/ Fail \/ Cleanup \/ Finished
Spec == Init /\ [][Next]_vars
CheckPipelineContract ==
  /\ (phase = "finished" => ~temporary)
  /\ (checked => nativeBuilt /\ jsBuilt)
=============================================================================
