# Contract: Sparse Crystal State

## Formål

Desktop IDE runtime skal håndtere store krystalrum uden dense 1024³ allocation.

## Sparse voxel record

```json
{
  "coord": {"x": 5, "y": 5, "z": 5},
  "channels": {
    "GREEN": {
      "wavelength_nm": 532,
      "encoded_value": 1234567,
      "decoded_value": 1234567,
      "last_write_event": "event-id"
    }
  }
}
```

## Storage rules

- Empty voxel/channel reads return zero.
- Writes create sparse records lazily.
- Zero writes may either keep tombstones or remove channel entries; choice must be documented.
- Storage emits read/write events but does not call renderer directly.
- Serialization must be stable JSON for replay/debug.

## Required tests

- Empty read returns zero.
- Multiple channels per voxel remain independent.
- Sparse serialization roundtrip preserves values.
- Out-of-bounds coordinates fail with structured error.
