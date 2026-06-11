#!/usr/bin/env python3
"""Generate hw/fixtures/sw/media_bench.pls print routines."""

from __future__ import annotations

from pathlib import Path


def pr_line(name: str, attr: int, text: str) -> str:
    lines = [
        f"{name}:",
        "        LDA  0",
        f"        ADD  ${attr:02X}",
        "        MOV  $02",
        "        STIO $02",
    ]
    for i, ch in enumerate(text):
        off = 4 + i
        if off > 0x1B:
            raise ValueError(f"{name}: line too long ({len(text)} chars)")
        lines += [
            "        LDA  0",
            f"        ADD  ${ord(ch):02X}",
            "        MOV  $02",
            f"        STIO ${off:02X}",
        ]
    lines += [
        "        LDA  c_vdu_print",
        "        STIO $01",
        "        RET",
        "",
    ]
    return "\n".join(lines)


HEADER = """; Plover media diagnostic — NES-style auto tests + HID interactive (no HALT)
; ZP $E3-$FF; boot @ $E0; code follows constants @ $0100 (play --origin 0xE0)

        .ORG $00E0
        JMP  start

        .ORG $00E3
c_attr:       .DB $07
c_vdu_cls:    .DB $10
c_vdu_putch:  .DB $11
c_vdu_print:  .DB $14
c_vdu_cursor: .DB $16
c_vdu_vsync:  .DB $30
c_gfx_fill:   .DB $23
c_gfx_getpix: .DB $25
c_apu_ctrl:   .DB $50
c_apu_write:  .DB $51
c_apu_sync:   .DB $52
c_hid_poll:   .DB $40
c_hid_key:    .DB $41
c_hid_mouse:  .DB $42
c_master:     .DB $0F
c_ch0:        .DB $00
c_vol:        .DB $0F
c_wave_sq:    .DB $01
c_period_lo:  .DB $16
c_period_hi:  .DB $00
c_red_lo:     .DB $00
c_red_hi:     .DB $F8
c_grn_lo:     .DB $E0
c_grn_hi:     .DB $07
c_px_x:       .DB $0A
c_px_y:       .DB $14
c_box_w:      .DB $08
c_box_h:      .DB $08
c_pad:        .DB $00

start:
        CALL diag_init
        CALL test_vdu_text
        CALL test_vdu_vsync
        CALL test_gfx_pixel
        CALL test_apu_ch0
        CALL pr_hid_k_run
        CALL pr_hid_m_run
        LDA  0
        MOV  $20
        MOV  $30
        JMP  interact_loop

diag_init:
        LDA  c_attr
        STIO $02
        LDA  c_vdu_cls
        STIO $01
        CALL pr_title
        CALL pr_rule
        CALL apu_beep
        LDA  c_vdu_vsync
        STIO $01
        RET

test_vdu_text:
        LDA  0
        ADD  $58
        MOV  $02
        LDA  c_attr
        STIO $02
        LDA  c_vdu_putch
        STIO $01
        LDA  c_vdu_cursor
        STIO $01
        LDIO $04
        CMP  1
        BEQ  test_vdu_text_ok
        CALL pr_vdu_fail
        RET
test_vdu_text_ok:
        CALL pr_vdu_pass
        RET

test_vdu_vsync:
        LDA  c_vdu_vsync
        STIO $01
        CALL pr_sync_pass
        RET

test_gfx_pixel:
        LDA  c_px_x
        STIO $04
        LDA  c_px_y
        STIO $05
        LDA  c_box_w
        STIO $06
        LDA  c_box_h
        STIO $07
        LDA  c_red_lo
        STIO $08
        LDA  c_red_hi
        STIO $09
        LDA  c_gfx_fill
        STIO $01
        LDA  c_px_x
        STIO $04
        LDA  c_px_y
        STIO $05
        LDA  c_gfx_getpix
        STIO $01
        LDIO $06
        CMP  0
        BEQ  test_gfx_chk_hi
        JMP  test_gfx_fail
test_gfx_chk_hi:
        LDIO $07
        CMP  $F8
        BEQ  test_gfx_pass
test_gfx_fail:
        CALL pr_gfx_fail
        RET
test_gfx_pass:
        CALL pr_gfx_pass
        RET

test_apu_ch0:
        CALL apu_beep
        CALL pr_apu_pass
        RET

interact_loop:
        LDA  c_hid_poll
        STIO $01
        LDIO $04
        CMP  0
        BEQ  chk_mouse
        MOV  $02
        CMP  0
        BEQ  hid_key_first
        JMP  hid_key_echo
hid_key_first:
        CALL pr_hid_k_pass
        LDA  1
        MOV  $21
hid_key_echo:
        LDA  c_hid_key
        STIO $01
        LDIO $04
        STIO $02
        LDA  c_vdu_putch
        STIO $01
        CALL apu_beep
        LDA  c_vdu_vsync
        STIO $01
        JMP  interact_loop

chk_mouse:
        LDIO $05
        CMP  0
        BEQ  interact_loop
        LDA  c_hid_mouse
        STIO $01
        MOV  $03
        CMP  0
        BEQ  hid_mouse_first
        JMP  interact_loop
hid_mouse_first:
        CALL pr_hid_m_pass
        LDA  1
        MOV  $31
        LDA  c_vdu_vsync
        STIO $01
        JMP  interact_loop

apu_beep:
        LDA  c_master
        STIO $04
        LDA  0
        STIO $05
        LDA  c_apu_ctrl
        STIO $01
        LDA  c_ch0
        STIO $04
        LDA  c_period_lo
        STIO $05
        LDA  c_period_hi
        STIO $06
        LDA  c_vol
        STIO $07
        LDA  c_wave_sq
        STIO $08
        LDA  c_apu_write
        STIO $01
        LDA  c_apu_sync
        STIO $01
        RET

"""

MSGS = [
    ("pr_title", 0x17, "PLOVER DIAGNOSTIC\n"),
    ("pr_rule", 0x18, "--------------------\n"),
    ("pr_vdu_pass", 0x17, "VDU TEXT ........ PASS\n"),
    ("pr_vdu_fail", 0x17, "VDU TEXT ........ FAIL\n"),
    ("pr_sync_pass", 0x17, "VDU VSYNC ....... PASS\n"),
    ("pr_gfx_pass", 0x17, "GFX FILL/READ ... PASS\n"),
    ("pr_gfx_fail", 0x17, "GFX FILL/READ ... FAIL\n"),
    ("pr_apu_pass", 0x17, "APU CH0 ......... PASS\n"),
    ("pr_hid_k_run", 0x17, "HID KEY ......... RUN\n"),
    ("pr_hid_m_run", 0x17, "HID MOUSE ....... RUN\n"),
    ("pr_hid_k_pass", 0x17, "HID KEY ......... PASS\n"),
    ("pr_hid_m_pass", 0x17, "HID MOUSE ....... PASS\n"),
]


def main() -> None:
    body = HEADER + "\n".join(pr_line(*m) for m in MSGS)
    out = Path(__file__).resolve().parents[1] / "hw/fixtures/sw/media_bench.pls"
    out.write_text(body, encoding="utf-8")
    print(f"wrote {out} ({len(body.splitlines())} lines)")


if __name__ == "__main__":
    main()
