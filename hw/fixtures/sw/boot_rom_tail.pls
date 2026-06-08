; Boot ROM tail @ $0600 — sanitize, stacks, handoff
; Constants live in head ROM @ $00F0 (8-bit LDA/STA reach)

        .ORG $0600
sanitize:
        LDA  $F0
        MOV  $10
        MOV  $20
        MOV  $30
        JMP  boot_stacks

boot_stacks:
        LDA  $F0
        STA16 $0E00
        LDA  $F3
        STA16 $0E01
        LDA  $F0
        STA16 $0F00
        LDA  $F4
        STA16 $0F01
        LDA  $F0
        MOV  $10
        MOV  $20
        MOV  $30
        JMP  $0800
