# PQC-QKD Suite

PQC(ML-KEM 스타일의 교육용 C 라이브러리) + 임베디드 최적화 데모 + QKD 네트워크 시뮬레이터 + 통합 CLI/GUI를 포함하는 올인원 프로젝트입니다.

## 구성

- pqc_core: C99 기반의 교육용 KEM 구성 요소(N=256, q=3329), SHA-256 KDF, 시스템 RNG, CBD(eta=2)
- pqc_embedded: MCU 최적화 패턴(레이어 병합 NTT, 작은 해시, 스트리밍 M×V)과 호스트 데모
- qkdn_sim: Python 기반 QKD 네트워크 모델/라우팅/플로팅(베이스라인/크로스/강화학습)
- cli: 통합 CLI(빌드/실행/노트/QKD 시나리오). PyInstaller로 단일 바이너리 제공
- app_gui: Tkinter GUI. 로컬 로그인(등록/로그인) 후 PQC/QKD 작업 수행
- scripts: 빌드 스크립트(PyInstaller), 앱 번들 생성
- .github/workflows/ci.yml: Ubuntu에서 C 빌드/테스트 + QKD 스모크, macOS에서 PyInstaller 빌드

## 빠른 시작(인터랙티브 CLI)

```
./dist/pqc_qkd_cli
```

메뉴

- 1) PQC build: C 라이브러리 빌드(CMake 존재 시 CMake, 없으면 make -C)
- 2) PQC run example: 예제 실행(`make core-make-example`)
- 3) Show embedded optimization notes: 임베디드 최적화 노트 출력
- 4) Run QKD simulation: 정책/스텝/소스/도착/플롯 파일 지정으로 실행
- 5) Secure password input: 비밀번호 안전 입력(PBKDF2 데모)

직접 실행 예시

```
./dist/pqc_qkd_cli pqc build
./dist/pqc_qkd_cli pqc run
./dist/pqc_qkd_cli qkd run --policy rl --steps 80 --src 2 --dst 5 --plot qkd_path.png
./dist/pqc_qkd_cli auth --rounds 300000 --no-confirm
```

## GUI 앱(macOS)

이제 macOS용 GUI 앱도 제공합니다. 더블클릭으로 실행하면 로그인 화면 → 메인 화면 순으로 진입합니다.

- 위치: `dist/PQC-QKD Suite GUI.app`
- 처음 실행 시 보안 경고가 뜨면 Finder에서 Control-클릭 → “열기”로 1회 예외 승인

기능

- 로그인/등록: Username + Password. 비밀번호는 로컬 파일(`data/users.json`)에 PBKDF2-SHA256(솔트/라운드/해시)로만 저장되며 원문은 저장하지 않습니다. `data/users.json`은 .gitignore 처리됩니다.
- PQC Core: Build/Run example 버튼 제공
- Embedded Notes: 문서 로드하여 보기
- QKD Simulation: Src/Dst/Steps/Policy 지정 → Run & Save Plot → PNG 저장

빌드

```
bash scripts/build_app.sh
```

생성물

- CLI: `dist/pqc_qkd_cli`
- GUI: `dist/PQC-QKD Suite GUI.app`

## 개발/빌드 팁

- 루트 `Makefile` 제공:
	- `make core` / `make core-example`
	- `make core-make` / `make core-make-example` (CMake 없이도 동작)
- Matplotlib 백엔드는 GUI/패키징 호환을 위해 Agg로 설정됩니다(플롯 저장 중심).

## 보안 노트

- 본 저장소의 로그인/비밀번호 기능은 데모 용도입니다. 운영 환경에서는 Keychain/암호화 저장소, 계정 잠금, MFA 등을 고려하세요.
- 비밀번호 원문 저장 금지. 소금/라운드/해시만 저장합니다.

## 라이선스

교육/연구 목적의 예제 코드입니다. 실제 서비스 적용 전 충분한 검증과 보안 검토가 필요합니다.