from forth.interpreter import Forth


def test_stack_ops():
    f = Forth()
    f.eval_line("1 2 SWAP")
    assert f.data == [2, 1]
    f.eval_line("DUP")
    assert f.data == [2, 1, 1]
    f.eval_line("DROP")
    assert f.data == [2, 1]


def test_arith():
    f = Forth()
    f.eval_line("2 3 +")
    assert f.data == [5]
    f.eval_line("10 4 -")
    assert f.data == [5, 6]
    f.eval_line("6 7 *")
    assert f.data[-1] == 42

