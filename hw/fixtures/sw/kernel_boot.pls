; Kernel entry stub @ $0800 (boot-jmp-handoff.md §5.3)

        .ORG $0800
KERNEL_BOOT:
        CMP  $00
        JMP  KERNEL_MAIN

KERNEL_MAIN:
        HALT
