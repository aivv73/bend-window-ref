# ReferenceLifetime

TLC reached 7 states and 10 steps. The chart draws 5 states and 5 arrows.
The chart does not draw 4 steps that stay in one chart state.

## UnchangedReferenceIsLive breaks
The shortest path has 2 steps:
0. Window open
1. export reference: Reference points to original window
2. owner closes window: Unchanged reference points to no window

## UnchangedReferenceNeverAliases breaks
The shortest path has 3 steps:
0. Window open
1. export reference: Reference points to original window
2. owner closes window: Unchanged reference points to no window
3. X11 reuses the ID: Unchanged reference points to another window

## Rules that hold
BorrowedReferenceContract, NoDeadlock
