#!/usr/bin/env python3
"""Interactive quiz: SYS / phase / datapath / ustep misconceptions.

Non-normative teaching aid. Run:  python clock_datapath_quiz.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    id: str
    topic: str
    prompt: str
    choices: tuple[str, ...]  # A, B, C, ...
    correct: str  # e.g. "B"
    why_correct: str
    if_wrong: dict[str, str]  # choice -> misconception correction
    takeaway: str


QUESTIONS: tuple[Question, ...] = (
    Question(
        id="Q1",
        topic="숫자 의미",
        prompt=(
            "Gi1에서 ADD가 SYS 2 MHz일 때 대략 '0.7'이라고 말할 때,\n"
            "    이 0.7은 보통 무엇을 가리키나요?"
        ),
        choices=(
            "A) IPC = 0.7 (매크로당 평균 0.7 SYS)",
            "B) 처리량 ~= 0.7 M macros/s  (대략 2e6/3)",
            "C) USTEP이 SYS의 0.7배",
            "D) CPLD macrocell 사용률 70%",
        ),
        correct="B",
        why_correct=(
            "ADD는 대략 3 SYS/매크로 → macros/s ~= 2e6/3 ~= 0.67 M.\n"
            "    사람들이 말한 '0.7'은 대개 이 처리량입니다."
        ),
        if_wrong={
            "A": (
                "IPC는 macros/SYS_cycles 입니다. ADD면 IPC ~= 1/3 ~= 0.33 이지\n"
                "    0.7이 아닙니다. 0.7과 0.33을 자주 섞어 부릅니다."
            ),
            "C": "클럭 비율(2x 등)과 macros/s(0.7 M)는 다른 축입니다.",
            "D": "MC 사용률과는 무관합니다.",
        },
        takeaway="0.7 ~= M macros/s (처리량). ADD의 IPC ~= 0.33.",
    ),
    Question(
        id="Q2",
        topic="IPC 정의",
        prompt="교육용으로 쓰기로 한 IPC 정의는?",
        choices=(
            "A) IPC = macros / USTEP_cycles",
            "B) IPC = macros / SYS_cycles",
            "C) IPC = f_USTEP / f_SYS",
            "D) IPC = phase 개수",
        ),
        correct="B",
        why_correct=(
            "분모는 datapath 클럭(SYS)에 보이는 사이클입니다.\n"
            "    USTEP은 제어 오버헤드라 분모에 넣지 않습니다."
        ),
        if_wrong={
            "A": (
                "USTEP을 분모에 넣으면 'CU를 빨리 돌릴수록 IPC가 떨어져 보이는'\n"
                "    이상한 교육이 됩니다. 그래서 SYS-visible만 셉니다."
            ),
            "C": "그건 클럭 배수(ratio)이지 IPC가 아닙니다.",
            "D": "phase 개수는 비용의 원인이 될 수 있지만 IPC 정의 자체는 아닙니다.",
        },
        takeaway="IPC = macros / SYS_cycles.  macros/s = f_SYS / SYS_cycles.",
    ),
    Question(
        id="Q3",
        topic="3-phase의 의미",
        prompt="ADD가 3-phase라는 말은 무엇을 뜻하나요?",
        choices=(
            "A) ALU/버스 datapath 일을 SYS에서 반드시 3번 한다",
            "B) CU FSM이 논리적으로 3단계를 거치며, 지금은 그 단계가 SYS 틱에 묶여 있다",
            "C) 클럭이 3 MHz다",
            "D) opcode가 3바이트라서 3 phase다",
        ),
        correct="B",
        why_correct=(
            "규범상 ADD는 ALU_REG 3-phase이고, ph0-1은 idle·ph2만 ALU+REG_WE입니다.\n"
            "    '3번 datapath'가 아니라 'CU 단계 3번이 SYS에 묶임'에 가깝습니다."
        ),
        if_wrong={
            "A": (
                "이게 가장 흔한 오해입니다. 규범 스트로브표: ph0-1 idle, ph2만 DP.\n"
                "    datapath 필수 칸과 CU phase 칸을 같게 보면 안 됩니다."
            ),
            "C": "SYS는 2 MHz입니다.",
            "D": "명령 길이와 phase 수는 직접 1:1이 아닙니다 (ADD는 imm이 있어도 3-phase 템플릿).",
        },
        takeaway="phase = CU 단계. 지금은 SYS에 묶임. DP 필요 여부는 phase마다 다름.",
    ),
    Question(
        id="Q4",
        topic="datapath가 있는 칸",
        prompt="규범 기준 ADD execute에서 datapath 스트로브가 있는 phase는?",
        choices=(
            "A) ph0, ph1, ph2 모두",
            "B) ph0만",
            "C) ph2만 (ph0-1 idle)",
            "D) 없음 (순수 CU)",
        ),
        correct="C",
        why_correct="microcode-spec: ALU_REG(ADD) ph0-1 idle, ph2에 Y_OE/REG_WE/FLG_WE/ALU.",
        if_wrong={
            "A": "3-phase = 3번 DP라고 착각한 경우입니다. idle phase가 있습니다.",
            "B": "ph0은 idle입니다.",
            "D": "ph2는 분명히 ALU+REG_WE datapath입니다.",
        },
        takeaway="ADD의 '줄일 여지'는 주로 ph0-1 (CU-only로 보이는 칸).",
    ),
    Question(
        id="Q5",
        topic="왜 느린가",
        prompt=(
            "ADD 처리량이 ~0.67 M macros/s로 낮은 주된 구조적 이유는?"
        ),
        choices=(
            "A) ALU가 500 ns 안에 못 끝나서 일부러 3번 돌린다",
            "B) CU phase가 SYS에 묶여 idle 칸도 SYS 분모에 포함된다",
            "C) Flash에서 마이크로코드를 3번 fetch한다",
            "D) PLL이 없어서",
        ),
        correct="B",
        why_correct=(
            "공유 클럭이라 CU 한 step = SYS 한 tick.\n"
            "    idle이어도 SYS_cycles에 잡혀 macros/s = f_SYS/3."
        ),
        if_wrong={
            "A": (
                "타이밍 문서상 ADD path는 2 MHz 예산 안입니다.\n"
                "    'ALU가 느려서 3 phase'가 주원인은 아닙니다."
            ),
            "C": "Gi1은 Flash $4000 CW를 쓰지 않고 CPLD FSM입니다.",
            "D": "PLL 없음은 설계 선택이지, 3-phase 비용의 직접 원인이 아닙니다.",
        },
        takeaway="병목 서사: phase-bound-to-SYS (특히 idle 포함 계수).",
    ),
    Question(
        id="Q6",
        topic="ustep이 하는 일",
        prompt="related-clock ustep의 올바른 설명은?",
        choices=(
            "A) CU 클럭을 3배로 하면 3개 datapath 일을 1 SYS 주기에 전부 수행한다",
            "B) CU 제어 step을 USTEP으로 옮기고, 버스/ALU 스트로브만 SYS 정렬 창에서 연다",
            "C) SYS를 6 MHz로 올려 IPC 정의를 바꾼다",
            "D) 두 번째 크리스털로 비동기 CU를 돌리는 것이 기본안이다",
        ),
        correct="B",
        why_correct=(
            "USTEP = 제어 오버헤드, SYS = datapath 창.\n"
            "    related ÷N (같은 OSC)이 baseline. async CDC는 fallback."
        ),
        if_wrong={
            "A": (
                "핵심 오해입니다. SYS 한 주기 = datapath 창은 보통 1번입니다.\n"
                "    CU만 빨리 돈다고 ALU/MEM을 같은 SYS 칸에 3번 넣을 수 없습니다."
            ),
            "C": "연구 baseline은 f_SYS=2 MHz 유지. IPC 분모도 SYS.",
            "D": "기본안은 같은 크리스털+분주. 비동기 듀얼 OSC는 fallback.",
        },
        takeaway="[NO] 3 DP in 1 SYS.  [YES] move CU bookkeeping off SYS denominator.",
    ),
    Question(
        id="Q7",
        topic="2x면 충분한가",
        prompt="CLK_USTEP = 2 * CLK_SYS 만으로도 '되는' 것과 '안 되는' 것은?",
        choices=(
            "A) 됨: related sync / SYS 정렬.  안 됨(자동은 아님): 임의의 긴 CU step을 항상 1 SYS 벽시계에 끝냄",
            "B) 2x면 ADD datapath를 반드시 1 SYS로 보장한다",
            "C) 2x면 MEM_LD도 1 SYS로 줄어든다",
            "D) 2x는 부족하고 반드시 PLL이 필요하다",
        ),
        correct="A",
        why_correct=(
            "2x는 BOM(4 MHz→÷2)과 맞고 sync tax~=0에 충분합니다.\n"
            "    다만 CU 내부 step이 많으면 wall-time은 더 길 수 있습니다."
        ),
        if_wrong={
            "B": "datapath 1 SYS는 'ph0-1이 진짜 idle' lab 가정이지 2x의 자동 결과 아님.",
            "C": "MEM_LD는 ph0/ph1 둘 다 DP → SYS~=2 유지.",
            "D": "PLL 불필요. 배수 더 필요하면 OSC만 키우고 ÷N.",
        },
        takeaway="2x = 좋은 시작 구조. IPC 숫자 보장은 lab+템플릿 문제.",
    ),
    Question(
        id="Q8",
        topic="opcode별 DP",
        prompt="µstep으로 SYS-visible이 잘 안 줄어드는 쪽은?",
        choices=(
            "A) ADD/CMP (ph0-1 idle 가능)",
            "B) LDA/STA (매 phase DP)",
            "C) 둘 다 동일하게 3→1로 줄어든다",
            "D) HALT만 DP-bound",
        ),
        correct="B",
        why_correct="MEM_LD/ST는 두 phase 모두 버스/레지스터 스트로브. 옮길 idle이 거의 없음.",
        if_wrong={
            "A": "ADD/CMP가 오히려 desk에서 줄일 여지가 큰 쪽입니다.",
            "C": "opcode마다 e-IPC가 다르다는 게 교육 포인트입니다.",
            "D": "HALT는 거의 예외. MEM/CALL/BEQ 등이 DP-bound.",
        },
        takeaway="MEM·스택·(많은) 분기 = SYS-bound. ADD idle = 후보.",
    ),
    Question(
        id="Q9",
        topic="desk vs lab",
        prompt=(
            "연구 모델이 ADD를 3→1 SYS로 잡은 것에 대해 맞는 태도는?"
        ),
        choices=(
            "A) 규범이 이미 1 SYS로 바뀌었다",
            "B) desk 낙관: ph0-1이 책갈피라면. 빵판에서 settle에 필요하면 uplift 붕괴",
            "C) USTEP 4 MHz면 무조건 2.0 M macros/s",
            "D) sync1(async tax)이 기본 목표 숫자다",
        ),
        correct="B",
        why_correct=(
            "SUMMARY: Conditional Go. lab에서 movable vs required settle 검증 필요.\n"
            "    related-clock sync0 balanced +69%가 desk bound."
        ),
        if_wrong={
            "A": "normative phase table은 바꾸지 않았습니다 (연구 only).",
            "C": "f_USTEP만으로는 macros/s가 안 오릅니다. SYS-visible이 줄어야 함.",
            "D": "sync0(related)가 primary. sync1은 fallback.",
        },
        takeaway="모델 = 가설. 규범 변경 전 lab gate.",
    ),
    Question(
        id="Q10",
        topic="종합",
        prompt="다음 중 맞는 문장만 고르세요.",
        choices=(
            "A) CU만 3배 빠르게 하면 모든 opcode가 IPC=1이 된다",
            "B) SYS에 묶인 CU idle phase가 ADD 비용을 키우고, ustep은 그 제어를 SYS 분모 밖으로 빼려는 시도다",
            "C) datapath가 필요한 opcode는 ADD뿐이다",
            "D) IPC 분모는 USTEP이다",
        ),
        correct="B",
        why_correct="이 대화 전체의 한 줄 요약입니다.",
        if_wrong={
            "A": "MEM/CALL 등은 DP 칸이 남습니다. IPC=1 보장 없음.",
            "C": "LDA/STA/BEQ/JMP/CALL/RET 등 대부분 execute에 DP가 있습니다.",
            "D": "분모는 SYS.",
        },
        takeaway="기억: phase≠DP, IPC분모=SYS, ustep=제어 이동(압축 마법 아님).",
    ),
)


def setup_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return "q"


def grade_one(q: Question) -> tuple[bool, str]:
    print()
    print("=" * 64)
    print(f"  {q.id}  [{q.topic}]")
    print("=" * 64)
    print()
    print("  " + q.prompt.replace("\n", "\n  "))
    print()
    for line in q.choices:
        print(f"    {line}")
    print()
    print("  (답: A/B/C/D  ·  s=건너뛰기  ·  q=종료)")

    while True:
        raw = ask("답> ").upper()
        if raw == "Q":
            return False, "q"
        if raw == "S":
            print("  (skip)")
            return False, "s"
        # allow "A)" or "a"
        if raw and raw[0] in "ABCD":
            ans = raw[0]
            break
        print("  A/B/C/D 중 하나를 입력하세요.")

    ok = ans == q.correct
    print()
    if ok:
        print("  >> 맞음")
    else:
        print(f"  >> 다름 (선택한 답: {ans}, 정답: {q.correct})")
        if ans in q.if_wrong:
            print()
            print("  [오개념 교정]")
            print("  " + q.if_wrong[ans].replace("\n", "\n  "))
    print()
    print("  [왜 정답인가]")
    print("  " + q.why_correct.replace("\n", "\n  "))
    print()
    print("  [한 줄]")
    print(f"  {q.takeaway}")
    ask("\nEnter=계속  ")
    return ok, ans


def print_profile(results: list[tuple[Question, bool, str]]) -> None:
    print()
    print("#" * 64)
    print("  이해도 프로필")
    print("#" * 64)

    wrong_topics: list[str] = []
    for q, ok, ans in results:
        mark = "OK" if ok else "MISS"
        print(f"  [{mark}] {q.id} {q.topic}")
        if not ok and ans not in ("s", "q", ""):
            wrong_topics.append(q.topic)

    print()
    if not results:
        print("  (풀한 문항 없음)")
        return

    n_ok = sum(1 for _, ok, _ in results if ok)
    print(f"  점수: {n_ok}/{len(results)}")
    print()

    # misconception buckets
    hints = []
    missed = {q.id for q, ok, _ in results if not ok}
    if "Q1" in missed or "Q2" in missed:
        hints.append(
            "- 숫자 축이 흔들림: '0.7' = macros/s, IPC(ADD)~=0.33, 분모=SYS.\n"
            "  → clock_datapath_timeline.py 에서 ADD step 1-3을 다시 보세요."
        )
    if "Q3" in missed or "Q4" in missed or "Q5" in missed:
        hints.append(
            "- phase와 datapath를 동일시하는 중일 수 있음.\n"
            "  → ADD: ph0/ph1은 DP=--- , ph2만 DP. '3-phase != 3x ALU'."
        )
    if "Q6" in missed or "Q7" in missed or "Q10" in missed:
        hints.append(
            "- ustep을 '한 SYS에 DP 3번'으로 오해하는 패턴.\n"
            "  → 메뉴 9번 ADD@ustep: 제어는 USTEP, DP는 SYS 한 칸."
        )
    if "Q8" in missed:
        hints.append(
            "- opcode 전부 같다고 보는 중일 수 있음.\n"
            "  → LDA vs ADD timeline 비교."
        )
    if "Q9" in missed:
        hints.append(
            "- desk 모델 숫자를 규범/확정으로 받아들인 상태일 수 있음.\n"
            "  → Conditional Go / lab gate 문장만 다시 읽기."
        )

    if hints:
        print("  다음에 보면 좋은 것:")
        for h in hints:
            print()
            print("  " + h.replace("\n", "\n  "))
    else:
        print("  핵심 축(처리량/IPC/phase/DP/ustep)은 대체로 정렬된 편입니다.")
    print()


def main() -> None:
    setup_stdout()
    print()
    print("Plover quiz - 내가 뭘 오해했는지 찾기")
    print("(research/cpld-ustep / non-normative)")
    print()
    print("  모르는 척하지 말고, 지금 믿는 답을 고르세요.")
    print("  틀린 뒤의 [오개념 교정]이 본편입니다.")
    print()
    print("  1) 전체 퀴즈 (Q1-Q10)")
    print("  2) 짧은 진단 (Q1,Q3,Q6,Q8만)")
    print("  q) 종료")
    print()

    mode = ask("선택> ").strip().lower()
    if mode == "q":
        return
    if mode == "2":
        ids = {"Q1", "Q3", "Q6", "Q8"}
        qs = [q for q in QUESTIONS if q.id in ids]
    else:
        qs = list(QUESTIONS)

    results: list[tuple[Question, bool, str]] = []
    for q in qs:
        ok, ans = grade_one(q)
        if ans == "q":
            break
        if ans == "s":
            continue
        results.append((q, ok, ans))

    print_profile(results)
    print("끝. timeline: python clock_datapath_timeline.py")
    print()


if __name__ == "__main__":
    main()
