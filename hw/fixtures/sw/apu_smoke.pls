; APU smoke — SET_CTRL, CH_WRITE ch0 ~1 kHz, SYNC (zero-page constants)

        .ORG $00E0
start:
        LDA  c_master
        STIO $04          ; MB_BUFFER[0]
        LDA  c_flags
        STIO $05          ; MB_BUFFER[1]
        LDA  c_apu_ctrl
        STIO $01          ; MB_CMD APU_SET_CTRL
        LDA  c_ch
        STIO $04
        LDA  c_period_lo
        STIO $05
        LDA  c_period_hi
        STIO $06
        LDA  c_vol
        STIO $07
        LDA  c_wave
        STIO $08
        LDA  c_apu_write
        STIO $01
        LDA  c_apu_sync
        STIO $01
        HALT

c_master:     .DB $0F
c_flags:      .DB $00
c_apu_ctrl:   .DB $50
c_ch:         .DB $00
c_period_lo:  .DB $16       ; 22 = ~1 kHz @ 44.1 kHz clk
c_period_hi:  .DB $00
c_vol:        .DB $0F
c_wave:       .DB $01       ; square
c_apu_write:  .DB $51
c_apu_sync:   .DB $52
