# Plover v1.1 — 아키텍처 타협·BOM 재압축

**버전:** 1.1 · **기준일:** 2026-05-31  
**목표:** Apple II급 **OS 가능** 최소 요건 (64KB 논리 공간, 서브루틴, I/O) + **브레드보드 실장 가능** IC 수  
**전제:** v1.0 GPR·16b 병렬 MUX 폐기 → **단일 ACC + 시분할 MBR**

관련: [microcode-spec-v1.1.md](microcode-spec-v1.1.md) · [v1.1-implementation-plan.md](v1.1-implementation-plan.md) · [BOM.md](../BOM.md)

---

## 1. 채택·배제 요약

| 모델 | 결정 | 이유 |
|------|------|------|
| **단일 ACC** | ✅ v1.1 **minimal** | 최소 BOM — fallback |
| **ACC + TMP (v1.2)** | ✅ **권장** | §7 — 157×4 B-mux, +5 IC |
| **IR/MDR 병합 (MBR)** | ✅ **채택** | 574×1 시분할 — fetch byte / mem data |
| **8b PCL + PCH + µcode 간접 주소** | ✅ **채택** | 16b AddrMUX×4 대신 PCH 574×1 + 저위 157×2 |
| **소프트웨어 스택 (Zero Page)** | ✅ **채택** | 74HC193 SP 하드웨어 **미채택** |
| **폴링 I/O** | ✅ **채택** | IRQ·섀도우 FSM **미채택** |
| **Phase Collapsing + ACC datapath** | ✅ **유지** | v1.0 microarch — Prefetch 제외 |
| **게이트 ALU (alu8)** | ✅ **기본** | hwsim 11 tests — **학습·검증 경로** |
| **LUT ALU (Flash lookup)** | 📋 **대안 (Track B)** | BOM −~19 IC 가능 — 별도 gate |
| **비트 시리얼** | ❌ **배제** | ~0.05 MIPS — OS 목표와 양립 불가 |

---

## 2. 타협 모델 상세

### 2.1 단일 누산기 (ACC)

| v1.0 | v1.1 |
|------|------|
| 4×574 GPR + 8×153 A/B MUX + 4×153 B-src | **1×574 ACC** (B3c [`alu_b3_clock`](../hw/netlist/blocks/alu_b3_clock.yaml)와 동일) |
| `src/dst_reg` CW 필드 | **고정** — 모든 ALU·MEM op는 ACC |

**연산:** `LOAD` → MEM→ACC, `ADD` → ACC←ACC op MEM/imm, `STORE` → ACC→MEM.  
**CPI:** MOV/GPR 없음 → **메모리 micro-step 증가** — Collapsing floor **~0.5–0.8 MIPS** realistic (LOAD/STORE mix).

### 2.2 MBR (IR + MDR 병합)

단일 `74HC574` — FSM phase로 역할 전환:

| Phase | MBR.D | MBR.Q 사용 |
|-------|-------|------------|
| Fetch0 | SRAM | opcode byte → Flash addr prep |
| Fetch1 | SRAM | operand byte |
| Exec MEM | SRAM | read data → ALU A 또는 write buffer |

16-bit 매크로 명령 = **Fetch0 + Fetch1** (2 byte sequential fetch). 별도 IR 574×2 **불필요**.

### 2.3 16-bit 논리 주소 (64KB) — 배선 절감

```
A[15:8] ← PCH (574, µcode로 갱신)
A[7:0]  ← 157×2 MUX: PC_lo vs effective_lo
```

- **PCL:** `74HC161×2` (8-bit), fetch 시 INC  
- **PCH:** `74HC574×1`, CALL/RET/JMP far 시 micro-sequence로 ±1  
- **간접:** Zero Page `$00–$FF`에 `(ptr_lo, ptr_hi)` — 6502 **zp indirect** 유사  
- **16b AddrMUX×4 (48+ wire)** → **157×2 + PCH bus 8** 로 축소

### 2.4 OS 최소 요건 vs 타협

| OS 요건 | 6502 하드웨어 | **Plover v1.1** |
|---------|---------------|-----------------|
| 64KB space | 16b addr | PCL+PCH + zp indirect ✅ |
| 서브루틴 | HW stack (SP) | **SW stack** @ `$0100` page, µcode CALL/RET |
| 인터럽트 | IRQ/NMI | **Polling** @ MMIO `STAT` — 단순 OS·모니터 가능 |
| ACC | A reg | **ACC 574** ✅ |
| Indexed X/Y | 2 index regs | **없음** — zp + offset in operand (CPI↑) |

Apple II **동급 “가능”** = BASIC/모니터/단순 배치 OS — **게임·GUI full speed 아님**.

### 2.5 LUT ALU (Track B — optional)

| | Gate ALU (Track A) | LUT ALU (Track B) |
|--|-------------------|-------------------|
| IC | 283×2, 153×4, 86×4, … **20** | **+1 Flash** (ALU ROM), ACC path only |
| hwsim | ✅ `alu8_*` | 신규 `alu_lut.yaml` |
| 학습 가치 | 높음 | 낮음 (comb ROM) |
| 타이밍 | 228 ns path 검증됨 | Flash 70 ns + 8b out |

**권장:** Track A로 CPU 통합 **PASS 후** Track B 실험. v1.1 **기본 BOM = Track A**.

---

## 3. BOM Δ (v1.0 → v1.1)

| 부품 | v1.0 | v1.1 | Δ |
|------|------|------|---|
| 74HC574 | 9 | **4** | −5 (GPR×4, IR×1) |
| 74HC153 | 16 | **4** | −12 (regfile MUX) |
| 74HC157 | 15 | **8** | −7 (addr MUX) |
| 74HC161 | 5 | **3** | −2 (PCL×2 + phase; PCH→574) |
| ALU block | 20 | **20** | 0 (Track A) |
| **74HC 합계 (Track A)** | ~71 | **~48** | **−23** |

*Flash×2, SRAM×1, 클록, 245×1–2, 138, 595, 14×2 유지.*

---

## 4. 성능 재추정 (ACC machine)

| 프로파일 | CPI (avg) | MIPS @ 2 MHz |
|----------|-----------|--------------|
| ACC 연속 (INC/ADD imm) | ~2.0 macro | **~1.0** |
| LOAD/STORE every op | ~3–4 macro | **~0.5–0.7** |
| CALL/RET (SW stack) | ~5–8 macro | **~0.25–0.4** |
| **OS mix (현실)** | ~4–6 | **~0.3–0.5** |

v1.0 **1.33 MIPS stretch**는 GPR·Shadow ACC 전제 — v1.1은 **0.5 MIPS** 를 **실용 목표**, **1.0 MIPS** 를 ACC-only loop stretch로 재설정.

**0.1 MIPS 미만**은 SW stack·far call 남용 시 — **µcode CALL depth** 제한·zp stack convention으로 완화.

---

## 5. 검토 (리스크)

| 리스크 | 완화 |
|--------|------|
| ACC-only CPI 팽창 | Collapsing 유지; compiler/asm **ACC 스cheduling** |
| MBR 시분할 fetch 2 byte | 16-bit ISA latency +1 macro — 명세에 명시 |
| SW stack 느림 | Zero page `$0100–$01FF`; depth limit in monitor |
| PCH 갱신 지연 | far JMP rare; page-local code default |
| LUT ALU 학술성 | Track A default; B는 BOM 실험 |
| 비트 시리얼 | **채택 안 함** |

---

## 6. v1.0 대비 구현 변경

| v1.0 산출 | v1.1 |
|-----------|------|
| `regfile.yaml` | **삭제** → `acc.yaml` (574×1) |
| `ir_latch.yaml` (16b) | **`mbr.yaml`** (574×1, phase) |
| `addr_mux.yaml` (157×4) | **`addr_lo_mux.yaml`** (157×2) + `pch.yaml` |
| `{R1,R0}` effective addr | **MBR + PCH + zp indirect** micro-ops |
| `shadow_acc_rmw` test | **`acc_rmw`** — B3c 재사용 |

---

## 7. 아키텍처 스펙트럼 — ACC vs ACC+TMP vs GPR

| 위상 | 데이터 패스 | BOM Δ (CPU) | MIPS @ 2 MHz | 병목 |
|------|-------------|-------------|--------------|------|
| **v1.1 순수 ACC** | ACC 574×1, B←SRAM only | **0** (baseline ~48) | **0.3–0.5** | 중간값마다 STORE/LOAD |
| **v1.2 ACC+TMP** | ACC+TMP 574×2, **157×4** B←MEM\|TMP, A←ACC direct | **+5** (~**53**) | **0.6–0.8** | 157 B-bus ringing (국소) |
| **v1.0 4-GPR** | 574×4, **153×8** A/B tree | **+12** vs v1.2 (~71) | **~1.0** max | 64+ wire, crosstalk |

### 7.1 ACC+TMP 제어 (v1.2)

1. **ALU A ← ACC.Q** hardwired — A-side MUX **없음** → critical path 단축.
2. **ALU B ← 157×4** — `0`=SRAM read data, `1`=TMP.Q (153×4 대비 **제어·배선 절반**).
3. **ISA:** `TAX`/`TXA`/`ADD TMP` — **Execute 1 phase**, fetch 생략 → loop CPI ↓.

상세: [microcode-spec-v1.2.md](microcode-spec-v1.2.md).

### 7.2 hwsim gate (BOM 확정 전)

| 단계 | 산출 |
|------|------|
| M4a | `acc_tmp.yaml` + `acc_tmp_timing` slack ≥ 0 @ 2 MHz |
| PASS | **v1.2** BOM·라우팅 확정 |
| FAIL | **v1.1** pure ACC 유지 |

### 7.3 검토 요약

| | 판정 |
|--|------|
| 공학적 절충 | ✅ GPR 대비 **배선·IC 절반**, pure ACC 대비 **MEM traffic ↓** |
| 0.6–0.8 MIPS | ✅ 2-var loop·swap 시 **타당**; OS mix는 **0.5–0.7** |
| 157 ringing | ⚠ decap·짧은 배선 — **153×8보다 훨씬 낮은 리스크** |
| 2× TMP | 📋 v1.3 optional — BOM +6, diminishing returns |

**권장:** 구현 **default = v1.3 CPLD**; hwsim FAIL 시 v1.2 → v1.1 fallback.

---

## 8. v1.3 CPLD hybrid (권장)

| | v1.2 ACC+TMP | **v1.3 CPLD** |
|--|--------------|---------------|
| GPR | ACC+TMP 574×2 | **R0–R3 @ ATF1504AS** |
| ALU B | 157×4 MEM\|TMP | **`q_b` 직결** |
| 74HC Δ | +5 vs v1.1 | **−574×4, −157/153×4~8** vs discrete GPR |
| BOM | ~53 IC | **~48 74HC + CPLD + adapter** |
| hwsim | `acc_tmp.yaml` (예정) | **`cpld_regfile` PASS** |

상세: [cpld-hybrid-v1.3.md](cpld-hybrid-v1.3.md).

### 8.1 물리 검토

| 리스크 | 완화 |
|--------|------|
| Port A/B 16b SSO | PLCC adapter **0.1 µF×4** 최단 VCC/GND |
| JTAG 안테나 효과 | 짧은 ISP 헤더, GND 근접 *(프로그래머 BOM 외)* |
| async read 10 ns | 250 ns macro-cycle 내 ALU setup — M7 측정 |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-31 | §8 v1.3 CPLD hybrid — default 권장 |
| 2026-05-31 | §7 ACC+TMP spectrum, v1.2 fallback |
| 2026-05-31 | v1.1 — ACC, MBR, zp stack, polling, BOM −23 IC; bit-serial 배제 |
