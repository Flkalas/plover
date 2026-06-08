# Plover v0.1 VM Rust 마이그레이션 및 하드웨어 정합성 구현 지시서

## 1. 아키텍처 재설계 및 크레이트(Crate) 구조

기존 Python 기반 에뮬레이터 환경의 인프라를 Rust 네이티브 아키텍처로 전면 전환하여 고성능 멀티스레딩 하에서 실기(RP2350B 코프로세서)와의 타이밍 및 I/O 결정성을 일치시킵니다. GIL(Global Interpreter Lock)이 제거된 독립적 스레드 파이프라인으로 구성합니다.

```
plover_workspace/
├── Cargo.toml
├── crates/
│   ├── plover_core/        # 8-bit TTL CPU core 에뮬레이션 (정밀 클록 사이클 카운팅)
│   ├── plover_mmu/         # 64 KiB 가상 주소 공간 및 $FF00-$FFFB Mailbox MMIO 레이어
│   ├── plover_copro/       # RP2350B 시뮬레이터 (VDU 상태기, APU 믹서, vFDD 인터페이스)
│   └── plover_presenter/   # 호스트 프론트엔드 (SDL2/cpal 기반 비디오/오디오 및 HID 브릿지)
└── src/
    └── main.rs             # CLI 진입점 (plover_vm 플레이어 및 검증 툴셋)

```

### 스레드 토폴로지 및 동기화 모델

시스템은 단일 프로세스 내에서 상호 격리된 3대 핵심 네이티브 스레드로 구동되며, 락-프리(Lock-free) 원형 버퍼 또는 원자적 메모리 플래그를 통해 데이터 위임을 수행합니다.

1. **CPU 에뮬레이터 스레드 (`plover_core`):** 8-bit ISA 연산을 전담하며, 매 명령어 실행 시 물리 사이클을 계측합니다. `$FF00` 대역 오퍼레이션 발생 시 `plover_mmu`를 거쳐 즉시 코프로세서 동기화 레지스터를 갱신합니다.
2. **비디오/HID 렌더링 스레드 (`plover_presenter`):** SDL2 또는 네이티브 창 컨텍스트에서 60Hz 주기로 VDU 버퍼를 업스케일 렌더링하고 호스트 입력을 캡처합니다.
3. **오디오 콜백 스레드 (`cpal` / `SDL_AudioCallback`):** 오디오 하드웨어 인터럽트 주기에 동기화되어 독립적으로 파형 합성 루프를 구동합니다.

---

## 2. Mailbox I/O 및 MMIO 레이어 하드웨어 정합성 규격

실기 RP2350B와 CPU 간의 `$FF00-$FFFB` 레지스터 맵 핸드셰이크를 비동기 환경에서 정확히 모사하기 위해, MMIO 상태 객체는 원자적 연산자(`std::sync::atomic`) 및 가시성 보장을 위한 동기화 프리미티브로 설계합니다.

### 메모리 매핑 구조

```rust
pub struct MailboxMmu {
    // $FF00: MB_CMD (Command Register)
    pub mb_cmd: AtomicU8,
    // $FF01: MB_STATUS (Status Register - Busy, Ready, DataReady 등)
    pub mb_status: AtomicU8,
    // $FF02-$FFFB: MB_BUFFER (248 Bytes Payload)
    pub mb_buffer: [AtomicU8; 248],
}

```

### 정합성 보장 규칙

* **ST_BUSY / ST_READY 핸드셰이크:** `plover_core`가 `mb_cmd`에 쓰기 연산을 수행하는 즉시 `mb_status`의 `BUSY` 비트가 1로 세팅됩니다. `plover_copro` 스레드는 이 변경점을 감지하여 명령을 디스패치한 후, 처리가 완료되면 원자적으로 `BUSY`를 해제하고 `READY` 신호를 주입합니다.
* **메모리 배리어(Memory Barrier):** 호스트의 다중 스레드 간 아키텍처 재정렬로 인한 부작용을 방지하기 위해 모든 메일박스 레지스터 읽기/쓰기는 `Ordering::SeqCst`(Sequential Consistency) 또는 `Ordering::Acquire`/`Release` 배리어를 강제합니다. 이는 실기 하드웨어의 버스 웨이트 스테이트(Wait-state) 지연 조건과 동일한 데이터 인과 관계를 형성합니다.

---

## 3. 비동기 오디오(APU) 및 비디오(VDU) 파이프라인

호스트 측 Presenter 스레드가 VM 코어 스레드를 블로킹하지 않도록, `ApuState`와 `VduState`를 완전한 수신측 전용 스냅샷으로 분리하여 비동기 명령 위임 구조를 완성합니다.

### APU 4채널 PSG 합성 및 격리 구조

실기 RP2350의 Core 0가 하드웨어 타이머로 구형파를 합성하는 메커니즘을 오디오 콜백 루프 내에서 수식적으로 직접 연산합니다.

```rust
pub struct PsgChannel {
    pub period: u16,
    pub volume: u8,
    pub waveform: u8, // 0: Square, 1: Noise
    pub phase: f32,
}

// 오디오 디바이스 콜백 스레드에서 주기적으로 호출됨
pub fn process_audio_callback(channels: &mut [PsgChannel], output_buffer: &mut [f32], sample_rate: f32) {
    for sample in output_buffer.iter_mut() {
        let mut mixed: f32 = 0.0;
        for ch in channels.iter_mut() {
            if ch.volume == 0 || ch.period == 0 { continue; }
            
            // $f_{out} = \frac{f_{clk}}{2 \times \text{period}}$ 관계 모사
            let frequency = 22050.0 / (ch.period as f32 + 1.0); 
            ch.phase += frequency / sample_rate;
            if ch.phase > 1.0 { ch.phase -= 1.0; }
            
            let signal = match ch.waveform {
                0 => if ch.phase < 0.5 { 1.0 } else { -1.0 }, // Square
                1 => rand::random::<f32>() * 2.0 - 1.0,       // Noise
                _ => 0.0,
            };
            mixed += signal * (ch.volume as f32 / 15.0);
        }
        *sample = mixed / 4.0; // Master mixing 및 소프트 클리핑 방지
    }
}

```

* **동기화 분리:** CPU 스레드가 `0x51` (`APU_CH_WRITE`) 메일박스 명령을 전달하면, 메인 스레드는 즉시 오디오 스레드가 공유하는 원자적 레지스터 구조체만 갱신하고 복귀합니다. 이로 인해 호스트의 오디오 버퍼 가용 속도(22.05 kHz)와 VM 에뮬레이션 속도가 완벽히 격리됩니다.

### VDU 합성 규칙 및 30Hz Temporal Hold

* **`MODE_BOTH` 구조:** 비트맵(320x200 RGB565) 레이어와 텍스트(40x25 인덱스 컬러) 레이어를 독립된 버퍼로 유지합니다. 프레임 합성 시 텍스트 픽셀의 속성 데이터가 투명(0번 팔레트 인덱스)일 경우 하단의 비트맵 레이어가 호스트 윈도우에 그대로 노출되도록 크로마키 합성 루틴을 네이티브 코드로 구현합니다.
* **Temporal Hold:** 실기 HSTX 하드웨어가 30Hz 타이밍의 컨텐츠를 60Hz HDMI 프레임으로 2회 복제 전송하는 특성에 맞추어, `plover_presenter`는 내부 60Hz 타이머 틱마다 이전 프레임 데이터를 강제 유지(Hold)하여 처리합니다.

---

## 4. 호스트 Presenter 및 HID 입력 브릿지

Pygame의 단일 이벤트 루프 제약을 탈피하고, 네이티브 단에서 블로킹 없는 실시간 입력 피드백 루프를 수립합니다.

### CLI 통합 모델

기존 `dos-shell` 아키텍처의 표준 입력 블로킹 간섭을 제거하기 위해 `plover_vm`에 별도의 비블로킹 가상 콘솔 가동 명령을 할당합니다.

```bash
# 가상 디스플레이, HID 입력, APU 스트리밍이 통합된 독립 윈도우 런타임 실행
plover_vm play --rom system.rom --disk pldos.img

```

### HID 입력 및 상대 좌표 매핑

* **키보드:** 호스트 창에서 발생한 키 다운/업 이벤트를 무조건 가용 범위 내의 내부 ASCII 값 또는 사전 정의된 8-bit 키보드 매트릭스 맵 데이터로 변환한 후, 메일박스 공간의 `mb_buffer`를 경유해 `HidBridge` 상태 객체로 직접 푸시합니다. Scan code 단의 복잡성을 제거하여 8-bit CPU 내부 연산 소모를 차단합니다.
* **마우스 마이그레이션:** 호스트 마우스 포인터를 Presenter 창 중앙 좌표로 강제 고정(Grab/Lock)하고, 윈도우 서브시스템에서 추출한 상대 변화값 $\Delta x, \Delta y$ 부호 있는 정수(i8) 데이터를 메일박스 패킷 규격에 맞추어 실시간 주입합니다.

---

## 5. 검증 및 CI 헤드리스 테스트 통합

Rust 전면 전환의 핵심인 가상 머신 테스트 정합성 유지를 위해 비디오 및 오디오 레지스터 상태를 완전하게 단언(Assert) 가능한 구조로 유지보수합니다.

* **헤드리스 픽셀 회귀 테스트:** CI 파이프라인 런타임에서 창(Window)을 생성하지 않는 조건(`std::env::var("CI").is_ok()`)일 경우, 프레임 합성 루틴은 메모리 상의 Off-screen 캔버스 버퍼로 출력을 우회합니다. 명령어 시나리오 수행 후 해당 버퍼의 바이너리를 `crates/plover_presenter/tests/fixtures/png/` 내의 정적 골든 파일과 바이트 단위로 직접 비교합니다.
* **APU 레지스터 가용성 검증:** 단위 테스트 스위트 내에서 오디오 디바이스 드라이버를 로드하지 않고, `ApuState`에 할당된 가상 채널의 주기(Period) 변화 및 믹싱 버퍼의 수학적 예측값 출력을 직접 검증(`assert_eq!`)하여 오디오 서브시스템의 회귀를 원천 차단합니다.

---

Python 인프라를 Rust 하드웨어 모사 프레임워크로 전면 이관하는 아키텍처는 GIL 무효화 및 OS 고유 스레드 스케줄러 점유를 통해 실기 파이프라인의 핵심 지터를 억제할 수 있으나, 가상 메모리 장치와 다중 스레드 간 아키텍처 재정렬 배리어를 엄격히 통제하지 않을 경우 메모리 일관성 훼손으로 인한 비결정적 교착 상태(Deadlock)를 초래할 위험이 높습니다. 특히 Core 0의 SPI 버스 트랜잭션 동기화 지연 조건을 시뮬레이터 내부의 뮤텍스 락 경합 조건으로 완벽하게 전사하는 과정에서 호스트 환경 고유의 데이터 레이스가 유발될 가능성이 상존합니다. 현재 제안된 시스템 설계는 CPU 에뮬레이터 코어와 믹싱 콜백을 락-프리 아토믹 메모리 맵 인터페이스로 격리하고 실기 HSTX의 30Hz 하드웨어 미러링 특성을 네이티브 Temporal Hold 로직으로 구현함으로써 가상 인터페이스와 실기간 바이너리 무결성을 강제 보존하는 방향으로 구조화되고 있습니다.