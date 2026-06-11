; Smoke test — CALL rt_cls + rt_frame_flush (inlined rt_* routines)

        .ORG $00E0
start:
        CALL rt_cls
        CALL rt_frame_flush
        HALT

rt_cls:
        LDA  c_attr
        STIO $02
        LDA  c_vdu_cls
        STIO $01
        RET

rt_frame_flush:
        LDA  c_gfx_flush
        STIO $01
        RET

c_attr:       .DB $07
c_vdu_cls:    .DB $10
c_gfx_flush:  .DB $2C
