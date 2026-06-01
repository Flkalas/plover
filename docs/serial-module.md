# Serial module (slot peripheral)

Serial/UART is modeled as an independent slot module, not a motherboard-fixed feature.

## Signature

- `DEV_SIGNATURE = 0xD4`

## MMIO register sketch

- `+0x00` SIGNATURE
- `+0x01` STATUS (`RX_READY`, `TX_READY`, `ERR`)
- `+0x02` TXDATA
- `+0x03` RXDATA
- `+0x04` CTRL

## v0.1 policy

- Polling-only operation (`serial_rx_ready()` loop)
- Device is discovered by `devmgr` signature scan

## VM visibility

- `mon serial` in `dos-shell` reports signature/status and queue lengths

