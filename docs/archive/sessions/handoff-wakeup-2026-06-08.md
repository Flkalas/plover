# 일어나서 여기서부터 — 작업 인수인계

**작성:** 2026-06-08 (취침 전 세션)  
**주제:** `media_bench.pls` NES Diagnostic화 + `play` / PL-DOS GUI / Presenter 수정  
**Normative:** [`demo-program-spec.md`](../../software/demo-program-spec.md) · 계획 [`../.cursor/plans/media_bench_play_demo_bc7686ad.plan.md`](../.cursor/plans/media_bench_play_demo_bc7686ad.plan.md)

---

## 한 줄 요약

**트랙 A(Plover Diagnostic)는 코드·headless 테스트까지 끝났습니다.**  
일어나면 **SDL로 한 번 눈으로 확인** → **`cargo test --workspace` / `pytest` 회귀** → **커밋·PR 정리** 순서가 가장 자연스럽습니다.  
**아직 Git 커밋은 없습니다** (변경 파일 많음, unstaged/untracked 혼재).

---

## 완료한 것 ✅

### 1. `media_bench.pls` → Plover Diagnostic (NES-style)

| 항목 | 내용 |
|------|------|
| 부트 화면 | `PLOVER DIAGNOSTIC` + 구분선 |
| 자동 테스트 | VDU TEXT / VSYNC / GFX FILL+GETPIX @ (10,**20**) / APU CH0 — PASS·FAIL 행 |
| HID | `HID KEY ... RUN` / `HID MOUSE ... RUN` → **첫 입력만** PASS (motion마다 `M` 범람 제거) |
| HALT | 없음 — `interact_loop` 무한 |

**생성·수정 경로**

- 소스: [`hw/fixtures/sw/media_bench.pls`](../hw/fixtures/sw/media_bench.pls) (1370줄, `tools/gen_media_bench.py`로 print 루틴 재생성)
- Hex: [`hw/fixtures/sram/media_bench.sram.hex`](../hw/fixtures/sram/media_bench.sram.hex)
- Headless gate: [`crates/plover_vm/tests/media_bench_play.rs`](../crates/plover_vm/tests/media_bench_play.rs) — **통과 확인됨**

```powershell
cargo test -p plover_vm media_bench_play
```

### 2. 어셈블러·asm 함정 수정

- **`plover_asm/assemble.py`**: forward `.ORG` 시 **0 패딩** (다중 ORG 프로그램 정렬)
- **ZP 29B + `c_pad`**: `$E3–$FF` 상수 뒤 코드가 `$0100`에서 시작하도록 정렬
- **문자열 출력**: `LDA $50` 같은 표기는 **RAM[0x50] 로드**이지 즉값이 아님 → `LDA 0` / `ADD imm` / `MOV $02` / `STIO` 패턴으로 교체

### 3. Presenter / VM / PL-DOS (같은 세션에서 같이 수정됨)

| 영역 | 변경 요약 |
|------|-----------|
| `plover_presenter` | `font8x8`, MODE_BOTH 공백 셀 비트맵 통과, cpal F32/I16/U8, SDL TextInput |
| `plover_vm` `play` | 기본 `--max-steps 0`(무한), `--audio`, `dos-shell --gui` |
| `plover_os` | kprint `\n`, 40열 줄바꿈, Enter 후 커서, 40열 이중 `\n` 방지 |

### 4. 문서

- [`docs/software/demo-program-spec.md`](../../software/demo-program-spec.md) §5 — **v0.2 Plover Diagnostic** 명세
- [`docs/simulation/vm-rust.md`](../../simulation/vm-rust.md), [`README.md`](../README.md) — `play --pls media_bench` 실행 예 + demo-program-spec 링크
- [`docs/software/dos-shell.md`](../../software/dos-shell.md) — `--gui` 사용법

---

## 아직 안 한 것 / 다음 작업 🔲

우선순위 순.

### P0 — 아침에 10분 sanity check

```powershell
cd D:\Github\plover

# 1) headless (이미 통과했지만 재확인)
cargo test -p plover_vm media_bench_play

# 2) SDL + 오디오 — 눈·귀로 확인 (아직 수동 검증 안 함)
cargo run -p plover_vm --features sdl,audio -- play --pls hw/fixtures/sw/media_bench.pls --audio
```

**눈으로 볼 것**

- [ ] 타이틀 `PLOVER DIAGNOSTIC`, 구분선
- [ ] 자동 PASS 행 4줄 (VDU TEXT / VSYNC / GFX / APU)
- [ ] HID KEY / MOUSE `... RUN` 행
- [ ] (10, 20) 근처 **빨간 8×8** 사각형
- [ ] 키 입력 → echo + **비프** + `HID KEY ... PASS`
- [ ] 마우스 **첫 motion/클릭** → `HID MOUSE ... PASS` (M 글자 범람 없어야 함)

### P1 — 회귀 테스트

```powershell
cargo test --workspace
python -m pytest tests/ -q
```

전체 워크스페이스·Python oracle은 **이 세션에서 돌리지 않음**. PR 전 필수.

### P2 — Git 정리

- **커밋 없음** — 원하면 논리별로 나눠 커밋 권장:
  1. `media_bench` + `gen_media_bench.py` + hex + asm ORG fix
  2. `plover_presenter` / `play` / audio
  3. `plover_os` shell
  4. docs
- `.cursor/plans/media_bench_play_demo_bc7686ad.plan.md` 는 아직 **§5 “미작성”** 등 구버전 문구 — [`demo-program-spec.md`](../../software/demo-program-spec.md) 기준으로 **completed/pending 갱신** 필요

### P3 — 선택 (여유 있을 때)

| 항목 | 설명 |
|------|------|
| `hw/scenarios/vm/media_bench.yaml` | YAML 시나리오 게이트 (지금은 Rust integration test만) |
| SDL mouse UX | [`sdl_window.rs`](../crates/plover_presenter/src/sdl_window.rs) — motion 대신 **클릭만** inject |
| `gen_media_bench.py` | 문자열 바꿀 때만 실행; CI에 넣을지 결정 |
| `add_imm.sram.hex` 변경 | git diff에 포함됨 — 의도치 않으면 revert |

---

## 알려진 함정 / 참고

| 현상 | 원인·대응 |
|------|-----------|
| asm에서 `LDA $58` | 주소 0x58 **메모리** 로드. 문자 `'X'`는 `LDA 0` + `ADD $58` |
| `.ORG $0100` + ZP 28B만 | 코드가 `$FF`에서 1바이트 밀림 → **`c_pad` 필수** |
| `LDA label` (label > 0xFF) | 주소 **하위 8비트만** 사용 — 고주소 rodata는 이 ISA로 직접 못 읽음 |
| headless 80k steps | 자동 테스트+print 루틴이 김 — `media_bench_play.rs`의 `80_000` 유지 |
| `play --origin 0xE0` | 부트 `JMP` @ `$E0`; 상수 `$E3+` — [`software-memory-layout.md`](software-memory-layout.md)와 일치 확인 |

---

## 주요 파일 지도

```
hw/fixtures/sw/media_bench.pls     ← Diagnostic 본체 (generated print 블록)
tools/gen_media_bench.py           ← print 루틴 재생성
hw/fixtures/sram/media_bench.*     ← hex / lst / map
crates/plover_vm/tests/media_bench_play.rs
crates/plover_vm/src/main.rs       ← play, dos-shell --gui
crates/plover_presenter/           ← font, compose, sdl, audio
crates/plover_os/src/shell.rs      ← PL-DOS GUI kprint
plover_asm/assemble.py             ← ORG padding
docs/software/demo-program-spec.md          ← §5 normative
```

---

## Git 상태 (2026-06-08 취침 시점)

- **브랜치:** 로컬 작업 트리, **커밋 없음**
- **수정(M):** VM / presenter / copro / os / asm / docs 등 ~27 tracked files
- **미추적(??):** `media_bench.pls`, `gen_media_bench.py`, `plover_basic/`, `basic/`, `hw/fixtures/basic/`, gemini archive md 등 대량

커밋 전 `git status`로 **의도치 않은 archive·`.cargo/`** 포함 여부 확인.

---

## 실행 치트시트

```powershell
# Diagnostic (강사 시연)
cargo run -p plover_vm --features sdl,audio -- play --pls hw/fixtures/sw/media_bench.pls --audio

# PL-DOS GUI 쉘
cargo run -p plover_vm --features sdl -- dos-shell --gui

# BASIC 게임 (트랙 B — 별도 완료 상태, 회귀만)
cargo run -p plover_vm --features sdl,audio -- play --basic hw/fixtures/basic/pong.bas --audio

# asm 재빌드
python tools/gen_media_bench.py
python -m plover_asm build hw/fixtures/sw/media_bench.pls -o hw/fixtures/sram --origin 0xE0
```

---

## 세션 타임라인 (맥락)

1. `play --audio` / SDL 데모 문제 → 무한 실행, font, MODE_BOTH, audio format
2. `dos-shell --gui` — PL-DOS 글자·줄바꿈 버그
3. `media_bench` — 마우스 M 범람, 색/도형 안 보임
4. **NES Diagnostic 형태로 확장** — 자동 PASS/FAIL + HID RUN/PASS
5. 정렬·`LDA` 함정 수정 → headless test green
6. **SDL 수동 확인·전체 회귀·커밋은 미착수**

---

*이 문서는 취침 전 스냅샷입니다. 작업 후 삭제하거나 `docs/archive/`로 옮겨도 됩니다.*
