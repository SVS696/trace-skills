# Event mapping

| Process observation | Work Metrics marker |
|---|---|
| work actually begins | `work_started` |
| explicit pause | `pause_started` |
| intentionally deferred | `deferred` |
| explicit continuation | `resume` |
| result ready to transfer | `ready_for_handoff` |
| transfer completed | `handoff` |
| ordinary completion without handoff | `work_finished` |
| explicit user stop | `user_stopped` |
| process guard stopped work | `guard_stopped` |
| cancellation | `cancelled` |
| external failure ended lifecycle | `external_failure` |
