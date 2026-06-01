from kern.serial import SIG_UART, ST_RX_READY, ST_TX_READY, SerialModule


def test_serial_signature_and_status():
    s = SerialModule()
    assert s.signature == SIG_UART
    st = s.status()
    assert st & ST_TX_READY
    assert not (st & ST_RX_READY)


def test_serial_tx_rx_polling():
    s = SerialModule()
    s.tx(0x41)
    assert s.tx_fifo[-1] == 0x41
    s.inject_rx(b"Z")
    assert s.rx_ready()
    assert s.rx() == ord("Z")

