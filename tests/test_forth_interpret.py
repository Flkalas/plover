from forth.interpreter import Forth


def test_colon_definition_square():
    f = Forth()
    f.eval_line(": SQUARE DUP * ;")
    f.eval_line("5 SQUARE .")
    assert f.output == ["25"]

