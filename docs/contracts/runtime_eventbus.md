# Contract: Runtime Eventbus

## Formål

Eventbus er den eneste officielle kanal til live runtime-observation i Desktop IDE.

## Event envelope

```json
{
  "event_id": "uuid-or-monotonic-id",
  "event_type": "vm.step.completed",
  "schema_version": "1.0",
  "timestamp_ns": 0,
  "runtime_id": "session-id",
  "sequence": 0,
  "payload": {}
}
```

## Required event types

| Event type | Producer | Consumer |
|---|---|---|
| runtime.started | desktop_ide/vm | all panels |
| runtime.stopped | vm | all panels |
| vm.step.started | vm | trace/debug |
| vm.step.completed | vm | trace/debug/renderer |
| vm.registers.changed | vm | register panel |
| vm.pc.changed | vm | source trace |
| crystal.voxel.written | storage/vm | renderer, trace |
| crystal.voxel.read | storage/vm | trace |
| hardware.telemetry.updated | hardware_sim | telemetry panel |
| renderer.snapshot.requested | desktop_ide | renderer |
| renderer.snapshot.ready | renderer | desktop_ide |

## Guarantees

- Events are append-only.
- Sequence is monotonic per runtime session.
- Payloads are JSON-serializable.
- Event producers must not expose mutable internal objects.
- Failed operations emit an error event before raising or halting.

## Open specialist questions

- Runtime specialist: define minimal event API in Python.
- VM specialist: define exact hook points for instruction execution.
- Renderer specialist: confirm diff granularity for 60 FPS preview.
