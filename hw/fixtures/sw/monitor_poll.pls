; v2.0 mailbox poll loop — MMIO @ $FF00, no IRQ
; Conceptual 6502-style mnemonics for macroasm bring-up

poll:
    LDIO  $FF00          ; MB_STATUS
    AND   #$01           ; DataReady mask
    BEQ   poll
    LDIO  $FF01          ; MB_CMD (consume)
    ; ... dispatch READ/WRITE via MB_PARAM + MB_BUFFER ...
    JMP   poll
