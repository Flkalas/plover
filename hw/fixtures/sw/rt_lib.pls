; Runtime syscall library — vector table @ $1000 (see docs/runtime-api.md)
; Calling convention: R0–R3 = args; CALL label; returns via RET.

        .ORG $1000
vec_rt_cls:         .DW rt_cls
vec_rt_print_str:   .DW rt_print_str
vec_rt_vsync:       .DW rt_vsync
vec_rt_sprite_set:  .DW rt_sprite_set
vec_rt_frame_flush: .DW rt_frame_flush
vec_rt_sound_play:  .DW rt_sound_play

rt_cls:
        LDA  c_attr
        STIO $02
        LDA  c_vdu_cls
        STIO $01
        RET

rt_print_str:
        STIO $02
        LDA  c_vdu_print
        STIO $01
        RET

rt_vsync:
        LDA  c_vdu_vsync
        STIO $01
        RET

rt_sprite_set:
        STIO $02
        MOV  $01
        STIO $04
        MOV  $02
        STIO $05
        MOV  $03
        STIO $06
        LDA  c_zero
        STIO $07
        LDA  c_zero
        STIO $08
        LDA  c_one
        STIO $09
        LDA  c_gfx_oam
        STIO $01
        RET

rt_frame_flush:
        LDA  c_gfx_flush
        STIO $01
        RET

rt_sound_play:
        STIO $04
        MOV  $01
        STIO $05
        MOV  $02
        STIO $06
        LDA  c_vol
        STIO $07
        MOV  $03
        STIO $08
        LDA  c_zero
        STIO $09
        LDA  c_apu_note
        STIO $01
        LDA  c_apu_sync
        STIO $01
        RET

c_attr:       .DB $07
c_zero:       .DB $00
c_one:        .DB $01
c_vol:        .DB $0C
c_vdu_cls:    .DB $10
c_vdu_print:  .DB $14
c_vdu_vsync:  .DB $30
c_gfx_oam:    .DB $2A
c_gfx_flush:  .DB $2C
c_apu_note:   .DB $54
c_apu_sync:   .DB $52
