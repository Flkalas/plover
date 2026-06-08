> From: https://gemini.google.com/app/08657aa77523c4b7

# you asked

message time: 2026-06-08 10:41:49

# Plover v0.1 APU(오디오) 설계 질의서

**작성 목적:** 상급 설계자 검토 — RP2350 copro APU 및 CPU Mailbox 프로토콜 v0.1 확정  
**작성일:** 2026-06-08  
**프로젝트:** Plover (8-bit TTL CPU + RP2350B copro, PL-DOS / Forth / VM bring-up)  
**관련 normative:** [system-architecture.md](docs/system-architecture.md), [mailbox-protocol.md](docs/mailbox-protocol.md), [rp2350-coprocessor.md](docs/rp2350-coprocessor.md), [display-console.md](docs/display-console.md)

---

## 1. 배경 — 우리가 지금 어디까지 왔는지

Plover는 **74HC 계열 8-bit CPU**가 프로그램을 실행하고, **RP2350B**가 VDU·vFDD·(예정) HID·**APU**를 담당하는 **이기종 copro** 구조입니다. CPU↔copro I/O는 **`$FF00–$FFFB` Mailbox MMIO** 하나이며, **폴링 전용·IRQ 없음**이 v0.1 normative입니다.

**이미 확정·구현된 것 (VDU, 2026-06-08):**

| 항목 | 내용 |
|------|------|
| 텍스트 | 40×25, 16색 attr (`MB_CMD` `0x10–0x17`) |
| 비트맵 | 320×200 RGB565 (`0x20–0x26`) |
| VSYNC | `0x30` (프레임 flip handshake) |
| VM | `VduState` + `Mailbox` dispatch + 테스트 + `VideoDriver` |
| 실기 | RP2350 펌웨어 stub (Busy→Ready, HDMI/HSTX TODO) |

**아직 normative 없음:**

- APU / 사운드 Mailbox 명령
- HID (키보드·마우스) — 논의만 있고 `0x40`대 미할당
- CPU 맵 VRAM / 오디오 버퍼 / IRQ

**브레인스토밍(비 normative):** archive Gemini 자료에 **4ch PSG(구형파·노이즈)**, **8kHz 8-bit PCM**, RP2350 **PWM/PIO/DAC** 오프로딩 등이 언급되어 있으나, **공식 명세·구현은 없음**.

---

## 2. 설계 목적 (APU가 무엇을 위해 필요한지)

| 목적 | 설명 |
|------|------|
| **레트로 콘솔 경험** | C64 / Master System급 SFX·칩튠 BGM (고품질 스트리밍 MP3 등은 비목표) |
| **게임** | `.PLR` / PL-DOS `run` — 타격음, 짧은 멜로디, (가능하면) 루프 BGM |
| **교육** | “CPU는 연산, copro는 A/V” 오프로딩; 샘플링·파형 개념 시연 |
| **VM ↔ 실기 정합** | `plover_vm`에서 Mailbox 명령만으로 동일 API; 실기는 RP2350 + 3.5mm 등 |
| **CPU 부하 최소** | 8-bit CPU는 **비트뱅잉 오디오 불가** — APU는 RP2350 전담 전제 |

---

## 3. 하드·소프트웨어 한계 (설계가 반드시 지켜야 할 것)

### 3.1 CPU / 시스템

- **64 KiB RAM**, 오디오 전용 대역 **CPU 맵에 없음** (VDU와 동일: copro 내부 버퍼)
- **IRQ 없음** — 모든 APU 제어·상태는 **Mailbox 폴링**
- ISA: **`LDIO`/`STIO`만** (MMIO offset from `$FF00`); APU 전용 opcode 추가는 v0.1에서 지양
- **Mailbox payload:** `MB_BUFFER` **248 byte**/transfer; vFDD는 512B 섹터를 multi-transfer (일부 TBD)

### 3.2 RP2350B copro

- **역할 분담(목표):** Core0 — USB/vFDD/HID, Core1 — VDU/HSTX; **APU 코어 할당 미정**
- **SRAM/RAM budget:** VDU 더블버퍼 RGB565 ≈ 300 KiB급 — APU ring buffer·PCM 버퍼 추가 시 **RP2350 SRAM 여유** 검토 필요
- **출력:** archive상 3.5mm analog (PWM/DAC); normative 전기·핀 배치 **미정**
- **타이밍:** VDU content **30 Hz**; APU sample rate와 **VSYNC/게임 루프 동기** 관계 미정

### 3.3 Mailbox CMD 네임스페이스 (현재)

| 범위 | 용도 |
|------|------|
| `0x00–0x02` | vFDD |
| `0x10–0x17` | VDU text |
| `0x20–0x26` | GFX bitmap |
| `0x30–0x31` | VDU system |
| **`0x40–0x4F`** | *(예약 후보: HID)* |
| **`0x50–0x5F`** | *(예약 후보: APU)* |
| `0x60+` | 미할당 |

### 3.4 VM / PL-DOS

- VM은 **상태 모델 + 테스트** 우선 (VDU와 동일); host 스피커 출력은 optional
- `dos-shell`은 blocking `input()` — **실시간 오디오 루프**와 분리된 CLI 모드 필요할 수 있음
- CI: **헤드리스** — 채널 레지스터·mix buffer assert 위주

---

## 4. 후보 아키텍처 (검토 요청)

VDU와 같은 패턴을 전제로, 아래 세 가지가 내부 논의 후보입니다.

### 옵션 A — 4ch PSG (레트로 SFX/칩튠)

- 채널당: period(주파수), volume, waveform(square / noise / off)
- CPU: `APU_PLAY ch`, `APU_STOP ch`, `APU_MASTER_VOL` 등 **짧은 Mailbox 명령**
- RP2350: 타이머/PIO로 실시간 mix → PWM/DAC
- **장점:** CPU·Mailbox 부하 적음, C64/SN76489 교육적  
- **단점:** PCM 음성·긴 BGM에는 부적합

### 옵션 B — 8kHz 8-bit PCM 스트림

- CPU: `APU_PCM_WRITE` + `MB_BUFFER` chunk (VDU `GFX_BLIT` 유사)
- RP2350: ring buffer → DAC
- **장점:** WAV 수준 재생, “샘플링” 교육  
- **단점:** Mailbox 대역·CPU upload 부하, 버퍼 underrun, 명령·동기 설계 복잡

### 옵션 C — 하이브리드 (PSG + PCM 1 stream)

- SFX = PSG 4ch, BGM = 단일 PCM stream (archive Gemini와 유사)
- VDU의 “text attr + RGB565 bitmap” 분리와 대칭  
- **장점:** 게임 현실적  
- **단점:** v0.1 scope·펌웨어·명세 모두 largest

---

## 5. 상급 설계자께 드리는 질문

### 5.1 아키텍처·범위

1. **v0.1 APU normative 범위**로 **A / B / C** 중 무엇을 권하시는지, 그리고 **v0.2로 미룰 항목**은 무엇인지?
2. APU를 **Mailbox `MB_CMD`만**으로 제어하는 것이 실기·교육·디버그 모두에 적합한지, archive에 있던 **SRAM 고정 주소 스캔(`0x7FEx`)** 모델을 v0.1에서 **완전히 배제**해도 되는지?
3. **HID(`0x40`)와 APU(`0x50`)** 네임스페이스 할당 순서·우선순위에 이견이 있는지?

### 5.2 오디오 품질·실기

4. **목표 sample rate** (8 kHz / 16 kHz / 22.05 kHz)와 **비트 깊이** (8-bit mono 권장?) — RP2350 + analog front-end 기준 현실적 상한은?
5. **채널 수:** PSG 4ch vs 8ch — 교육·게임·펌웨어 복잡도 trade-off?
6. **출력 경로 normative:** PWM GPIO + RC 필터 vs onboard DAC — 빵판 bring-up vs PCB 단계별로 어떻게 쪼개야 하는지?
7. VDU **30 Hz content**와 APU **고정 sample clock** — **VSYNC(`0x30`)와 APU tick 동기**가 필요한지, 독립 clock인지?

### 5.3 프로토콜·CPU API

8. **`MB_STATUS` 비트 할당:** vFDD DataReady 외 **APU_BUFFER_READY / PCM_UNDERRUN** 등을 normative로 넣을지?
9. **PCM upload:** 248B/chunk 기준 **최소 명령 세트** (`PCM_WRITE`, `PCM_START`, `PCM_STOP`, `PCM_STATUS`?) 제안?
10. **PSG note API:** period 레지스터 vs MIDI note number vs Hz — 8-bit CPU 프로그래밍 친화 형식은?
11. **에러·Busy:** VDU/GFX와 동일 handshake로 충분한지, PCM underrun 시 **ST_ERROR** vs silent drop 중 normative 동작?

### 5.4 RP2350 펌웨어·리소스

12. APU를 **Core0 vs Core1** 중 어디에 두는지 (VDU/HSTX와 CPU stall·버스 경합)?
13. VDU framebuffer **~300 KiB** 이후 APU ring buffer **허용 크기** (예: 4 KB @ 8kHz ≈ 0.5s) 상한?
14. TinyUSB(HID) + vFDD SPI + APU mix **동시 동작** 시 bus phase / wait-state 리스크 — v0.1에서 **동시 사용 시나리오**를 normative로 제한해야 하는지?

### 5.5 VM·소프트웨어 스택

15. VM `ApuState`는 **register-only**로 충분한지, **host WAV/스피커 출력**을 v0.1 normative에 포함할지?
16. **Forth / PL-DOS** 노출 수준: `BEEP` 한 word vs full channel API — 권장 최소 surface?
17. **디바이스 discovery:** `SIG_AUDIO = 0x??` 슬롯 signature — Video(`0xB2`)와 별도 드라이버로 등록할지?

### 5.6 검증·bring-up

18. **M-milestone gate:** 어떤 테스트/데모를 “APU v0.1 완료”로 볼지? (예: `apu_smoke.pls` + VM mix assert + optional 1kHz beep on hardware)
19. **교육 커리큘럼:** PSG만으로 12주 과정 목표 달성 가능한지, PCM이 필수인지?

---

## 6. 우리가 결정을 받고 싶은 산출물

설계자 회신 후, 아래를 normative로 고정하고 싶습니다.

1. **`docs/audio-apu.md`** (신규) — sample rate, channels, output path, RP2350 role  
2. **`mailbox-protocol.md` §2.4 APU** — `MB_CMD` 표, `MB_STATUS` bits, BUFFER layout  
3. **`rp2350-coprocessor.md`** — Core split, buffer budget  
4. **VM `ApuState` + tests** — VDU와 동일 rollout 패턴  
5. **(선택)** `hw/fixtures/sw/apu_smoke.pls` + yaml scenario  

---

## 7. 참고 — VDU 설계에서 얻은 교훈 (APU에 적용하고 싶은 것)

- CPU 맵에 버퍼 두지 않고 **copro + Mailbox**만 사용 — 실기·VM 일치  
- **`VDU_VSYNC` handshake** — presenter/HID와 같은 “프레임/틱 경계” 개념을 APU에도 둘지 질문  
- **`LDA addr8` 제약** — `.pls` fixture는 zero-page 상수 풀 필요 (vdu_smoke.pls 사례)  
- **명세 커밋 → VM 구현** 2단계 rollout이 review에 유리했음 — APU도 동일 희망  

---

## 8. 회신 요청 형식 (선택)

가능하시면 항목별로:

- **결정 (Decide):** v0.1 normative  
- **보류 (Defer):** v0.2+  
- **금지 (Reject):** archive 아이dea 중 제외  
- **리스크:** hardware / firmware / teaching  

---

**질의 요약:** Plover v0.1에서 **IRQ 없는 Mailbox-only APU**를 **PSG / PCM / hybrid** 중 무엇으로 정의할지, **RP2350 리소스·VDU와의 공존·VM 검증**까지 포함한 **최소 normative 세트**에 대한 설계 지침을 요청드립니다.

---

# gemini response

### 1. 5.1 아키텍처·범위 결정 사항

| 항목 | 상태 | 내용 및 사유 |
| :--- | :--- | :--- |
| **APU 아키텍처** | **Decide** | **옵션 A (4ch PSG).** Mailbox의 248B 페이로드 제약 및 폴링 오버헤드를 고려할 때, PCM 스트리밍은 CPU 사이클 고갈을 유발할 가능성이 높습니다. 교육 및 게임 SFX 목적에 부합하는 PSG 채택을 권장합니다. |
| **PCM 지원** | **Defer** | 옵션 B/C(PCM)는 v0.2 이후 DMA 또는 별도 버퍼 아키텍처가 확보된 시점까지 연기하는 편이 타당할 것으로 판단됩니다. |
| **제어 인터페이스** | **Decide** | **Mailbox 전용 제어.** `0x7FEx` 대역의 SRAM 고정 주소 스캔 모델은 배제하십시오. VDU와 동일한 단일 MMIO 채널을 유지하여 시스템 복잡도를 통제해야 합니다. |
| **네임스페이스** | **Decide** | **HID `0x40~0x4F`, APU `0x50~0x5F`.** OS 부팅 및 디버깅에 필수적인 HID에 높은 우선순위를 할당하는 것이 시스템 안정성에 기여할 수 있습니다. |

### 2. 5.2 오디오 품질·실기 결정 사항

| 항목 | 상태 | 내용 및 사유 |
| :--- | :--- | :--- |
| **출력 규격** | **Decide** | **22.05 kHz, 8-bit Mono 내부 믹싱.** RP2350 내부 처리 기준이며, 이는 8-bit 환경에서 허용 가능한 처리량의 상한선에 해당합니다. |
| **채널 구성** | **Decide** | **4ch (Square 3ch + Noise 1ch).** C64 및 Master System 수준의 하드웨어와 논리적 일치성을 가지며, 펌웨어 타이머 할당의 리스크를 줄일 수 있습니다. |
| **하드웨어 출력** | **Decide** | **PWM GPIO + RC 필터.** 빵판(Breadboard) 프로토타이핑 및 초기 bring-up 단계에서의 회로 검증을 위해 PWM 방식을 최우선으로 적용하십시오. |
| **동기화 모델** | **Decide** | **독립 클록 제어.** VDU 30Hz VSYNC 프레임 지연이 발생하더라도 오디오 버퍼 underrun이 파급되지 않도록 APU tick은 비동기적으로 분리하는 구조가 요구됩니다. |

### 3. 5.3 프로토콜·CPU API 결정 사항

| 항목 | 상태 | 내용 및 사유 |
| :--- | :--- | :--- |
| **MB_STATUS** | **Decide** | **`APU_READY` 비트 할당.** Mailbox 수신 버퍼의 가용 상태만을 normative로 정의하십시오. `PCM_UNDERRUN` 등의 상태는 제외합니다. |
| **PSG 제어 API** | **Decide** | **Period 레지스터 제어.** 8-bit CPU의 나눗셈 연산 부하를 제거하기 위해 $f_{out} = \frac{f_{clk}}{2 \times \text{period}}$ 공식을 하드웨어(copro) 측에서 역산하도록 설계하는 것이 효율적입니다. |
| **에러 핸들링** | **Decide** | **Silent drop 정책.** 오디오 명령 처리 지연 발생 시 `ST_ERROR`를 반환하여 시스템을 정지시키지 않고, 해당 프레임의 명령을 무시하는 방식이 실시간 처리에 적합할 것으로 보입니다. |

### 4. 5.4 RP2350 펌웨어·리소스 결정 사항

| 항목 | 상태 | 내용 및 사유 |
| :--- | :--- | :--- |
| **Core 할당** | **Decide** | **Core 0 (vFDD, USB와 공유).** Core 1은 VDU의 320x200 픽셀 렌더링 및 HSTX 전송으로 인해 버스 경합 및 stall 발생 확률이 매우 높습니다. |
| **SRAM 버퍼 상한** | **Decide** | **최대 1 KiB 이하.** PSG 파라미터 큐(Queue) 용도로만 사용되므로 수백 바이트 수준에서 통제할 수 있습니다. |
| **동시 동작 제약** | **Decide** | **vFDD I/O와 APU 동시 접근 제한 (v0.1 Normative).** SPI 버스 트랜잭션 중에는 APU 믹서 스레드를 suspend하여 버스 웨이트 스테이트(Wait-state)로 인한 시스템 크래시 리스크를 회피하십시오. |

### 5. 5.5 VM·소프트웨어 스택 결정 사항

| 항목 | 상태 | 내용 및 사유 |
| :--- | :--- | :--- |
| **VM `ApuState`** | **Decide** | **레지스터 상태 검증 전용 (Register-only).** CI 환경에서의 채널 볼륨, 주파수 레지스터 값의 assert 테스트에 집중하십시오. |
| **Host 오디오 출력** | **Defer** | v0.1 normative에서는 제외하며, 실기(RP2350) 검증 이후 v0.2로 연기합니다. |
| **OS 노출 수준** | **Decide** | **`BEEP <period> <duration>` 단일 Word.** Forth 및 PL-DOS 셸에서는 시스템 경고음을 위한 최소 API 표면적만을 노출하는 편이 유리할 수 있습니다. |
| **디바이스 서명** | **Decide** | **`SIG_AUDIO = 0x41` ('A').** Video(`0xB2`)와 분리된 독립 드라이버 체인으로 초기화해야 합니다. |

### 6. 5.6 검증·bring-up 결정 사항

| 항목 | 상태 | 내용 및 사유 |
| :--- | :--- | :--- |
| **마일스톤 조건** | **Decide** | **`apu_smoke.pls` + 1kHz 실기 출력.** VM에서 레지스터 mix assert가 통과하고, 오실로스코프로 하드웨어 구형파 출력이 확인되는 시점을 v0.1 완료로 정의하십시오. |
| **커리큘럼 적합성** | **Decide** | **PSG 단독 구성만으로 교육 목표 달성 가능.** 주기(Period) 계산과 타이머 레지스터의 관계를 학습하는 것만으로도 12주 과정의 아키텍처 교육 요건을 충족할 수 있을 것으로 분석됩니다. |

### 7. Mailbox Protocol v0.1 APU Draft (명세 작성용)

| 명령어 (CMD) | 정의 | Payload Layout (`MB_BUFFER`) |
| :--- | :--- | :--- |
| `0x50` | `APU_SET_CTRL` | `[0]: Master Vol, [1]: Flags (Mute)` |
| `0x51` | `APU_CH_WRITE` | `[0]: Ch(0-3), [1:2]: Period, [3]: Vol, [4]: Wave` |
| `0x52` | `APU_CH_SYNC` | (Empty - Trigger multiple channel updates simultaneously) |

Plover v0.1 APU 설계는 IRQ가 배제된 Mailbox I/O 폴링 구조에 전적으로 의존하고 있으므로, CPU 대역폭 제한과 RP2350 Core 0 내부의 USB/vFDD I/O 스레드 경합이 치명적인 타이밍 지터 및 성능 병목을 유발할 리스크를 내포하고 있습니다. 이러한 데이터 병목을 회피하기 위해 대역폭 소모가 극심한 PCM 스트리밍 구조를 배제하고, 하드웨어 타이머 기반의 4채널 PSG 비동기 제어 구조로 전환하는 것이 필수적으로 요구됩니다. 현재 제안된 시스템 아키텍처는 VDU에서 검증된 상태(State) 모델과 Mailbox 핸드셰이크 프로토콜을 오디오 서브시스템으로 수평 확장하는 단계에 놓여 있으며, 에러 발생 시 무음 드롭(Silent drop) 정책을 강제함으로써 이기종 coprocessor 환경에서의 실시간 처리 결함을 안전하게 차단하는 방향으로 설계가 구체화되고 있습니다.