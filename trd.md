# 연락처 관리 웹 서비스 (Contact Management Web Service)
## Technical Requirements Document (기술 요구사항 정의서)

| 항목 | 내용 |
| :--- | :--- |
| **문서명** | 연락처 관리 웹 서비스 TRD (2차 과제) |
| **버전** | v1.0 (Baseline) |
| **대상 언어/환경** | Python 3.12+ / FastAPI 0.139.0 / SQLAlchemy 2.0.51 / PostgreSQL 16 |
| **인증 방식** | Session-based Cookie Auth (with Passlib/Argon2) |
| **인코딩 규격** | UTF-8 (전 계층 한글 입출력 보장) |

---

## 1. 아키텍처 및 디렉토리 구조 (Directory Architecture)

본 프로젝트는 비기능 요구사항(NFR-02)에 따라 단일 파일 구현을 금지하며, 계층 분리(Separation of Concerns) 원칙을 준수하여 아키텍처를 구성합니다.

```text
contact_app/
├── main.py              # 앱 진입점, FastAPI 인스턴스, 미들웨어 및 라우터 등록
├── database.py          # DB Engine 설정, SessionLocal 및 Base 모델 선언
├── models.py            # SQLAlchemy ORM 데이터베이스 테이블 스키마 정의
├── schemas.py           # Pydantic v2 기반의 DTO 입출력 및 데이터 유효성 검사 스키마
├── security.py          # 패스워드 Argon2 해싱 및 세션 비즈니스 로직
├── crud.py              # SQL 쿼리 추상화 레이어 (데이터베이스 액세스 전담)
├── routers/             # API 엔드포인트 계층 (웹 라우터 분리)
│   ├── auth.py          # 회원가입, 로그인, 로그아웃, 세션 조회 (/auth)
│   ├── contacts.py      # 연락처 CRUD API (/contacts)
│   └── categories.py    # 카테고리 CRUD API (/categories)
└── static/              # 정적 프론트엔드 리소스 자원
    └── index.html       # SPA(Single Page Application) 구조의 HTML/JS 파일 (GET /)
```
## 2. 데이터베이스 물리 스펙 및 매핑 모델 (Database Physical Schema)

SQLAlchemy 2.0 선언형 스타일(`Mapped`, `mapped_column`)을 적용하여 4개의 테이블 간 관계를 설정합니다. 사용자 격리(NFR-04)를 위해 `user_id` 외래키를 기반으로 논리적 격리를 수행합니다.

### 2.1. `users` 테이블 (사용자 엔티티)
* **물리명**: `users`
* **설명**: 회원가입된 사용자 계정 정보를 관리합니다.

| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| **id** | `Integer` | PK, Autoincrement | 고유 식별자 |
| **username** | `String(50)` | Unique, Not Null | 로그인 ID |
| **hashed_password** | `String(255)` | Not Null | Argon2 해시값 포맷의 비밀번호 |

### 2.2. `sessions` 테이블 (인증 세션 데이터 구조)
* **물리명**: `sessions`
* **설명**: 사용자의 로그인 상태 유지를 위한 세션 토큰 스토어입니다.

| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| **session_id** | `String(255)` | PK | UUIDv4 또는 암호학적 랜덤 문자열 |
| **user_id** | `Integer` | FK (`users.id`), Not Null | 세션 소유 사용자 (ON DELETE CASCADE) |
| **created_at** | `DateTime` | Not Null | 세션 생성 일시 (Default: `func.now()`) |

### 2.3. `categories` 테이블 (연락처 분류 군)
* **물리명**: `categories`
* **설명**: 사용자가 분류하는 카테고리 정보입니다. 가입 시 기본 3종이 바인딩됩니다.

| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| **id** | `Integer` | PK, Autoincrement | 고유 식별자 |
| **name** | `String(20)` | Not Null | 카테고리명 (ex. 가족, 친구, 기타) |
| **user_id** | `Integer` | FK (`users.id`), Not Null | 카테고리 소유 사용자 (ON DELETE CASCADE) |

* **제약조건:** 동일 유저 내 카테고리명 중복 방지를 위한 복합 유니크 인덱스(`UniqueConstraint`) 권장: `(user_id, name)`

### 2.4. `contacts` 테이블 (연락처 정보 원장)
* **물리명**: `contacts`
* **설명**: 개별 연락처의 마스터 데이터 항목입니다.

| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| **id** | `Integer` | PK, Autoincrement | 고유 식별자 |
| **name** | `String(10)` | Not Null | 연락처 소유자 이름 (유효성 검사 대상) |
| **phone** | `String(15)` | Unique, Not Null | 전화번호 (시스템 전체 혹은 유저별 선택 가능, 중복 차단) |
| **address** | `String(255)` | Not Null | 주소 |
| **user_id** | `Integer` | FK (`users.id`), Not Null | 연락처 소유 사용자 (ON DELETE CASCADE) |
| **category_id**| `Integer` | FK (`categories.id`) | 참조 카테고리 ID (Restrict / No Action으로 삭제 방지) |

## 3. 입출력 데이터 무결성 검사 정의 (Data Validation Schemas)

Pydantic v2 규격에 따라 입력 필드를 검증하며, 정규표현식 매칭 실패 시 FastAPI 내장 익셉션 핸들러를 통해 `422 Unprocessable Entity`를 자동 반환하도록 설계합니다.

### 3.1. 연락처 검증 도메인 제약 조건 (`ContactCreate` / `ContactUpdate`)

| 필드명 | 데이터 타입 | 유효성 검사 및 정규표현식 규칙 | 비고 |
| :--- | :--- | :--- | :--- |
| **name** | `str` | `Field(..., min_length=1, max_length=5)`<br>한글 정규식 필터링 적용: `^[가-힣]{1,5}$` | 1자 이상 5자 이내의 한글만 허용 |
| **phone** | `str` | 하이픈이 제외된 `010` 시작 11자리 숫자 조건 매핑:<br>`^010\d{8}$` | 중복 및 포맷 검증 필수 |
| **address** | `str` | 문자열의 종미가 반드시 '시'로 끝나는 구조 패턴 제한:<br>`^.*시$` | 예: "서울시", "수원시" 등 |
| **category_id**| `int` | `Field(...)` | 필수 입력 값 |

### 3.2. 인증 도메인 제약 조건 (`UserCreate` / `UserLogin`)

* **아이디 (`username`)**
  * **타입:** `str`
  * **검증 규칙:** 앞뒤 공백 제거(`strip=True`), 최소 1자 이상 필수 입력
* **비밀번호 (`password`)**
  * **타입:** `str`
  * **검증 규칙:** 클라이언트 단에서는 평문(Plain Text) 문자열로 전송받으며, 비즈니스 로직 진입 후 `security.py` 레이어에서 `Argon2` 알고리즘을 통해 해싱 처리 후 저장

  ## 4. API 엔드포인트 세부 명세 (API Specification)

모든 데이터 API(인증 제외)는 요청 헤더의 `Cookie`에서 `session_id`를 파싱하여 세션 유효성을 먼저 검증해야 합니다. 미인증 상태이거나 세션이 만료된 경우 `401 Unauthorized`를 즉시 반환하며 비즈니스 로직 진입을 차단합니다.

### 4.1. 인증 라우터 (`/auth`)

| HTTP Method | URL Path | Request Body / Params | 기대 응답 (성공) | 예외 및 대응 상태 코드 |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/auth/signup` | `UserCreate` (JSON) | `201 Created`<br>유저 정보 반환 | `409 Conflict`: 이미 존재하는 아이디 |
| **POST** | `/auth/login` | `UserLogin` (Form/JSON) | `200 OK`<br>`Set-Cookie` 세션 발급 | `401 Unauthorized`: 일치하지 않는 아이디 또는 비밀번호 |
| **POST** | `/auth/logout` | 없음 (Cookie 지참) | `200 OK`<br>쿠키 파기 및 만료 처리 | `401 Unauthorized`: 유효하지 않거나 만료된 세션 정보 |
| **GET** | `/auth/me` | 없음 (Cookie 지참) | `200 OK`<br>현재 로그인된 유저 메타 정보 | `401 Unauthorized`: 미로그인 유저 접근 권한 없음 |

### 4.2. 연락처 라우터 (`/contacts`)

> 💡 **비기능 요구사항 준수 (사용자 격리):** 데이터 노출 및 변조 방지를 위해 모든 조회/수정/삭제 쿼리문 실행 시 `WHERE user_id = current_user.id` 조건을 원자적으로 강제 적용합니다.

| HTTP Method | URL Path | Request Body / Params | 기대 응답 (성공) | 예외 및 대응 상태 코드 |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/contacts` | `ContactCreate` (JSON) | `201 Created`<br>추가된 연락처 데이터 | `422 Unprocessable Entity`: 입력값 유효성 검사 실패<br>`409 Conflict`: 시스템 내 이미 등록된 전화번호<br>`404 Not Found`: 유효하지 않거나 존재하지 않는 `category_id` 참조 시 |
| **GET** | `/contacts` | 없음<br>*(Query Param - Optional: 검색어)* | `200 OK`<br>본인 소유의 연락처 리스트 | `401 Unauthorized`: 유효한 세션 쿠키가 없음 |
| **PATCH** | `/contacts/{id}` | `ContactUpdate` (JSON) | `200 OK`<br>수정 완료된 연락처 데이터 | `404 Not Found`: 대상 연락처 ID가 없거나 타인의 데이터에 접근한 경우 (격리) |
| **DELETE** | `/contacts/{id}` | Path Parameter: `id` | `200 OK`<br>삭제 확인 완료 메시지 | `404 Not Found`: 대상 연락처 ID가 없거나 타인의 데이터에 접근한 경우 (격리) |

### 4.3. 카테고리 라우터 (`/categories`)

| HTTP Method | URL Path | Request Body / Params | 기대 응답 (성공) | 예외 및 대응 상태 코드 |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/categories` | `CategoryCreate` (JSON) | `201 Created`<br>생성된 카테고리 데이터 | `409 Conflict`: 동일 유저 내 이미 중복된 카테고리명 존재 |
| **GET** | `/categories` | 없음 | `200 OK`<br>본인의 카테고리 전체 목록 | `401 Unauthorized`: 세션 미확인 및 권한 없음 |
| **PATCH** | `/categories/{id}`| `CategoryCreate` (JSON) | `200 OK`<br>변경 완료된 카테고리 데이터 | `404 Not Found`: 타인의 카테고리 ID이거나 존재하지 않는 ID 수정 시 |
| **DELETE** | `/categories/{id}`| Path Parameter: `id` | `200 OK`<br>카테고리 삭제 완료 | **`409 Conflict`**: 해당 카테고리를 소유하거나 참조 중인 연락처가 1건이라도 존재할 시 무결성 제약에 의해 비즈니스 예외 거부 처리 |

## 5. 핵심 컴포넌트별 함수 및 로직 명세

### 5.1. `security.py` (보안 및 데이터 격리 엔진)

인증 프로세스의 핵심 보안을 담당하며, `passlib(Argon2)`를 활용한 단방향 비밀번호 암호화 및 FastAPI 의존성 주입(`Depends`)을 통한 사용자 세션 검증을 수행합니다.

---

#### 🔑 `get_password_hash(password: str) -> str`
* **설명:** 사용자가 회원가입 시 입력한 평문(Plain Text) 비밀번호를 암호학적으로 안전한 해시 문자열로 변환합니다.
* **구현 가이드:** `passlib.context` 객체의 `CryptContext(schemes=["argon2"])`를 내부적으로 활용하여 인코딩을 수행합니다. (NFR-03 패스워드 암호화 요구사항 준수)
* **입력 매개변수:**
  * `password`: `str` (사용자가 입력한 평문 패스워드)
* **반환값:** `str` (Argon2 알고리즘으로 단방향 암호화된 해시 텍스트)

---

#### 🔄 `verify_password(plain_password: str, hashed_password: str) -> bool`
* **설명:** 로그인 요청 시 사용자가 제출한 평문 비밀번호와 데이터베이스(`users` 테이블)에 저장되어 있는 해시된 비밀번호가 일치하는지 비교 검증합니다.
* **구현 가이드:** 암호학적 타이밍 공격(Timing Attack)을 방지하기 위해 평문 문자열을 직접 비교하지 않고, `CryptContext`가 제공하는 안전한 검증 메커니즘을 사용합니다.
* **입력 매개변수:**
  * `plain_password`: `str` (로그인 시 유저가 입력한 평문 패스워드)
  * `hashed_password`: `str` (DB에 보관 중인 기존 해시 패스워드)
* **반환값:** `bool` (일치 여부에 따라 `True` 또는 `False` 반환)

---

#### 🛡️ `get_current_user(db: Session, session_id: str = Cookie(None))`
* **설명:** HTTP 요청 헤더에 포함된 쿠키(Cookie)를 분석하여 현재 접근한 사용자가 누구인지 식별하고 유효성을 검증하는 **인증 가드(Guard)** 역할을 합니다.
* **구현 가이드:**
  * FastAPI Dependency Injection(`Depends`) 레이어 및 API 라우터의 공통 미들웨어 단에서 실행됩니다.
  * 전달받은 쿠키의 `session_id`를 기반으로 데이터베이스의 `sessions` 테이블을 조회합니다.
  * 세션이 유효할 경우 연결된 `users` 레코드(객체)를 인프라 레벨에서 반환합니다.
* **입력 매개변수:**
  * `db`: `Session` (SQLAlchemy DB 세션 객체)
  * `session_id`: `str` (HTTP Request Cookie에서 파싱된 세션 고유 식별자, 기본값 `None`)
* **예외 및 상태 코드 반환 규칙:**
  * 만약 쿠키에 `session_id`가 없거나, `sessions` 테이블 조회 결과 만료/유실되어 유효하지 않은 세션일 경우, 비즈니스 로직 진입을 전면 차단하고 즉시 **`HTTPException(status_code=401, detail="...")`** 예외를 송출합니다.
* **반환값:** `models.User` (인증에 성공한 사용자의 SQLAlchemy ORM 모델 객체)

## 6. 비기능적 요구사항 및 에러 가이드 (NFR & Exception Handling)

시스템의 가용성과 데이터 무결성을 확보하고, 예외적인 사용자 유입 및 시스템 장애 상황에서도 서비스 안정성을 유지하기 위한 비기능적 명세입니다.

---

### 6.1. `NFR-01`: 치명적 에러 회피 및 글로벌 예외 핸들링 (Fatal Error Bypass)
* **목적:** 어떠한 예측 불허의 런타임 오류가 발생하더라도 백엔드 인프라가 다운되거나 클라이언트에게 가공되지 않은 `500 Internal Server Error`를 그대로 노출하지 않도록 방어합니다.
* **구현 명세:** * 애플리케이션 진입점(`main.py`)에 최상위 예외 클래스인 `Exception`을 캐치하는 글로벌 익셉션 핸들러(`@app.exception_handler(Exception)`) 또는 커스텀 미들웨어를 등록합니다.
  * 내부 시스템 에러 및 디버깅용 트레이스백(Traceback) 로그는 서버 내부 콘솔(`stdout/stderr`)에만 기록합니다.
  * 클라이언트에게는 아래와 같이 규격화된 표준 JSON 에러 메시지와 예외 상황에 매핑되는 적절한 HTTP 상태 코드(`400`, `401`, `404`, `409`, `422` 등)를 반환합니다.

```json
{
  "detail": "서버 내부에서 처리할 수 없는 오류가 발생했습니다. (익셉션 메시지)"
}
```
### 6.2. 한글 깨짐 방지 및 인코딩 규격 표준화 (`NFR-05`)

* **목적:** 웹 브라우저 및 클라이언트 환경에 관계없이 데이터 전송 과정에서 한글 데이터를 온전히 보존합니다.
* **구현 명세:** 백엔드 API 서버에서 반환하는 모든 JSON Response 및 HTML 정적 리소스 응답 헤더에 데이터 포맷 및 문자셋 컨텍스트를 강제 인입합니다.
* **응답 헤더 매개변수:** `Content-Type: application/json; charset=utf-8` 및 `text/html; charset=utf-8` 규격을 시스템 기본값으로 고정합니다.


## 7. 기능 구현 점검 매트릭스 (Verification Metric)

- [ ] **TR-001 (DB 구조 자동 생성 검증):** 인프라 환경(PostgreSQL) 기동 상태에서 API 서버가 최초 구동될 때, SQLAlchemy의 `Base.metadata.create_all(bind=engine)` 메커니즘에 의해 설계된 4개 데이터 테이블(`users`, `sessions`, `categories`, `contacts`) 구조가 영속성 스토어 내에 유실 없이 자동 빌드되는가?
- [ ] **TR-002 (인터랙티브 자동 문서화 보장):** 웹 브라우저를 통해 `/docs` (Swagger UI) 엔드포인트에 접근했을 때, `schemas.py`에 선언한 Pydantic v2 스키마 기반의 데이터 타입 사양과 API 라우터 명세가 동적으로 매핑 및 렌더링되어 즉시 테스트 가능한 상태로 제공되는가?
- [ ] **TR-003 (동적 런타임 데이터 격리성):** 시스템 내 인가된 'A' 계정의 쿠키 세션(`session_id`)을 지참한 채 주소록 조회 API(`GET /contacts`)를 호출하는 경우, 데이터베이스 내에 소유권자 ID(`user_id`)가 'B'로 격리 등록되어 있는 타인의 데이터가 단 1건도 유출되거나 침해되지 않는가?
- [ ] **TR-004 (외래키 무결성 및 참조 제약):** 특정 카테고리 ID를 외래키로 참조하여 소속되어 있는 연락처 원장 데이터가 시스템에 최소 1건 이상 존재하는 상태에서, 해당 카테고리 삭제 API(`DELETE /categories/{id}`) 요청이 인입될 때, DB 레벨의 Foreign Key Restrict 제약 또는 비즈니스 단의 카운트 쿼리 검증을 거쳐 `409 Conflict` 예외를 올바르게 송출하고 삭제를 방어하는가?
- [ ] **`TR-005` (공백 아이디 차단)**
  * **테스트 케이스:** 회원가입(`POST /auth/signup`) 요청 시 `username: "   "` (공백만으로 구성된 문자열) 전송
  * **기대 결과:** Pydantic의 `strip=True` 또는 커스텀 `strip_username` 검증기에 의해 전후 공백이 제거되어 최종 길이가 0이 됨으로써 비즈니스 로직 진입 전 `422 Unprocessable Entity` 표준 에러 템플릿이 반환되는가?

- [ ] **`TR-006` (로그아웃 후 세션 무효화)**
  * **테스트 케이스:** `POST /auth/logout` 성공 직후, 소지하고 있던 `session_id` 쿠키 값을 그대로 활용하여 `GET /auth/me`를 호출
  * **기대 결과:** DB의 `sessions` 테이블에서 해당 토큰이 실제로 삭제(Delete)되었으므로, `security.py` 가드가 이를 감지하고 `401 Unauthorized`를 정상 반환하는가?

- [ ] **`TR-007` (탈취/위조 쿠키 방어)**
  * **테스트 케이스:** 임의로 변조하거나 조작한 세션 데이터(`Cookie: session_id=fake_token_123`)를 헤더에 주입하여 `GET /contacts` 호출
  * **기대 결과:** 비즈니스 로직(CRUD 계층)에 진입하기 전, FastAPI `Depends(get_current_user)` 가드 레이어에서 디비 조회 실패를 인지하고 즉시 `401 Unauthorized`로 클라이언트를 차단하는가?

- [ ] **`TR-008` (이름 한글 규격 엄수)**
  * **테스트 케이스:** 연락처 등록/수정 시 `name` 필드에 영문(`"홍길D"`), 특수문자(`"길동!"`), 자음/모음 분리(`"ㅎㄱㄷ"`), 또는 5자를 초과하는 한글(`"동방신기최강"`) 입력
  * **기대 결과:** 정규식 `^[가-힣]{1,5}$` 매칭 실패로 인해 서버 크래시 없이 `422 Unprocessable Entity`가 즉시 반환되는가?

- [ ] **`TR-009` (전화번호 하이픈 국한 제약)**
  * **테스트 케이스:** `phone` 필드에 하이픈이 포함된 데이터(`"010-1234-5678"`)나 11자리가 아닌 번호(`"0101234567"`) 입력
  * **기대 결과:** Pydantic 밸리데이터(`validate_phone_format`)가 `^010\d{8}$` 규칙에 의거해 거부 처리하고 `422 Unprocessable Entity`를 반환하는가?

- [ ] **`TR-010` (주소 종미 제약 조건)**
  * **테스트 케이스:** `address` 필드에 "서울시 강남구", "경기도 수원", "부산광역시 해운대구" 등 끝 문자가 '시'로 끝나지 않는 주소 포맷 전송
  * **기대 결과:** 정규식 `^.*시$` 검증 조건에 걸려 차단되며, 오직 "서울시", "수원시", "고양시" 등 '시'로 완전히 종결되는 입력만 수용하는가?

- [ ] **`TR-011` (회원가입 시 기본 카테고리 자동 바인딩)**
  * **테스트 케이스:** 신규 사용자 계정 가입(`POST /auth/signup`) 완료 직후, 해당 계정의 쿠키를 지참하여 카테고리 목록조회(`GET /categories`) 요청
  * **기대 결과:** 사용자가 수동으로 생성하지 않았음에도 비즈니스 단(`crud.py`)에서 영속화한 기본 3종 셋트(`"가족"`, `"친구"`, `"기타"`)가 JSON 배열 형태로 응답되는가?

- [ ] **`TR-012` (카테고리명 유저 내 중복 방지)**
  * **테스트 케이스:** 로그인된 유저가 본인 소유의 카테고리 목록에 이미 존재하는 이름(예: `"가족"`)으로 `POST /categories`를 중복 요청
  * **기대 결과:** 데이터베이스의 복합 유니크 제약조건(`UniqueConstraint("user_id", "name")`) 또는 사전 카운트 쿼리에 의해 차단되어 `409 Conflict`가 발생하는가? (※ 단, 다른 유저가 자신의 격리 공간에 `"가족"`을 생성하는 것은 독립적으로 허용되어야 함)

- [ ] **`TR-013` (연락처 수정 시 타인 카테고리 도용 차단)**
  * **테스트 케이스:** 연락처 수정(`PATCH /contacts/{id}`) 요청 시, 본인의 카테고리가 아닌 타인의 고유 ID(`category_id: 9999`)를 강제로 변조 인입 시도
  * **기대 결과:** `crud.get_category_by_id_and_user`에서 데이터가 감지되지 않으므로, 외래키 무결성 크래시를 유발하기 전에 비즈니스 레이어에서 `404 Not Found` (또는 카테고리 참조 오류 예외)로 안전하게 격리 방어하는가?

- [ ] **`TR-014` (글로벌 런타임 에러 은폐 및 표준화)**
  * **테스트 케이스:** 백엔드 구동 중 강제로 데이터베이스 연결을 끊거나(`DB Down`), 인위적인 내부 문법 오류를 일으켜 크래시 유발
  * **기대 결과:** 클라이언트 진영에 민감한 인프라 정보(파이썬 소스 트레이스백, SQL Raw 쿼리문 등)가 노출되지 않고, `main.py`에 구현된 글로벌 예외 핸들러가 가로채어 규격화된 표준 에러 포맷(`{"detail": "서버 내부에서 처리할 수 없는 오류가 발생했습니다. (...)"}`)과 함께 `500 Internal Server Error` 코드로 변환되어 나가는가?
