# Device discovery (slot signature model)

Discovery uses **standard bus slot windows** and a fixed signature register.

## Slot rule

- `SLOTn_BASE + 0x00` = `DEV_SIGNATURE`
- `0x00` or `0xFF` => empty/unpopulated slot

## Signature examples

- `0xA1` => vFDD
- `0xB2` => Video
- `0xC3` => GPIO
- `0xD4` => Serial (UART module)

## Kernel behavior

`devmgr_scan(slots)` probes each slot, builds `device_table`, and binds driver by signature.

Example log:

`DEV slot1 sig=C3 drv=gpio`

