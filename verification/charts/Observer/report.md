# Observer

TLC reached 15 states and 25 steps. The chart draws 10 states and 15 arrows.
The chart does not draw 7 steps that stay in one chart state.

## ReadHasDeadline breaks
The shortest path has 1 step:
0. Wait for display line
1. producer stops sending output: Waiting without a deadline

## Rules that hold
ObserverReleasesResources, NoDeadlock
