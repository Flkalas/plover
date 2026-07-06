# CPLD pin budget — rev G dual ATF1504

**Normative:** [reference/hardware/cpld-system-controller.md](../../reference/hardware/cpld-system-controller.md)

## CPLD-CU (26/32 used)

| In | `opc[4:0]`, `flg_z`, `clk` |
| Out SoC | 14 strobes |
| Out G-IC | `reg_we`, `w_sel[1:0]`, `tfr_valid`, `src[1:0]` |

## CPLD-DP (31/32 used)

| In | `d_in[7:0]`, G-IC×6, `clk` |
| Out | `q_a[7:0]`, `q_b[7:0]` |

## Superseded

Tier C monolithic pin lock — [archive/tier-c-single-cpld/](../../archive/tier-c-single-cpld/).
