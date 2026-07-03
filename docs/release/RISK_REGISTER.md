# Risk Register

| ID | Risk | Impact | Mitigation | Owner |
|---|---|---|---|---|
| R-001 | Renderer reads VM internals directly | Divergent runtime truth | Eventbus-only observation | Runtime Architect |
| R-002 | Dense crystal allocation in IDE | Memory blowup | Sparse state contract | Storage Specialist |
| R-003 | Logical and physical coordinates mixed | Unsafe hardware assumptions | Canonical coordinate model | Hardware/Geometry |
| R-004 | Simulation confused with physical hardware | Safety and credibility risk | Explicit simulation mode and hardware gate | Hardware Specialist |
| R-005 | Source trace missing after compile | Poor debugger UX | Source-map preservation | Compiler Specialist |
| R-006 | Physics claims exceed review | Credibility risk | Physics/material review gate | Physics Reviewer |
| R-007 | Event volume blocks runtime | Poor performance | Diffs, batching, backpressure | Runtime Architect |
