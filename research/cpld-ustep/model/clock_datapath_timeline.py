#!/usr/bin/env python3
"""Interactive teaching aid: SYS / USTEP / phase / datapath, one step at a time.

Non-normative. Strobe sketch from Gi1 microcode-spec 2.2 / 4.
Run:  python clock_datapath_timeline.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Scenario data
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Step:
    """One wall-time slot in a timeline."""

    label: str  # e.g. SYS[0] or USTEP[u2]/SYS[1]
    phase: str  # ph0 / ph1 / ph2 / (internal) / -
    cu: str  # what CU does this tick
    dp: str  # --- or strobe summary
    note: str = ""


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    mode: str  # baseline | ustep
    blurb: str
    steps: tuple[Step, ...]
    summary: str


def _scenarios() -> dict[str, Scenario]:
    add_base = Scenario(
        key="ADD",
        title="ADD (baseline, shared SYS)",
        mode="baseline",
        blurb="ALU_REG 3-phase. ph0-1 idle, ph2 ALU+REG_WE. CU phase == SYS tick.",
        steps=(
            Step("SYS[0]", "ph0", "advance FSM", "---", "규범: idle (스트로브 없음)"),
            Step("SYS[1]", "ph1", "advance FSM", "---", "규범: idle"),
            Step("SYS[2]", "ph2", "advance FSM", "ALU ADD, Y_OE, REG_WE, FLG_WE", "datapath"),
        ),
        summary="SYS-visible=3 (빈 칸 포함). macros/s ~= 2e6/3 ~= 0.67 M. IPC=1/3.",
    )
    cmp_base = Scenario(
        key="CMP",
        title="CMP (baseline, shared SYS)",
        mode="baseline",
        blurb="ALU_REG 3-phase. ph0-1 idle, ph2 FLG_WE only (flags_only).",
        steps=(
            Step("SYS[0]", "ph0", "advance FSM", "---", "idle"),
            Step("SYS[1]", "ph1", "advance FSM", "---", "idle"),
            Step("SYS[2]", "ph2", "advance FSM", "ALU CMP, FLG_WE", "datapath (flags)"),
        ),
        summary="SYS-visible=3. ADD와 같이 idle 2칸이 SYS 분모에 포함.",
    )
    lda_base = Scenario(
        key="LDA",
        title="LDA / LDIO (baseline, MEM_LD)",
        mode="baseline",
        blurb="2-phase. 둘 다 datapath.",
        steps=(
            Step("SYS[0]", "ph0", "advance FSM", "MEM_RD", "버스 읽기"),
            Step("SYS[1]", "ph1", "advance FSM", "REG_WE -> R0", "레지스터 기록"),
        ),
        summary="SYS-visible=2. ustep으로도 거의 안 줄어듦.",
    )
    sta_base = Scenario(
        key="STA",
        title="STA / STIO / STA16 (baseline, MEM_ST)",
        mode="baseline",
        blurb="2-phase. 둘 다 datapath.",
        steps=(
            Step("SYS[0]", "ph0", "advance FSM", "Y_OE", "버스에 R0 구동"),
            Step("SYS[1]", "ph1", "advance FSM", "MEM_WR", "메모리 기록"),
        ),
        summary="SYS-visible=2. LDA와 동일하게 DP-bound.",
    )
    beq_base = Scenario(
        key="BEQ",
        title="BEQ (baseline)",
        mode="baseline",
        blurb="ALU SUB로 Z, macro_end에서 조건부 PC_LOAD. (위상표 2-phase 스케치)",
        steps=(
            Step("SYS[0]", "ph0", "advance FSM", "ALU SUB (Z)", "datapath"),
            Step("SYS[1]", "end", "macro_end", "PC_LOAD if FLG_Z", "datapath (PC)"),
        ),
        summary="SYS-visible>=2. idle 여유가 ADD보다 적음.",
    )
    jmp_base = Scenario(
        key="JMP",
        title="JMP (baseline, BRANCH)",
        mode="baseline",
        blurb="위상표 1-phase. PC_LOAD.",
        steps=(
            Step("SYS[0]", "end", "macro_end", "PC_LOAD_EN=1", "datapath (PC)"),
        ),
        summary="SYS-visible=1 (execute). fetch는 별도.",
    )
    call_base = Scenario(
        key="CALL",
        title="CALL (baseline + stack assist sketch)",
        mode="baseline",
        blurb="PC 분기 + macro_end RAM push (desk 스케치, 연구용).",
        steps=(
            Step("SYS[0]", "end", "BRANCH", "PC_LOAD (target)", "datapath (PC)"),
            Step("SYS[1]", "stack", "CU assist", "MEM_WR return_pc lo", "datapath (MEM)"),
            Step("SYS[2]", "stack", "CU assist", "MEM_WR return_pc hi / RP+=2", "datapath (MEM)"),
        ),
        summary="스택 MEM 때문에 SYS가 김. CU만 빨리 돌려도 크게 안 줄어듦.",
    )
    ret_base = Scenario(
        key="RET",
        title="RET (baseline + stack assist sketch)",
        mode="baseline",
        blurb="macro_end RAM pop -> PC (desk 스케치).",
        steps=(
            Step("SYS[0]", "stack", "CU assist", "RP-=2 / MEM_RD", "datapath (MEM)"),
            Step("SYS[1]", "stack", "CU assist", "PC <- popped word", "datapath (PC)"),
        ),
        summary="SYS-bound (스택). ADD형 idle 압축 대상 아님.",
    )

    add_ustep = Scenario(
        key="ADD@ustep",
        title="ADD (related-clock ustep, 2x, desk optimistic)",
        mode="ustep",
        blurb="제어는 USTEP, datapath는 SYS-aligned 창 1번. 3 phase를 1 SYS에 우겨 넣는 것 아님.",
        steps=(
            Step("USTEP[0]", "i0", "decode / enter", "---", "SYS 분모 밖"),
            Step("USTEP[1]", "i1", "bookkeep (was ph0)", "---", "예전 SYS idle"),
            Step("USTEP[2]||SYS[0]", "i2", "wait SYS align", "---", "다음 엣지에서 DP"),
            Step("USTEP[3]||SYS[0]", "exec", "qualify strobes", "ALU ADD, REG_WE, FLG_WE", "SYS-visible=1"),
            Step("USTEP[4]", "i3", "macro_end / next", "---", "다시 USTEP"),
        ),
        summary="SYS-visible=1 (desk). macros/s ~= 2.0 M if lab confirms ph0-1 truly idle.",
    )
    lda_ustep = Scenario(
        key="LDA@ustep",
        title="LDA (ustep) - still 2 SYS DP slots",
        mode="ustep",
        blurb="MEM은 두 칸 모두 DP. USTEP은 사이 제어만.",
        steps=(
            Step("USTEP[0]", "i0", "prepare MEM_RD", "---", ""),
            Step("USTEP[1]||SYS[0]", "ph0", "qualify", "MEM_RD", "SYS-visible #1"),
            Step("USTEP[2]", "i1", "prepare REG_WE", "---", ""),
            Step("USTEP[3]||SYS[1]", "ph1", "qualify", "REG_WE -> R0", "SYS-visible #2"),
        ),
        summary="SYS-visible=2. baseline과 처리량 동일 계열.",
    )

    out = {
        "ADD": add_base,
        "CMP": cmp_base,
        "LDA": lda_base,
        "LDIO": lda_base,
        "STA": sta_base,
        "STIO": sta_base,
        "STA16": sta_base,
        "BEQ": beq_base,
        "JMP": jmp_base,
        "CALL": call_base,
        "RET": ret_base,
        "ADD@ustep": add_ustep,
        "LDA@ustep": lda_ustep,
    }
    return out


MENU_ORDER = [
    "ADD",
    "CMP",
    "LDA",
    "STA",
    "BEQ",
    "JMP",
    "CALL",
    "RET",
    "ADD@ustep",
    "LDA@ustep",
]


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


def _setup_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def pause(prompt: str = "Enter=다음 / b=이전 / q=메뉴로  ") -> str:
    try:
        return input(prompt).strip().lower()
    except EOFError:
        return "q"


def print_step(sc: Scenario, index: int) -> None:
    n = len(sc.steps)
    st = sc.steps[index]
    print()
    print("-" * 64)
    print(f"  [{sc.key}] step {index + 1}/{n}   mode={sc.mode}")
    print("-" * 64)
    print(f"  slot   : {st.label}")
    print(f"  phase  : {st.phase}")
    print(f"  CU     : {st.cu}")
    print(f"  DP     : {st.dp}")
    if st.note:
        print(f"  note   : {st.note}")
    # mini strip
    cells = []
    for i, s in enumerate(sc.steps):
        mark = "*" if i == index else " "
        dp = "DP" if s.dp != "---" else "--"
        cells.append(f"{mark}{s.label.split('||')[0][:8]}:{dp}")
    print()
    print("  strip: " + " | ".join(cells))


def run_scenario(sc: Scenario) -> None:
    print()
    print("=" * 64)
    print(sc.title)
    print("=" * 64)
    print(sc.blurb)
    print()
    print("한 스텝씩 진행합니다.")
    if pause("Enter로 시작 (q=취소)  ") == "q":
        return

    i = 0
    while 0 <= i < len(sc.steps):
        print_step(sc, i)
        cmd = pause()
        if cmd == "q":
            print("  (메뉴로)")
            return
        if cmd == "b":
            i = max(0, i - 1)
            continue
        if cmd in ("", "n", "s"):
            i += 1
            continue
        # number jump
        if cmd.isdigit():
            j = int(cmd) - 1
            if 0 <= j < len(sc.steps):
                i = j
            else:
                print(f"  범위: 1..{len(sc.steps)}")
            continue
        print("  키: Enter=다음, b=이전, 숫자=점프, q=메뉴")

    print()
    print("~" * 64)
    print("  끝:", sc.summary)
    print("~" * 64)
    pause("Enter로 메뉴  ")


def print_menu(scenarios: dict[str, Scenario]) -> None:
    print()
    print("=" * 64)
    print("Plover clock / datapath walkthrough (interactive)")
    print("research/cpld-ustep / non-normative")
    print("=" * 64)
    print()
    print("  opcode를 고르세요 (번호 또는 이름):")
    print()
    for n, key in enumerate(MENU_ORDER, 1):
        sc = scenarios[key]
        tag = "ustep" if sc.mode == "ustep" else "base "
        print(f"    {n:2d}. [{tag}] {key:12s}  - {sc.title}")
    print()
    print("    h. 용어")
    print("    q. 종료")
    print()


def print_glossary() -> None:
    print(
        """
  SYS tick   : datapath 클럭 (2 MHz). IPC = macros / SYS_cycles 의 분모.
  USTEP tick : CU 전용 (예: 4 MHz = 2x). IPC 분모에 안 들어감.
  phase      : CU FSM 단계. baseline에서는 한 phase ~= 한 SYS.
  DP         : 버스/ALU/REG/PC 스트로브가 있는 칸 (datapath 필요).
  cu / ---   : CU만 진행하거나 대기. baseline에선 그래도 SYS 한 칸을 씀.
  * strip    : 현재 step 위치. DP=datapath, --=idle.
"""
    )
    pause("Enter로 메뉴  ")


def resolve_choice(raw: str, scenarios: dict[str, Scenario]) -> str | None:
    raw = raw.strip()
    if not raw:
        return None
    low = raw.lower()
    if low in ("q", "quit", "exit"):
        return "q"
    if low in ("h", "help", "?"):
        return "h"
    if raw.isdigit():
        n = int(raw)
        if 1 <= n <= len(MENU_ORDER):
            return MENU_ORDER[n - 1]
        return None
    # name match (case-insensitive)
    for key in scenarios:
        if key.lower() == low:
            return key
    # allow "add ustep" style
    compact = low.replace(" ", "").replace("-", "")
    for key in scenarios:
        if key.lower().replace("@", "") == compact or key.lower() == compact:
            return key
    if compact in ("addustep", "add@ustep"):
        return "ADD@ustep"
    if compact in ("ldaustep", "lda@ustep"):
        return "LDA@ustep"
    return None


def main() -> None:
    _setup_stdout()
    scenarios = _scenarios()
    print_menu(scenarios)
    while True:
        try:
            raw = input("선택> ").strip()
        except EOFError:
            print()
            break
        choice = resolve_choice(raw, scenarios)
        if choice is None:
            print("  예: 1  /  ADD  /  ADD@ustep  /  h  /  q")
            continue
        if choice == "q":
            print("bye")
            break
        if choice == "h":
            print_glossary()
            print_menu(scenarios)
            continue
        run_scenario(scenarios[choice])
        print_menu(scenarios)


if __name__ == "__main__":
    main()
