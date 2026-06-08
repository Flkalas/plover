; Fibonacci: iterate until next > 200. Halt with R1 = last value <= 200 (144).
; RAM 0x20=0, 0x21=1 preloaded by runner.
    LDA 0x21
    MOV 0x10
    LDA 0x20
    ADD_RR
    MOV 0x02
    CMP 201
    BCS 20
    MOV 0x01
    MOV 0x12
    JMP 6
    HALT
