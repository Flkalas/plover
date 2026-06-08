        .ORG 0
main:   CALL sub
        ADD 10
        MOV 2
        HALT
sub:    ADD 1
        MOV 2
        RET
