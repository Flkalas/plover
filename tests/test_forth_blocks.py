from forth.interpreter import Forth


def test_block_read_write_roundtrip():
    f = Forth()
    # store 'A' into block 3 offset 7
    f.eval_line("65 3 7 BLK!")
    f.eval_line("3 7 BLK@")
    assert f.pop() == 65


def test_emit_and_key():
    f = Forth()
    f.input_bytes = [ord("Z")]
    f.eval_line("KEY EMIT")
    assert "".join(f.output) == "Z"

