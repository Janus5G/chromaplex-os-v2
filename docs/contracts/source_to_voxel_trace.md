# Contract: Source-to-Voxel Trace

## Formål

IDE skal kunne forklare hvilken CPL/CPA-kilde der ændrede hvilken voxel og kanal.

## Trace record

```json
{
  "trace_id": "trace-id",
  "runtime_id": "session-id",
  "event_sequence": 42,
  "source": {
    "file": "examples/hello.cpl",
    "line": 7,
    "column": 5,
    "span": "kanal grøn = e, rest = rest;"
  },
  "bytecode": {
    "pc": 18,
    "opcode": "LASER_WRITE"
  },
  "voxel": {
    "x": 0,
    "y": 0,
    "z": 0,
    "channel": "GREEN",
    "wavelength_nm": 532
  }
}
```

## Requirements

- Compiler must preserve source map metadata where possible.
- Assembler must preserve instruction origin metadata where possible.
- VM emits trace correlation during storage writes.
- Renderer can highlight traced voxel but cannot create trace records.
