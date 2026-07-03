# Contract: VM Instrumentation

## Formål

VM skal kunne observeres live uden at UI eller renderer læser private felter direkte.

## Hook points

- before_instruction
- after_instruction
- before_storage_read
- after_storage_read
- before_storage_write
- after_storage_write
- on_register_change
- on_pc_change
- on_halt
- on_error

## Minimal emitted payload

```json
{
  "pc": 12,
  "opcode": "LASER_WRITE",
  "registers": {"R0": 0, "R1": 123},
  "position": {"x": 5, "y": 5, "z": 5},
  "channel": "GREEN",
  "wavelength_nm": 532
}
```

## Constraint

VM instrumentation must be optional and must not change program semantics.
