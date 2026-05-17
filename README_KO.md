# 듀얼 암 MuJoCo 디지털 트윈

바이매뉴얼 OpenArm + OMX-F 팔로워 암 + Vic Pinky 모바일 베이스를 MuJoCo로 모델링하고, Rerun 뷰어와 FastAPI 상태 대시보드로 구동합니다. 선택적으로 RViz 인터랙티브 마커를 통한 ROS 2 Jazzy 연동도 지원합니다.

## 디렉토리 구조

```
scratch/build_mjcf.py     # 단일 소스 — urdf/dual_openarm.xml 빌드
urdf/dual_openarm.xml     # 컴파일된 MJCF (build_mjcf.py로 재생성)
urdf/dual_openarm.urdf    # OpenArm URDF (STL 메시 + 댐핑 포함)
urdf/omx_f.urdf           # 참조용; 메시는 시스템 경로에서 가져옴
urdf/vicpinky.urdf        # 참조용; 섀시는 build_mjcf.py에서 정의
meshes/                   # OpenArm STL/OBJ 에셋
scripts/                  # 런처 및 헬퍼 스크립트
dashboard/                # FastAPI 상태 보드 (포트 8000)
backups/                  # 검증된 모델 상태 스냅샷
```

`build_mjcf.py`는 URDF에서 OpenArm을 로드한 후, OMX-F 운동학 체인
(`/opt/ros/jazzy/share/open_manipulator_description/meshes/omx_f/`의 STL 메시 사용),
Vic Pinky 섀시(상단 플레이트, 알루미늄 기둥, 캐스터, LiDAR 마운트, 바퀴),
환경(스카이박스, 체커 바닥, 태양광)을 프로그래밍 방식으로 포함합니다.
재생성해도 체크인된 XML과 시각적으로 동일합니다.

## 빠른 시작

Python 가상환경 (시스템 Python 3.12):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

OMX-F 메시는 ROS 패키지가 필요합니다:

```bash
sudo apt install ros-jazzy-open-manipulator-description
```

### 실행

```bash
bash scripts/start_all.sh
```

다음을 실행합니다:

- MuJoCo 네이티브 뷰어 + Rerun 스트림 → <http://localhost:9090>
- FastAPI 대시보드 → <http://localhost:8000>

`start_full_sim.sh`는 추가로 `robot_state_publisher`, RViz 2,
인터랙티브 마커 IK 타겟 서버를 실행합니다.
PATH에 ROS 2 Jazzy가 있고 venv에 `pyyaml`이 설치되어 있어야 합니다.

**참고**: ROS 2 IK 경로는 현재 `target_left` / `target_right` mocap 바디가
생성된 모델에 없어서 충돌이 발생합니다 — 사용 전에 `build_mjcf.py`에 추가하세요.

### 모델 재생성

```bash
python scratch/build_mjcf.py
```

`build_mjcf.py` 안에서 OMX-F 관절 원점, vicpinky 지오메트리, 조명, 댐핑을 조정하세요.
이 파일이 단일 소스입니다.

## 참고 사항

- 참조 스냅샷은 `backups/2026-05-13_vicpinky_orbit/`입니다.
  `urdf/dual_openarm.xml`이 예상치 못하게 변경되면 해당 스냅샷과 비교하세요.
- `lerobot/`은 추적되지 않습니다; 필요하면 pip으로 업스트림을 설치하세요.
- 렌더 캡처는 `captures/`에 저장됩니다 (gitignore 처리됨).
