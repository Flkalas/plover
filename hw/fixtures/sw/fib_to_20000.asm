; 16-bit Fibonacci until next term > 20000. Result: W1 = 17711 (0x452F).
; Init: runner sets W0=0, W1=1.
    WADD_RR
    WMOV 0x02
    WCMP16 20001
    BCS 15
    WMOV 0x01
    WMOV 0x12
    JMP 0
    HALT
