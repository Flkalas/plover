from kern.gpio import GpioController


def test_gpio_output_bits():
    g = GpioController(direction=0x0F)
    g.set_bit(0)
    g.set_bit(2)
    assert g.read_port() & 0x0F == 0b0101
    g.clear_bit(0)
    assert g.get_bit(0) == 0


def test_gpio_input_bits():
    g = GpioController(direction=0x0F)  # bit4-7 inputs
    g.set_input_bits(mask=(1 << 5), values=(1 << 5))
    assert g.get_bit(5) == 1

