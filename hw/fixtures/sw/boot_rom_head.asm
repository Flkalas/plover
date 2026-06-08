; Boot ROM head @ $0000 / $0100

        .ORG $0000
        JMP  post

        .ORG $0100
post:
        LDA  $F0
        STIO $02
        LDA  $F1
        STIO $01
poll:
        LDIO $00
        CMP  $F2
        BEQ  poll_done
        JMP  poll
poll_done:
        JMP  $0120
