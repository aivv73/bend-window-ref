--------------------------- MODULE ExportBridge ---------------------------
EXTENDS Naturals
\* IDs 1 and 2 represent ordinary and UINT32_MAX; the C probe checks actual U32 boundaries.
\* winref.c:3-22 and winref.js:2-5. One foreign call runs on the IO thread.
\* The call is atomic relative to other Bend effects. Xlib failure is excluded.
VARIABLES phase, input, owner, result, synced, queued, refId
vars == <<phase, input, owner, result, synced, queued, refId>>
Inputs == {"valid", "maxId", "missing", "overflow", "unsupported", "javascript"}
Init == /\ phase = "ready" /\ input \in Inputs /\ owner = "original"
        /\ result = "none" /\ synced = FALSE /\ queued = 1 /\ refId = 0
Export ==
  /\ phase = "ready" /\ phase' = "returned" /\ owner' = owner
  /\ result' = CASE input \in {"valid", "maxId"} -> "Done"
                   [] input = "missing" -> "EIO"
                   [] input = "overflow" -> "EOVERFLOW"
                   [] OTHER -> "ENOTSUP"
  /\ synced' = (input \in {"valid", "maxId"})
  /\ refId' = CASE input = "valid" -> 1 [] input = "maxId" -> 2 [] OTHER -> 0
  /\ UNCHANGED <<input, queued>>
Finished == /\ phase = "returned" /\ UNCHANGED vars
Next == Export \/ Finished
Spec == Init /\ [][Next]_vars
\* LAWS.bend: same owner, valid identity, ordered publication, no lost events.
ExportContract == phase = "returned" =>
  /\ owner = "original" /\ queued = 1
  /\ (result = "Done" <=> input \in {"valid", "maxId"})
  /\ (result = "Done" => synced /\ refId \in {1, 2})
  /\ (input = "missing" => result = "EIO")
  /\ (input = "overflow" => result = "EOVERFLOW")
  /\ (input \in {"unsupported", "javascript"} => result = "ENOTSUP")
=============================================================================
