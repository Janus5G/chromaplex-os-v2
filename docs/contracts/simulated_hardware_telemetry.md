# Contract: Simulated Hardware Telemetry

## Formål

Desktop IDE skal vise laserposition, bølgelængde og power som simuleret telemetry, adskilt fra fysisk hardware.

## Telemetry payload

```json
{
  "mode": "simulated",
  "position": {"x": 5, "y": 5, "z": 5},
  "wavelength_nm": 532,
  "power_percent": 50,
  "beam_state": "idle|moving|write_pulse|read_pulse",
  "safety_state": "simulation-only"
}
```

## Rules

- Simulated telemetry is default.
- Physical telemetry requires explicit hardware driver gate.
- No physical write/read pulse may be exposed through simulation API.
- Safety state must be visible in UI.
