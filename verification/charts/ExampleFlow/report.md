# ExampleFlow

TLC reached 12 states and 14 steps. The chart draws 12 states and 11 arrows.
The chart does not draw 3 steps that stay in one chart state.

## EveryExitExplicitlyCloses breaks
The shortest path has 4 steps:
0. Start
1. open window: Window open
2. export fails: Export failed; owner returned
3. rename returned window: Renamed after export failure
4. report error and exit: Exited without explicit close

## Rules that hold
SuccessfulRunCloses, NoDeadlock
