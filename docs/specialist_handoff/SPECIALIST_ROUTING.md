# Specialist Routing Matrix

| Priority | Topic | Owner | Output required |
|---:|---|---|---|
| 1 | Eventbus og runtime events | Runtime Architect | `docs/contracts/runtime_eventbus.md` plus prototype API |
| 2 | Canonical coordinate model | Storage/Geometry Specialist | coordinate schema and bounds tests |
| 3 | Sparse crystal state | Storage Specialist | sparse state API and JSON roundtrip tests |
| 4 | Live 3D renderer contract | Renderer Specialist | snapshot/diff schema and performance notes |
| 5 | VM instrumentation | VM Specialist | hook map and event emission points |
| 6 | Source-to-voxel trace | Compiler/Debug Specialist | source-map/trace schema |
| 7 | Simulated hardware telemetry | Hardware Abstraction Specialist | simulation-only telemetry interface |
| 8 | Physics/material review | Physics Reviewer | review memo and risk register |
| 9 | Release documentation | Release Engineer | package JSON, unpack script, release notes |

## Mandatory handoff format

Each specialist output must include:

```text
Title:
Owner:
Status:
Inputs:
Outputs:
Contracts changed:
Tests required:
Open decisions:
Risks:
```
