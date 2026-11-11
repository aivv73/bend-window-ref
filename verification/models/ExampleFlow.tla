----------------------------- MODULE ExampleFlow -----------------------------
EXTENDS Naturals
\* examples/export.bend: each action is one IO effect or outcome dispatch.
VARIABLES phase, owner, result, lines, explicitlyClosed
vars == <<phase, owner, result, lines, explicitlyClosed>>
Init == /\ phase = "start" /\ owner = FALSE /\ result = "none"
        /\ lines = 0 /\ explicitlyClosed = FALSE
Open == /\ phase = "start" /\ phase' = "open" /\ owner' = TRUE
        /\ UNCHANGED <<result, lines, explicitlyClosed>>
OpenFails == /\ phase = "start" /\ phase' = "openFailed"
             /\ UNCHANGED <<owner, result, lines, explicitlyClosed>>
Export == /\ phase = "open" /\ phase' = "exported" /\ result' \in {"Done", "Fail"}
          /\ UNCHANGED <<owner, lines, explicitlyClosed>>
Rename == /\ phase = "exported" /\ phase' = "renamed"
          /\ UNCHANGED <<owner, result, lines, explicitlyClosed>>
PrintDisplay == /\ phase = "renamed" /\ result = "Done"
                /\ phase' = "displayPrinted" /\ lines' = 1
                /\ UNCHANGED <<owner, result, explicitlyClosed>>
PrintId == /\ phase = "displayPrinted" /\ phase' = "reported" /\ lines' = 2
           /\ UNCHANGED <<owner, result, explicitlyClosed>>
ReportFailure == /\ phase = "renamed" /\ result = "Fail" /\ phase' = "exportFailed"
                 /\ UNCHANGED <<owner, result, lines, explicitlyClosed>>
Sleep == /\ phase = "reported" /\ phase' = "slept"
         /\ UNCHANGED <<owner, result, lines, explicitlyClosed>>
Close == /\ phase = "slept" /\ phase' = "closed" /\ owner' = FALSE
         /\ explicitlyClosed' = TRUE /\ UNCHANGED <<result, lines>>
Finished == /\ phase \in {"closed", "openFailed", "exportFailed"} /\ UNCHANGED vars
Next == Open \/ OpenFails \/ Export \/ Rename \/ PrintDisplay \/ PrintId \/ ReportFailure \/ Sleep \/ Close \/ Finished
Spec == Init /\ [][Next]_vars
SuccessfulRunCloses == phase = "closed" => ~owner /\ explicitlyClosed /\ lines = 2
\* Diagnostic about explicit cleanup, NOT a claim that process exit leaks X11.
EveryExitExplicitlyCloses == phase \in {"closed", "openFailed", "exportFailed"} => ~owner
=============================================================================
