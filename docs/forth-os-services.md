# Forth OS services (S4)

Forth 위에 OS-like word를 추가해, 이후 subset C / 커널 계층에서 재사용할 I/O semantics를 고정한다.

## Block I/O (256B)

- `BLK@ (blk off -- byte)` : block `blk`의 byte offset 읽기
- `BLK! (byte blk off -- )` : block `blk`에 byte 쓰기
- `FLUSH ( -- )` : no-op (v0.1); S7에서 vFDD sector flush로 승격

## Console

- `EMIT (ch -- )` : 출력
- `KEY ( -- ch)` : 입력 (테스트에서는 host input buffer 사용)

## Tests

- `tests/test_forth_blocks.py`

