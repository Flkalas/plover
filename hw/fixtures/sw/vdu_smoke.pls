; VDU smoke — CLS, PUTCH 'H', VSYNC (constants in zero page; LDA addr8)

        .ORG $00E0
start:
        LDA  c_attr
        STIO $02          ; MB_PARAM
        LDA  c_vdu_cls
        STIO $01          ; MB_CMD
        LDA  c_char_h
        STIO $02
        LDA  c_vdu_putch
        STIO $01
        LDA  c_vdu_vsync
        STIO $01
        HALT

c_attr:     .DB $07
c_vdu_cls:  .DB $10
c_char_h:   .DB $48
c_vdu_putch:.DB $11
c_vdu_vsync:.DB $30
