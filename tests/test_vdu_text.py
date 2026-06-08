"""Tests for VDU text mailbox commands."""

from plover_vm.memory.mailbox import MB_BUFFER, ST_ERROR, ST_READY, Mailbox
from plover_vm.memory.vdu import (
    CMD_VDU_ATTR,
    CMD_VDU_CLS,
    CMD_VDU_CURSORGET,
    CMD_VDU_GOTO,
    CMD_VDU_PRINT,
    CMD_VDU_PUTCH,
    CMD_VDU_SCROLL,
    VDU_COLS,
    VDU_ROWS,
)


def test_vdu_cls():
    mb = Mailbox()
    mb.issue_vdu(CMD_VDU_CLS, 0x1E)
    assert mb.vdu.chars[0][0] == 0x20
    assert mb.vdu.attrs[0][0] == 0x1E
    assert mb.vdu.cursor_col == 0
    assert mb.vdu.cursor_row == 0


def test_vdu_putch_and_wrap():
    mb = Mailbox()
    mb.issue_vdu(CMD_VDU_PUTCH, ord("A"))
    assert mb.vdu.chars[0][0] == ord("A")
    mb.vdu.cursor_col = VDU_COLS - 1
    mb.vdu.cursor_row = 0
    mb.issue_vdu(CMD_VDU_PUTCH, ord("B"))
    assert mb.vdu.chars[0][VDU_COLS - 1] == ord("B")
    assert mb.vdu.cursor_col == 0
    assert mb.vdu.cursor_row == 1


def test_vdu_goto():
    mb = Mailbox()
    mb.issue_vdu(CMD_VDU_GOTO, 5, aux=10)
    assert mb.vdu.cursor_col == 5
    assert mb.vdu.cursor_row == 10


def test_vdu_goto_error():
    mb = Mailbox()
    mb.issue_vdu(CMD_VDU_GOTO, 40, aux=0)
    assert mb.read(0xFF00) & ST_ERROR


def test_vdu_attr_and_print():
    mb = Mailbox()
    mb.issue_vdu(CMD_VDU_ATTR, 0xF1)
    mb.issue_vdu(CMD_VDU_PRINT, 5, buffer=b"HELLO")
    assert mb.vdu.chars[0][0] == ord("H")
    assert mb.vdu.attrs[0][4] == 0xF1


def test_vdu_scroll():
    mb = Mailbox()
    mb.issue_vdu(CMD_VDU_PUTCH, ord("X"))
    mb.vdu.cursor_row = VDU_ROWS - 1
    mb.vdu.cursor_col = 0
    mb.issue_vdu(CMD_VDU_PUTCH, ord("Y"))
    assert mb.vdu.chars[0][0] == 0x20 or mb.vdu.chars[0][0] == ord("X")
    mb.issue_vdu(CMD_VDU_SCROLL, 2)
    assert mb.vdu.chars[VDU_ROWS - 1][0] == 0x20


def test_vdu_cursorget():
    mb = Mailbox()
    mb.issue_vdu(CMD_VDU_GOTO, 3, aux=7)
    mb.issue_vdu(CMD_VDU_ATTR, 0x42)
    mb.issue_vdu(CMD_VDU_CURSORGET)
    assert mb.read(MB_BUFFER + 0) == 3
    assert mb.read(MB_BUFFER + 1) == 7
    assert mb.read(MB_BUFFER + 2) == 0x42


def test_vdu_putch_via_mailbox_write():
    mb = Mailbox()
    mb.write(MB_BUFFER, 0)  # not used for putch
    mb.write(0xFF02, ord("Z"))
    mb.write(0xFF01, CMD_VDU_PUTCH)
    assert mb.read(0xFF00) & ST_READY
    assert mb.vdu.chars[0][0] == ord("Z")
