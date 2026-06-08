; HID smoke — INJECT 'A', POLL, KEY_READ (zero-page constants)

        .ORG $00E0
start:
        LDA  c_type_key
        STIO $04
        LDA  c_char_a
        STIO $05
        LDA  c_hid_inject
        STIO $01
        LDA  c_hid_poll
        STIO $01
        LDA  c_hid_key_read
        STIO $01
        HALT

c_type_key:   .DB $00
c_char_a:     .DB $41
c_hid_inject: .DB $43
c_hid_poll:   .DB $40
c_hid_key_read:.DB $41
