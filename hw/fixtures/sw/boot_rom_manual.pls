; Boot ROM — manual Run+RESET recovery path (bootloader.md §3)

        .ORG $0000
        JMP  manual_boot

        .ORG $0100
manual_boot:
        LDA  zero
        STA16 $FFFC
        LDA  entry_hi
        STA16 $FFFD
        HALT

zero:       .DB $00
entry_hi:   .DB $08
