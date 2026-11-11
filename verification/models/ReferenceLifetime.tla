------------------------- MODULE ReferenceLifetime -------------------------
EXTENDS Naturals
\* winref.bend:7-15; LAWS.bend native requirements.
\* One exported value, one copy, one close, and one possible X11 ID reuse.
\* Server generations are ghost state: WindowRef stores no generation.
VARIABLES phase, owner, server, ref, copy
vars == <<phase, owner, server, ref, copy>>
Init == /\ phase = "owned" /\ owner = "open" /\ server = "original"
        /\ ref = 0 /\ copy = 0
Export == /\ phase = "owned" /\ phase' = "exported" /\ ref' = 7
          /\ UNCHANGED <<owner, server, copy>>
Copy == /\ phase = "exported" /\ phase' = "copied" /\ copy' = ref
        /\ UNCHANGED <<owner, server, ref>>
Close == /\ phase \in {"exported", "copied"} /\ phase' = "expired"
         /\ owner' = "closed" /\ server' = "absent" /\ UNCHANGED <<ref, copy>>
Reuse == /\ phase = "expired" /\ phase' = "reused" /\ server' = "other"
         /\ UNCHANGED <<owner, ref, copy>>
Finished == /\ phase \in {"expired", "reused"} /\ UNCHANGED vars
Next == Export \/ Copy \/ Close \/ Reuse \/ Finished
Spec == Init /\ [][Next]_vars
BorrowedReferenceContract ==
  /\ (phase # "owned" => ref = 7)
  /\ (phase = "copied" => copy = ref)
  /\ (copy # 0 => copy = ref)
  /\ (phase \in {"expired", "reused"} => owner = "closed")
\* Diagnostic assumptions, NOT library promises. Keep their counterexamples.
UnchangedReferenceIsLive == ref # 0 => server = "original"
UnchangedReferenceNeverAliases == ref # 0 => server # "other"
=============================================================================
