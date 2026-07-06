# Tier C — single ATF1504 + CW 574×2 (superseded)



**Superseded:** 2026-07-06 by **v1.0 hardware rev G** (dual ATF1504: CPLD-CU + CPLD-DP).



Normative replacement: [reference/hardware/cpld-system-controller.md](../../reference/hardware/cpld-system-controller.md).



## Contents



| File | Role |

|------|------|

| [control-word-latch.md](control-word-latch.md) | Tier C CW latch spec (archived) |

| [system_ctrl.pld](system_ctrl.pld) | Monolithic CPLD HDL snapshot |

| [system_ctrl.jed](system_ctrl.jed) | Monolithic bitstream (WinCUPL) |

| [system_ctrl.pin](system_ctrl.pin) | WinCUPL pin lock |

| [gen_pin_lock.py](gen_pin_lock.py) | Pin lock generator (monolithic `.fit`) |

| [fit_report.txt](fit_report.txt) | Tier C fit notes |

| [cpld_system_ctrl.yaml](cpld_system_ctrl.yaml) | Monolithic logical netlist |
| `system_ctrl_gen.*` | WinCUPL monolithic build intermediates (jed, fit, sim, …) |



Active-tree `test_cw_latch_pack.py` removed with rev G promotion.



Do not cite for new breadboard builds.

