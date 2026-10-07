# NVIDIA PCI PM Suspend 실패 — cmg-v16 (2026-10-07)

**Agent:** Hermes (분석), 원 스크린샷: 사령관 제공
**상태 / Status:** 📝 원인 후보 정리 완료, **원격 명령 실행으로 범위 좁히기 대기** (이 세션은 cmg-v16에 직접 접근 불가)
**관련 / Related:** `agents/hermes/MEMORY.md` 안건 #50(hb5u·cmg-cv16 오케스트레이션), thesis `2026-09-08-economi-cmg-v16-input-paralysis-blind-remote-diagnosis` (cmg-v16 = Sunshine 호스트, 화면 없이 SSH만으로 원격 진단한 선례)

---

## 1. 증상 / Symptoms

사령관이 cmg-v16 콘솔 화면을 촬영해 전달한 커널 로그:

```
[763806.914639] nvidia 0000:01:00.0: PM: pci_pm_suspend(): nv_pmops_suspend [nvidia] returns -5
[763806.914836] nvidia 0000:01:00.0: PM: dpm_run_callback(): pci_pm_suspend returns -5
[763806.914841] nvidia 0000:01:00.0: PM: failed to suspend async: error -5
[763807.099572] PM: Some devices failed to suspend, or early wake event detected
[763808.608521] nvidia 0000:01:00.0: PM: pci_pm_suspend(): nv_pmops_suspend [nvidia] returns -5
[763808.608630] nvidia 0000:01:00.0: PM: dpm_run_callback(): pci_pm_suspend returns -5
[763808.608633] nvidia 0000:01:00.0: PM: failed to suspend async: error -5
[763808.669936] PM: Some devices failed to suspend, or early wake event detected
```

- `-5` = `EIO`. NVIDIA 커널 모듈(`nvidia.ko`)의 서스펜드 콜백(`nv_pmops_suspend`)이 I/O 에러로 실패 → 커널 PM이 S3 절전 진입 자체를 중단.
- 1.7초 간격으로 **동일 실패 2회 반복** — 일시적 글리치가 아니라 지속 상태 문제로 판단.

## 2. 원인 후보 (발생 빈도순)

| # | 후보 | 확인 명령 |
|---|---|---|
| 1 | NVIDIA 서스펜드 전용 systemd 유닛 비활성 (`nvidia-suspend`/`nvidia-hibernate`/`nvidia-resume`) | `systemctl status nvidia-suspend.service nvidia-hibernate.service nvidia-resume.service` |
| 2 | 커널 모듈 파라미터 `NVreg_PreserveVideoMemoryAllocations=1` 누락 | `cat /proc/driver/nvidia/suspend`, `grep -r PreserveVideoMemoryAllocations /etc/modprobe.d/` |
| 3 | 커널-모듈 ABI 불일치 (업데이트 후 미재부팅) | `uname -r` vs `modinfo nvidia \| grep vermagic`, `dkms status` |
| 4 | **서스펜드 시점에 GPU를 물고 있는 프로세스 존재** | `nvidia-smi`, `fuser -v /dev/nvidia*` |

## 3. cmg-v16 고유 맥락 — 후보 4가 특히 유력

MEMORY.md(안건 #50 인용)와 thesis `2026-09-08-economi-cmg-v16-input-paralysis-blind-remote-diagnosis`에 따르면 **cmg-v16은 "Sunshine" 호스트**다. Sunshine은 NVENC(NVIDIA 하드웨어 인코더) 기반 원격 스트리밍 서비스로, 세션이 붙어있지 않아도 GPU 캡처/인코딩 컨텍스트를 상시 열어두는 경우가 흔하다. 이게 서스펜드 콜백과 충돌해 EIO를 유발하는 전형적 패턴과 정확히 일치한다 — 즉 단순 드라이버 설정 문제가 아니라 **"이 머신이 상시 GPU 스트리밍 서비스로 쓰인다"는 용도 자체가 서스펜드와 구조적으로 상충할 가능성**이 높다.

```bash
systemctl status sunshine        # 또는 등록된 서비스명
nvidia-smi                       # Sunshine 프로세스가 GPU 점유 중인지 확인
```

## 4. 이 레포 맥락에서의 의미

CLAUDE.md 기준 cmg-cv16은 hb5u와 함께 간헐가동 물리 GPU 노드로 분류된다(안건 #50 오케스트레이션 설계의 전제). 서스펜드가 반복 실패하면:
- 노트북/머신이 의도와 달리 깨어있는 상태로 남아 전력 소모
- 강제 절전 시 GPU가 비정상 전원상태로 빠져, 재부팅 전까지 cmg-v16 의존 작업(용접 아크 3D 표출, Sunshine 스트리밍 등) 불가
- 안건 #73에서 "cmg-cv16이 꺼져있다"고 전제했던 synapse_failover_daemon.py 소재 확인 작업에도 영향 — 꺼진 게 아니라 **서스펜드 실패로 불안정 상태**였을 가능성도 배제 못함

## 5. 추가 증언 — 전원 분리, 배터리는 충분했음 (사령관 확인)

사령관이 "전원이 빠졌었는데 밧데리는 충분했어"라고 확인 — **배터리 고갈로 인한 정상 셧다운이 아니라, AC 전원 분리와 맞물린 비정상 전원차단**이다. §1의 서스펜드 반복 실패와 연결하면 가설이 다음과 같이 좁혀진다:

- **(a) 커널 행/패닉 → 하드 크래시**: 서스펜드 재시도가 계속되며 시스템이 멎었고, 그 결과가 "전원이 빠진 것"처럼 관측됐을 가능성. 이 경우 AC 분리는 증상이지 원인이 아님.
- **(b) 배터리 BMS 보호회로 컷오프**: 서스펜드 실패로 GPU가 절전 없이 계속 전력을 소모하던 중 AC가 물리적으로 빠지는 순간, 배터리가 그 순간 전력 피크를 못 받쳐 보호회로가 작동했을 가능성. 충전량(SOC)은 충분해도 순간 전류 공급능력은 별개 문제라 "배터리는 충분했는데 꺼짐" 증상과 부합.

두 가설 모두 **§1의 서스펜드 반복 실패가 선행 원인일 가능성**을 가리킨다 — 단순 배터리 이슈가 아니라 GPU PM 실패가 전원 안정성까지 끌고 내려간 사례로 보는 게 더 설명력이 높다.

**확인 명령 추가**:
```bash
journalctl -k -b -1 --since "<전원차단 추정시각 -5분>"   # 크래시 직전 커널 로그(이전 부팅)
journalctl -b -1 -p err                                 # 직전 부팅의 에러 레벨 로그
upower -i /org/freedesktop/UPower/devices/battery_BAT0   # 배터리 상태·보호회로 이력(지원 시)
dmesg | grep -i -E "thermal|critical|shutdown"           # 열적 셧다운 여부
```

## 6. 다음 단계 (미착수)

이 세션은 cmg-v16에 직접 접근 권한이 없어 위 명령을 실행할 수 없음. §2·§3·§5의 확인 명령 실행은 cmg-v16 접근 권한이 있는 에이전트(Gravity·Codezy 등, MEMORY.md §3 참조)에게 요청 필요.

---

*Hermes 분석, 2026-10-07. 스크린샷 직접 촬영·현장 접근 없이 로그 텍스트만으로 작성 — 원격 재현 검증 전까지 원인은 후보 단계임을 명시.*
