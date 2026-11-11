------------------------------ MODULE Observer ------------------------------
EXTENDS Naturals
\* scripts/check_x11.py:20-47. Ordinary Python errors, not process-fatal Xlib errors.
\* Silent producer can block the first or second readline; no timer exists there.
VARIABLES phase, display, name, child
vars == <<phase, display, name, child>>
Init == /\ phase = "readDisplay" /\ display = FALSE /\ name = FALSE /\ child = "running"
ReadDisplay == /\ phase = "readDisplay" /\ phase' = "readId" /\ UNCHANGED <<display, name, child>>
ReadId == /\ phase = "readId" /\ phase' = "connect" /\ UNCHANGED <<display, name, child>>
Silence == /\ phase \in {"readDisplay", "readId"} /\ phase' = "blocked" /\ UNCHANGED <<display, name, child>>
ParseFails == /\ phase \in {"readDisplay", "readId", "connect"} /\ phase' = "stopChild" /\ UNCHANGED <<display, name, child>>
Connect == /\ phase = "connect" /\ phase' = "fetchName" /\ display' = TRUE /\ UNCHANGED <<name, child>>
ConnectFails == /\ phase = "connect" /\ phase' = "stopChild" /\ UNCHANGED <<display, name, child>>
FetchName == /\ phase = "fetchName" /\ phase' = "checkName" /\ name' = TRUE /\ UNCHANGED <<display, child>>
FetchFails == /\ phase = "fetchName" /\ phase' = "closeDisplayOnError" /\ UNCHANGED <<display, name, child>>
CheckName == /\ phase = "checkName" /\ phase' \in {"freeName", "freeNameOnError"} /\ UNCHANGED <<display, name, child>>
FreeName == /\ phase \in {"freeName", "freeNameOnError"}
            /\ phase' = IF phase = "freeName" THEN "geometry" ELSE "closeDisplayOnError"
            /\ name' = FALSE /\ UNCHANGED <<display, child>>
Geometry == /\ phase = "geometry" /\ phase' \in {"closeDisplay", "closeDisplayOnError"} /\ UNCHANGED <<display, name, child>>
CloseDisplay == /\ phase \in {"closeDisplay", "closeDisplayOnError"} /\ phase' = (IF phase = "closeDisplay" THEN "wait" ELSE "stopChild") /\ display' = FALSE /\ UNCHANGED <<name, child>>
Wait == /\ phase = "wait" /\ phase' = "finished" /\ child' = "reaped" /\ UNCHANGED <<display, name>>
WaitTimeout == /\ phase = "wait" /\ phase' = "stopChild" /\ UNCHANGED <<display, name, child>>
Kill == /\ phase = "stopChild" /\ phase' = "reap" /\ child' = "killed" /\ UNCHANGED <<display, name>>
Reap == /\ phase = "reap" /\ phase' = "finished" /\ child' = "reaped" /\ UNCHANGED <<display, name>>
Finished == /\ phase = "finished" /\ UNCHANGED vars
\* Stuttering while waiting is legitimate; a separate diagnostic checks timeout coverage.
Blocked == /\ phase = "blocked" /\ UNCHANGED vars
Next == ReadDisplay \/ ReadId \/ Silence \/ ParseFails \/ Connect \/ ConnectFails \/ FetchName \/ FetchFails \/ CheckName \/ FreeName \/ Geometry \/ CloseDisplay \/ Wait \/ WaitTimeout \/ Kill \/ Reap \/ Finished \/ Blocked
Spec == Init /\ [][Next]_vars
ObserverReleasesResources == phase = "finished" => ~display /\ ~name /\ child = "reaped"
ReadHasDeadline == phase # "blocked"
=============================================================================
