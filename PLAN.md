# Academic Article — Pick-and-Place Approaches Comparison
# mycobot_320 + Gazebo Harmonic

## Goal
Compare different pick-and-place programming approaches on the same robot platform.
Same robot (mycobot_320), same simulation (Gazebo Harmonic), same task (pick cube, place).

## Approaches

| # | Name | File | Status |
|---|------|------|--------|
| A | Hardcoded Joint Angles | approach_A.md | DONE |
| B | Inverse Kinematics (ikpy) | approach_B.md | IN PROGRESS |
| C | MoveIt2 Motion Planning | approach_C.md | IN PROGRESS |
| D | Reinforcement Learning (MuJoCo/SB3) | approach_D.md | IN PROGRESS |

## Platform
- Robot: mycobot_320 M5
- Simulation: Gazebo Harmonic (gz-sim 8.x)
- ROS2: Humble
- OS: Ubuntu 22.04

## Task Definition
- Pick red cube from fixed position (x=0.2620, y=-0.0842, z=0.030)
- Lift and place at target position (TBD)

## Metrics to compare
- [ ] Lines of code / setup complexity
- [ ] Pose accuracy (end position error)
- [ ] Execution time
- [ ] Robustness to small cube position changes
- [ ] Ease of adding new poses/targets

## Next Steps
- [x] Implement Approach B (IK) — pick phase done, compared to Approach A
- [ ] Define place target position
- [ ] Define measurement methodology
- [ ] Run all approaches and record results
