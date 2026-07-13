# 회원 관리 프로그램 — TRD (기술 요구사항 정의서)

| 항목 | 내용 |
|------|------|
| **문서명** | 회원 관리 프로그램 TRD |
| **문서 유형** | Technical Requirements Document |
| **버전** | v1.0 |
| **작성일** | 2026-07-10 |
| **대상 언어** | Python 3.10 이상 |
| **의존성** | 표준 라이브러리만 사용 (외부 패키지 없음) |
| **상태** | 최종(Final) |

---

## 0. 문서 개요

이 문서는 **회원 관리 프로그램**의 기술적 설계를 정의합니다.

- **PRD의 관점**: "무엇을 만들까?" (사용자 입장의 기능 요구)
- **TRD의 관점**: "어떻게 만들까?" (개발자 입장의 기술 설계)

TRD는 아키텍처, 데이터 구조, 함수 설계, 기술 스택, 예외 처리 전략을 포함합니다.

---

## 1. 목적 및 배경 (Goals & Background)

### 1-1. 프로젝트 목표

Python 언어를 사용하여 **회원 관리 프로그램(콘솔 기반)**을 구현하고, 다음을 학습한다:

1. **CRUD 패턴**: 데이터 생성(Create), 읽기(Read), 수정(Update), 삭제(Delete)의 기본 동작
2. **데이터 구조**: 딕셔너리를 이용한 복잡한 데이터 모델링
3. **영속화(Persistence)**: 메모리 데이터를 파일에 저장·복원하는 방식
4. **유효성 검사 & 예외 처리**: 잘못된 입력으로부터 프로그램 보호

### 1-2. 실무 연계

이 프로젝트는 모든 백엔드 시스템의 원형(原型)을 다룬다:

| 과제 | 실무 시스템 |
|------|----------|
| 회원 딕셔너리 | 사용자(User) 테이블 |
| 바이너리 파일 | 관계형 데이터베이스(RDB) |
| 콘솔 메뉴 입력 | REST API 엔드포인트 |
| 유효성 검사 함수 | 서버/프론트엔드 입력 검증 |

---

## 2. 기술 스택 및 인프라 제약 (Tech Stack & Constraints)

### 2-1. 선택된 기술

| 구성요소 | 선택 | 버전 | 근거 |
|--------|------|------|------|
| **언어** | Python | 3.10 이상 | 표준 라이브러리 충분, match 문 등 가독성 기능 활용 가능 |
| **직렬화(저장)** | pickle | 표준 라이브러리 | 파이썬 객체 바이너리 저장/복원 용이 |
| **유효성 검사** | re (정규식) | 표준 라이브러리 | 전화번호 형식 검증 |
| **실행 환경** | 콘솔/터미널 | OS 무관 | Windows/macOS/Linux 공통 |

### 2-2. 라이브러리 버전 충돌 분석

**결론**: 버전 충돌 위험 없음

- 본 프로그램은 `pickle`, `re` 등 **Python 표준 라이브러리만 사용**
- 외부 패키지(`pip install` 대상) 전혀 미사용
- 표준 라이브러리는 Python 인터프리터에 내장 → 별도 버전 관리 불필요
- 패키지 간 의존성 충돌 원천 차단

**권장 최소 버전**: Python 3.10

**하위 호환성**: `pickle`, `re`는 Python 3.8 이상에서 동작

---

## 3. 시스템 아키텍처 및 데이터 흐름 (System Architecture)

### 3-1. 3계층 아키텍처(Layered Architecture)

콘솔 프로그램이지만 유지보수성을 위해 **3계층 구조**로 설계:

```
┌─────────────────────────────────────────────┐
│     표현 계층 (Presentation Layer)           │
│  - 메뉴 출력                                 │
│  - 사용자 입력 수신                          │
│  - 결과 출력                                 │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│     로직 계층 (Business Logic Layer)         │
│  - 회원 처리 (add/list/update/delete)       │
│  - 유효성 검사 (validate_*)                 │
│  - 동명이인 처리                            │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      데이터 계층 (Data Layer)                │
│  - 메모리: 딕셔너리                         │
│  - 영속화: members.dat (바이너리 파일)      │
└─────────────────────────────────────────────┘
```

**계층별 책임**:

| 계층 | 책임 | 예시 함수 |
|------|------|---------|
| 표현 | 사용자 입출력 | `print_menu()`, `input()` |
| 로직 | 검증·CRUD 처리 | `validate_phone()`, `add_member()`, `update_member()` |
| 데이터 | 메모리·파일 보관 | `load_data()`, `save_data()` |

### 3-2. 데이터 흐름도

```
프로그램 시작
    ↓
load_data() → 파일에서 회원 데이터 읽기
    ↓
members = {...} (메모리의 딕셔너리)
    ↓
무한 루프: print_menu()
    ↓
메뉴 선택 (1~5)
    ├─ 1 → add_member()
    ├─ 2 → list_members()
    ├─ 3 → find_by_name() → update_member()
    ├─ 4 → find_by_name() → delete_member()
    └─ 5 → save_data() → 프로그램 종료
    ↓
save_data() → members를 바이너리 파일에 저장
    ↓
프로그램 종료
```

---

## 4. 기능적 기술 요구사항 (Functional Specs)

### 4-1. 데이터 구조

#### 회원 1명 (딕셔너리)

```python
member = {
    "name": "윤아",          # 이름 (str, 1~5자)
    "phone": "01012345678",  # 전화번호 (str, 식별자)
    "addr": "서울시",        # 주소 (str, 검증 없음)
    "type": "친구",          # 종류 (str: 가족/친구/기타)
}
```

#### 전체 회원 컬렉션 — 권장안 A (dict 구조)

```python
# 구조
members = {
    "01012345678": {"name": "윤아", "phone": "01012345678", "addr": "서울시", "type": "친구"},
    "01023456789": {"name": "윤아", "phone": "01023456789", "addr": "부산시", "type": "가족"},
    ...
}

# 이점
- 전화번호로 O(1) 즉시 조회 가능
- 동명이인 존재해도 전화번호는 고유 → 중복 가입 자연스럽게 방지
- 이름 검색: 전체 값 순회하여 일치 항목 수집 (동명이인 → 리스트로 반환)

# 이름으로 검색 예시 (동명이인 처리)
hits = [m for m in members.values() if m["name"] == "윤아"]
# 결과: [{"name": "윤아", ...}, {"name": "윤아", ...}]
```

### 4-2. 함수 사양 (Function Specification)

| 함수 | 입력 | 출력/효과 | 설명 |
|------|------|---------|------|
| `load_data(path)` | 파일 경로 | dict | 파일 읽어 복원, 없으면 빈 dict 반환 |
| `save_data(path, members)` | 경로, dict | (파일 기록) | pickle로 바이너리 저장 |
| `print_menu()` | - | (화면 출력) | 메뉴 5개 출력 |
| `validate_name(name)` | str | bool | 1~5자 검사 |
| `validate_phone(phone)` | str | bool | 정규식 형식 검사 |
| `validate_type(t)` | str | bool | 가족/친구/기타 검사 |
| `input_member()` | - | dict | 검증 통과한 회원 정보 입력 받기 |
| `add_member(members)` | dict | (dict 갱신) | 회원 추가 |
| `list_members(members)` | dict | (화면 출력) | 총원 + 목록 출력 |
| `find_by_name(members, name)` | dict, str | list | 이름 일치 회원 목록 (동명이인 포함) |
| `update_member(members)` | dict | (dict 갱신) | 검색→선택→수정 |
| `delete_member(members)` | dict | (dict 갱신) | 검색→선택→삭제 |
| `main()` | - | - | 전체 루프 제어 |

### 4-3. 유효성 검사 규칙 (Validation Rules)

#### 검사 규칙

| 대상 | 규칙 | 통과 예 | 실패 예 |
|------|------|--------|--------|
| **이름** | 1자 이상 5자 이내 | 윤아, 김은혁 | (빈 값), 가나다라마바(6자) |
| **전화번호** | 정해진 형식 일치 | 아래 참조 | 123, 010abc |
| **주소** | 검증 없음 | 서울시, 제주도 | (없음 — 빈 값만 거를지 선택) |
| **종류** | 가족/친구/기타 중 하나 | 친구, 가족 | 동료, 직장 |

#### 전화번호 형식 (⚠️ 의사결정 필요)

**원본 과제 불일치**: 규칙 텍스트와 실제 화면 예시가 다름

| 형식 | 정규식 | 근거 |
|------|--------|------|
| **권장안** (선택) | `^010\d{8}$` | 실제 화면 캡처: `01012345678` (11자리, 하이픈 없음) |
| **대안** | `^\d{3}-\d{4}-\d{4}$` | 규칙 텍스트: `000-0000-0000` (하이픈 포함) |

**본 TRD 권장**: 입력은 숫자 11자리로 받되, 형식 검증은 `^010\d{8}$`로 하고, 저장/표시도 입력 그대로(`01012345678`)

```python
import re

def validate_name(name: str) -> bool:
    return 1 <= len(name) <= 5

def validate_phone(phone: str) -> bool:
    # 권장: 11자리 숫자 (010으로 시작)
    return re.fullmatch(r"010\d{8}", phone) is not None
    # 대안: 하이픈 포함
    # return re.fullmatch(r"\d{3}-\d{4}-\d{4}", phone) is not None

def validate_type(t: str) -> bool:
    return t in ("가족", "친구", "기타")
```

### 4-4. 주요 기능별 워크플로우

#### FR-01. 프로그램 시작 & 메뉴 루프

```
프로그램 시작
    ↓
load_data() → 파일 있으면 복원, 없으면 {}
    ↓
[반복]
print_menu()
메뉴 입력 (1~5, 그 외 거부)
    ├─ 1 → add_member()
    ├─ 2 → list_members()
    ├─ 3 → update_member()
    ├─ 4 → delete_member()
    └─ 5 → save_data() + 종료
```

#### FR-02/04/05. 회원 추가/수정/삭제 흐름

```
사용자 이름 입력
    ↓
[검색/추가 분기]

[추가의 경우]
validate_name() → 통과 시 전화번호 입력
validate_phone() → 통과 시 주소/종류 입력
validate_type() → 통과 시 members[phone] = {...}

[수정의 경우]
find_by_name() → 0건 "없습니다" 복귀
         → 1건 바로 수정 단계
         → 2건+ 번호 선택 후 수정 단계
새 정보 입력 + 검증 통과
members[phone] 갱신

[삭제의 경우]
find_by_name() → 0건 "없습니다" 복귀
         → 1건 바로 삭제
         → 2건+ 번호 선택 후 삭제
del members[phone]
```

#### FR-03. 회원 목록 보기

```
총원 계산
    ↓
0명이면: "저장된 회원이 없습니다."
         또는 "총 0명..."
    ↓
1명 이상: "총 N명..."
         각 회원을 정해진 형식으로 1줄씩 출력
         예: "회원정보 : 이름 = 윤아, 전화번호 : 01012345678, 주소 : 서울시, 종류 : 친구"
```

---

## 5. 비기능적 요구사항 (Non-Functional Specs)

| ID | 요구사항 | 설명 |
|----|---------|------|
| **NFR-01** | 강건성(Robustness) | 모든 비정상 입력에도 프로그램이 강제 종료되지 않을 것 |
| **NFR-02** | 가독성(Readability) | 기능별로 함수를 분리하여 코드 가독성 확보 |
| **NFR-03** | 의존성 최소화 | 외부 라이브러리 없이 표준 라이브러리만 사용 |
| **NFR-04** | 인코딩 안정성 | 한글 입출력이 깨지지 않을 것 (한국어 완벽 지원) |
| **NFR-05** | 성능 | 회원 100명 이하에서 즉시 응답 (성능 상 제약 없음) |

---

## 6. 예외 처리 규칙 (Exception Handling)

### 6-1. 발생 위치별 예외 처리

| 발생 위치 | 예외 유형 | 처리 방법 |
|----------|---------|---------|
| **파일 읽기** | `FileNotFoundError` | 빈 dict `{}` 반환 (최초 실행) |
| **파일 읽기** | `EOFError`, `UnpicklingError` | 빈 dict 반환 (파일 손상 복구) |
| **메뉴 입력** | 숫자 변환 실패 | 입력을 문자열로 받아 직접 비교, 또는 `try/except ValueError` |
| **메뉴 입력** | 범위 밖 메뉴 (1~5 아님) | "잘못된 입력입니다." 후 메뉴 재출력 |
| **번호 선택** | 범위 밖 번호 | "잘못된 번호입니다." 후 재입력 |
| **검색** | 결과 0건 (없는 회원) | "해당하는 회원 정보가 없습니다." 후 메뉴 복귀 |
| **입력 필드** | 빈 값 | 유효성 검사에서 거부, 재입력 유도 |

### 6-2. 예외 처리 코드 패턴

#### 메뉴 입력 안전 처리

```python
choice = input("선택: ").strip()
if choice not in ("1", "2", "3", "4", "5"):
    print("잘못된 입력입니다.")
    continue  # 메뉴 재출력
```

#### 파일 읽기 안전 처리

```python
import pickle

def load_data(path):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return {}  # 최초 실행
    except (pickle.UnpicklingError, EOFError):
        return {}  # 파일 손상 시 안전 복구
```

#### 파일 저장

```python
def save_data(path, members):
    with open(path, "wb") as f:
        pickle.dump(members, f)
```

### 6-3. 핵심 원칙

**NFR-01 연계**: 어떤 입력에도 프로그램이 죽지 않도록, 입력을 받는 모든 지점에 검증 또는 `try/except`를 둔다.

---

## 7. 영속화(Persistence) 설계

### 7-1. pickle을 이용한 직렬화/역직렬화

```python
import pickle

# 저장 (직렬화) — 반드시 바이너리 모드 'wb'
def save_data(path, members):
    with open(path, "wb") as f:
        pickle.dump(members, f)

# 읽기 (역직렬화) — 바이너리 모드 'rb'
def load_data(path):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return {}
    except (pickle.UnpicklingError, EOFError):
        return {}
```

**핵심 포인트**:
- 텍스트 파일: 'w' / 'r'
- **바이너리 파일: 'wb' / 'rb'** ← pickle은 반드시 `b` 모드 필수

### 7-2. 저장 시점 전략

| 전략 | 설명 | 권장 상황 | 장·단점 |
|------|------|---------|--------|
| **종료 시 저장** (원본 기준) | 메뉴 5에서 1회만 저장 | 과제 요구사항 충족 | ✓ 단순, ✗ 비정상 종료 시 데이터 손실 |
| **즉시 저장** (대안) | 추가/수정/삭제 직후마다 저장 | 실무 권장 | ✓ 안전, ✗ 약간 느림 |

**본 TRD 선택**: 원본 기준 "종료 시 저장" 구현, 필요시 "즉시 저장"으로 강화 가능

### 7-3. ⚠️ pickle 보안 주의

pickle은 신뢰할 수 없는 출처의 파일을 역직렬화하면 임의 코드 실행 위험이 있다.

**안전 범위**: 본 프로그램이 직접 만든 파일만 읽음 → **안전**

**실무**: 외부 데이터는 JSON, 내부 신뢰 데이터는 pickle로 구분

---

## 8. 데이터베이스 설계 대안

본 프로젝트는 파일 기반이지만, 실무 확장을 위한 참고:

| 계층 | 과제 프로젝트 | 실무 시스템 |
|------|-------------|----------|
| 데이터 모델 | dict: {"phone": member} | SQL 테이블: users(id, name, phone, addr, type) |
| 조회 | members.values() | SELECT * FROM users |
| 검색 | [m for m in ... if ...] | SELECT * FROM users WHERE name = '윤아' |
| 저장 | pickle.dump(members, f) | INSERT/UPDATE INTO users |
| 삭제 | del members[phone] | DELETE FROM users WHERE phone = '...' |

---

## 9. 인수 조건 (Acceptance Criteria)

### 9-1. 기능 인수 체크리스트

프로그램이 다음을 모두 만족할 때 완성으로 간주한다:

#### 데이터 저장·복원
- [ ] **FN-001**: 파일 없을 때 오류 없이 빈 상태로 시작
- [ ] **FN-008**: 종료 후 재실행 시 데이터 유지 (pickle 저장/로드 정상)

#### CRUD 기능
- [ ] **FN-003**: 회원 추가 → 모든 4개 항목 입력, 유효성 통과 후 추가
- [ ] **FN-004**: 회원 목록 → 총원 표시 + 각 회원을 정해진 형식으로 1줄 출력
- [ ] **FN-006**: 회원 수정 → 동명이인 처리(번호 선택) + 새 정보 입력 + 검증
- [ ] **FN-007**: 회원 삭제 → 동명이인 처리(번호 선택) + 삭제 완료

#### 메뉴·예외 처리
- [ ] **FN-002**: 메뉴 루프 → 1~5 외 입력 시 거부 후 재출력, 5 선택 시 저장 후 종료
- [ ] **NFR-01**: 어떤 입력에도 프로그램이 강제 종료되지 않음

#### 유효성 검사
- [ ] **FN-009**: 이름 1~5자만 허용
- [ ] **FN-009**: 전화번호 형식 검증 (010으로 시작하는 11자리 또는 000-0000-0000)
- [ ] **FN-009**: 종류는 가족/친구/기타 중 하나만 허용

### 9-2. 테스트 시나리오

| TC | 입력/행위 | 기대 결과 |
|----|---------|---------|
| **TC-01** | 최초 실행(파일 없음) | 오류 없이 빈 목록으로 시작 |
| **TC-02** | 정상 회원 추가 후 목록 보기 | 추가한 회원이 보임, 총원 +1 |
| **TC-03** | 이름 6자 이상 입력 | 거부, 재입력 요구 |
| **TC-04** | 전화번호 형식 오류(123, 010abc) | 거부, 재입력 요구 |
| **TC-05** | 종류 잘못된 값(동료) | 거부, 재입력 요구 |
| **TC-06** | 동명이인 2명 중 1명 수정 | 번호 선택 후 해당 회원만 수정 |
| **TC-07** | 없는 이름 삭제 시도 | "해당하는 회원 정보가 없습니다." |
| **TC-08** | 메뉴에 abc 입력 | "잘못된 입력입니다.", 미종료 |
| **TC-09** | 종료 후 재실행 | 직전 데이터 그대로 복원 |

---

## 10. 파일 구조 및 배포

### 10-1. 디렉터리 구조

```
member_manager/
├── member_manager.py      # 메인 프로그램 (단일 파일)
├── members.dat            # 자동 생성되는 바이너리 데이터 파일
└── README.md              # 실행 방법 안내
```

### 10-2. 실행 방법

```bash
# 터미널에서
python member_manager.py
```

### 10-3. 주의사항

- **Python 버전**: 3.10 이상 필수
- **외부 패키지**: 설치 불필요 (표준 라이브러리만 사용)
- **한글 지원**: Windows/macOS/Linux 모두 정상 작동
- **데이터 파일**: `members.dat`는 자동 생성, 수동 수정 금지 (pickle 바이너리)

---

## 11. 개발자용 구현 체크리스트

프로그램 구현 완료 기준:

```
[ ] load_data / save_data 바이너리 모드( rb / wb ) 확인
[ ] 시작 시 load_data , 종료 시 save_data 호출
[ ] 4개 CRUD 함수 분리 구현 (add/list/update/delete)
[ ] 3종 유효성 검사 함수 (validate_name/phone/type)
[ ] 동명이인 번호 선택 로직 구현
[ ] 없는 회원 / 잘못된 메뉴 예외 처리
[ ] 한글 출력 인코딩 정상 확인
[ ] 테스트 시나리오 TC-01~09 전수 통과
[ ] 메인 루프가 무한 반복되고 5 선택 시에만 종료
[ ] 모든 입력 실패해도 프로그램이 죽지 않음(NFR-01)
```

---

## 12. 참고 자료 및 후속 문서

| 문서 | 역할 |
|------|------|
| **과제목적** | "왜" 이 프로젝트를 하는지, 학습 목표 |
| **구현요구사항** | "무엇을" 구현할 기능, 상세 명세 |
| **화면정의서** | 콘솔 화면 레이아웃, UI/UX |
| **기능정의서** | 함수 단위 상세 기능 (입력·처리·출력) |
| **PRD** | 사용자 관점의 기능 요구사항 |
| **TRD** | 개발자 관점의 기술 설계 (본 문서) |

**문서 읽는 순서**: 과제목적 → 구현요구사항 → 화면정의서 → 기능정의서 → PRD → TRD

---

## 부록: 개발 시 유의사항

### A. pickle 저장/로드 예시

```python
import pickle

# 저장
def save_data(path, members):
    try:
        with open(path, "wb") as f:
            pickle.dump(members, f)
        print("저장 완료")
    except Exception as e:
        print(f"저장 실패: {e}")

# 로드
def load_data(path):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        print("신규 시작")
        return {}
    except Exception as e:
        print(f"로드 실패: {e}")
        return {}
```

### B. 정규식 테스트

```python
import re

# 전화번호 검증 테스트
pattern = r"010\d{8}"
tests = [
    ("01012345678", True),   # 통과
    ("01012345679", True),   # 통과
    ("123", False),          # 실패
    ("010abc", False),       # 실패
    ("01012345", False),     # 7자 - 실패
]

for phone, expected in tests:
    result = re.fullmatch(pattern, phone) is not None
    print(f"{phone}: {result} (expected: {expected})")
```

### C. 주요 Python 문법

```python
# 딕셔너리 순회
for phone, member in members.items():
    print(f"{member['name']} - {phone}")

# 조건부 리스트 수집 (동명이인 찾기)
hits = [m for m in members.values() if m["name"] == "윤아"]

# 정규식 검증
if re.fullmatch(r"010\d{8}", phone):
    print("유효한 전화번호")
```

---

**문서 완성**: 2026-07-10  
**상태**: 최종(Final) — 개발 착수 가능
