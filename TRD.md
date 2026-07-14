# 연락처 관리 웹 서비스 (Contact Management Web Service) 
## 기술 요구사항 정의서(TRD)

**버전**: 2.1  
**작성일**: 2026-07-14  
**최종 검토일**: -

---

## 1. 목적 및 배경 (Goals & Background)

### 1.1. 비즈니스 목표
본 프로젝트는 개인 사용자가 연락처(이름, 전화번호, 주소)를 웹 기반으로 **안전하게 관리**할 수 있는 
풀스택 웹 애플리케이션을 구축하는 것을 목표로 합니다.

**주요 목표:**
- 개인별 격리된(Multi-tenant) 연락처 저장소 제공
- 사용자 맞춤형 카테고리(그룹) 기반 연락처 분류 지원
- 직관적인 웹 UI를 통한 CRUD(Create, Read, Update, Delete) 기능 제공
- 데이터 무결성과 보안을 최우선으로 설계

### 1.2. 핵심 기능 영역
1. **사용자 인증**: 회원가입 및 로그인 (세션 쿠키 기반)
2. **연락처 관리**: 등록, 조회, 수정, 삭제
3. **카테고리 관리**: 사용자 정의 그룹 생성 및 관리
4. **데이터 검증**: 입력값 형식 엄격 검증 (정규식)

---

## 2. 기술 스택 및 인프라 제약 (Tech Stack & Constraints)

### 2.1. 백엔드 기술 스택

| 컴포넌트 | 기술/도구 | 버전 |
|---------|--------|------|
| **프레임워크** | FastAPI | 0.110.0 |
| **ASGI 서버** | Uvicorn | 0.28.0 |
| **ORM** | SQLAlchemy | 2.0.28 |
| **데이터베이스** | PostgreSQL / SQLite | 15-alpine / Built-in |
| **비밀번호 해싱** | Passlib + Argon2 | 1.7.4 + 23.1.0 |
| **데이터 검증** | Pydantic | 2.6.4 |
| **CORS** | FastAPI CORS Middleware | Built-in |

**선택 이유:**
- **FastAPI**: 빠른 개발, 자동 문서화(Swagger), 타입 안전성
- **SQLAlchemy**: ORM 표준, 복잡한 쿼리 지원, 다양한 DB 지원
- **Argon2**: NIST 권장 해시 알고리즘, GPU 무차별 대입 공격 방어
- **Pydantic**: 데이터 검증 자동화, 정규식 패턴 강제

### 2.2. 프론트엔드 기술 스택

| 컴포넌트 | 기술 | 설명 |
|---------|------|------|
| **마크업** | HTML5 | 시맨틱 구조 |
| **스타일** | CSS3 | 반응형 디자인 |
| **로직** | Vanilla JavaScript | 번들러 미사용, 직접 Fetch API |

**특징:**
- 프레임워크 미사용 (경량, 의존성 최소화)
- Fetch API를 통한 REST 비동기 통신
- Live Server 연동 지원 (포트: 5500)

### 2.3. 데이터베이스 구성

**개발 환경:**
- SQLite (`contact_app.db`)
- 환경 변수 `DATABASE_URL` 미설정 시 자동 선택

**운영 환경 (Docker):**
- PostgreSQL 15-alpine
- 자동 한글 UTF-8 인코딩 설정
- 데이터 지속성: `postgres_data` 볼륨

### 2.4. 인프라 & 배포

**개발 환경:**
- 로컬 머신에서 Python 직접 실행
- `python -m uvicorn main:app --reload`

**운영 환경:**
- Docker Compose (v2.0+) 기반 컨테이너 오케스트레이션
- 서비스 구성:
  - `postgres`: PostgreSQL DB (포트 5432)
  - `backend`: FastAPI (포트 8001 → 8000)
  - `pgAdmin`: DB 웹 관리 (포트 5050)
- 네트워크: `contact_network` (브릿지)

### 2.5. 시스템 요구사항

**최소 사양:**
- CPU: 2 cores (도커 환경)
- 메모리: 512MB (도커 환경)
- 디스크: 100MB (데이터베이스 포함)

**필수 소프트웨어:**
- Docker 20.10+
- Docker Compose 2.0+
- 또는 Python 3.11+, PostgreSQL 12+

---

## 3. 시스템 아키텍처 및 데이터 흐름 (System Architecture)

### 3.1. 전체 시스템 구조도

```
┌─────────────────────────────────────────────────────────────┐
│                     브라우저 (Client)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  HTML/CSS/JavaScript (SPA - Single Page App)         │  │
│  │  - login / signup 화면                               │  │
│  │  - 연락처 목록/상세/CRUD UI                           │  │
│  │  - 카테고리 선택 UI                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬──────────────────────────────────────────┘
                 │ HTTP(S)
                 │ REST API Calls
                 │ (credentials: include)
                 ▼
    ┌────────────────────────────────────┐
    │     FastAPI 백엔드 서버             │
    │     (포트: 8001 / 내부: 8000)      │
    │                                    │
    │  ┌─────────────────────────────┐  │
    │  │ 라우터 레이어                 │  │
    │  │ ├─ /auth (signin/up/out)    │  │
    │  │ ├─ /contacts (CRUD)         │  │
    │  │ └─ /categories (CRUD)       │  │
    │  └─────────────────────────────┘  │
    │  ┌─────────────────────────────┐  │
    │  │ 비즈니스 로직 (CRUD)         │  │
    │  │ ├─ 인증 검증 (security.py)  │  │
    │  │ ├─ 데이터 CRUD (crud.py)    │  │
    │  │ └─ 스키마 검증 (schemas.py) │  │
    │  └─────────────────────────────┘  │
    │  ┌─────────────────────────────┐  │
    │  │ ORM 매핑 (SQLAlchemy)        │  │
    │  │ ├─ User (사용자)             │  │
    │  │ ├─ Session (세션)            │  │
    │  │ ├─ Contact (연락처)          │  │
    │  │ └─ Category (카테고리)       │  │
    │  └─────────────────────────────┘  │
    └────────────────┬──────────────────┘
                     │ SQL
                     │ (Psycopg2 드라이버)
                     ▼
      ┌──────────────────────────────┐
      │  PostgreSQL / SQLite DB      │
      │  ┌────────────────────────┐  │
      │  │ 테이블 구조:            │  │
      │  │ ├─ users               │  │
      │  │ ├─ sessions            │  │
      │  │ ├─ contacts            │  │
      │  │ └─ categories          │  │
      │  └────────────────────────┘  │
      │  ┌────────────────────────┐  │
      │  │ 저장소:                 │  │
      │  │ ├─ postgres_data       │  │
      │  │ │  (Docker Volume)     │  │
      │  │ └─ contact_app.db      │  │
      │  │    (SQLite 파일)       │  │
      │  └────────────────────────┘  │
      └──────────────────────────────┘
```

### 3.2. 데이터 흐름 (Data Flow)

#### **3.2.1. 회원가입 흐름 (Signup Flow)**

```
1. 사용자 입력 (UI)
   ├─ POST /auth/signup
   │  └─ JSON: { "username": "...", "password": "..." }
   │
2. 백엔드 처리 (auth.py / signup)
   ├─ 1단계: 중복 검사 (get_user_by_username)
   ├─ 2단계: 암호화 (get_password_hash - Argon2)
   ├─ 3단계: 사용자 생성 및 기본 카테고리 3종 원자적 생성
   │  └─ User(username, hashed_password) 생성
   │  └─ Category(name: "가족", user_id) 자동 생성
   │  └─ Category(name: "친구", user_id) 자동 생성
   │  └─ Category(name: "기타", user_id) 자동 생성
   └─ Response: 201 Created + UserResponse
   
3. 자동 로그인 (앱 로직)
   ├─ POST /auth/login
   │  └─ FormData: x-www-form-urlencoded
   │
4. 세션 발급 (auth.py / login)
   ├─ 1단계: 사용자 검증
   ├─ 2단계: 비밀번호 검증 (verify_password)
   ├─ 3단계: UUID 세션 토큰 생성 및 DB 저장
   └─ Response: 200 OK + Set-Cookie: session_id (httponly=True)
```

#### **3.2.2. 로그인 흐름 (Login Flow)**

```
1. 사용자 입력 (UI)
   └─ POST /auth/login (x-www-form-urlencoded)
   
2. 백엔드 인증 처리 (auth.py / login)
   ├─ 1단계: username으로 사용자 조회
   ├─ 2단계: verify_password(입력값, DB해시) 타이밍 공격 방어
   ├─ 3단계: 세션 토큰(UUID) 발급 → sessions 테이블 저장
   └─ Response: 200 OK + Set-Cookie: session_id (24시간 유효)
   
3. 쿠키 저장 (브라우저)
   └─ 이후 모든 API 요청에 자동 포함 (credentials: include)
```

#### **3.2.3. 인증 보호 엔드포인트 흐름 (Protected Endpoint Flow)**

```
사용자 요청 (예: GET /contacts)
   │
   └─ Depends(get_current_user) 의존성 검사
      ├─ 1단계: request.cookies.get("session_id") 추출
      ├─ 2단계: sessions 테이블에서 유효성 검증
      ├─ 3단계: 해당 user_id와 매핑된 User 객체 반환
      └─ 실패 시: 401 Unauthorized
      
성공 시: current_user 객체 라우터에 주입
   └─ CRUD 작업은 current_user.id로 테넌트 격리 수행
```

#### **3.2.4. 연락처 생성 흐름 (Contact Create Flow)**

```
1. 프론트엔드 입력 검증
   └─ 정규식 클라이언트 검증 (선택, 서버 필수)
   
2. POST /contacts
   {
     "name": "김철수",                    ← 한글 1~5자
     "phone": "01012345678",             ← 010-XXXX-XXXX (하이픈 제외)
     "address": "서울시",                 ← "시"로 종결
     "category_id": 1
   }
   
3. 백엔드 처리 (contacts.py / create_new_contact)
   ├─ 1단계: Pydantic 정규식 자동 검증
   │  ├─ name: ^[가-힣]{1,5}$
   │  ├─ phone: ^010\d{8}$
   │  └─ address: ^.*시$
   ├─ 2단계: 시스템 전체 전화번호 중복 검사 (409 Conflict)
   ├─ 3단계: 사용자의 카테고리 소유권 검증 (404 Not Found)
   ├─ 4단계: DB 저장 (created_at, updated_at 자동)
   └─ Response: 201 Created + ContactResponse
```

#### **3.2.5. 연락처 수정 흐름 (Contact Update Flow - PATCH)**

```
PATCH /contacts/{contact_id}
{
  "name": "김철수",        ← Optional (선택)
  "phone": "01098765432", ← Optional
  "address": "부산시",     ← Optional
  "category_id": 2        ← Optional
}

검증 단계:
├─ 1단계: 소유권 검증 (타인 연락처 접근 차단)
├─ 2단계: phone 변경 시 중복 검사 (기존값과 다를 때만)
├─ 3단계: category_id 변경 시 사용자 소유권 재검증
└─ 4단계: 제공된 필드만 업데이트 (updated_at 자동)
```

#### **3.2.6. 카테고리 삭제 흐름 (Category Delete Flow)**

```
DELETE /categories/{category_id}

검증 단계:
├─ 1단계: 사용자 소유권 검증 (404 Not Found)
├─ 2단계: RESTRICT 외래키 제약조건 검사
│  └─ 연락처가 1개라도 남아있으면 IntegrityError 발생
│  └─ 409 Conflict 에러 응답
└─ 3단계: 삭제 성공 시 204 No Content

예시:
- "가족" 카테고리에 연락처 0개 → 삭제 성공
- "친구" 카테고리에 연락처 3개 → 삭제 실패 (409)
```

### 3.3. 엔티티 관계도 (ER Diagram)

```
┌─────────────────┐
│    USERS        │
├─────────────────┤
│ id (PK)         │◄──┐
│ username (UQ)   │   │
│ hashed_password │   │
│ created_at      │   │ 1:N
└─────────────────┘   │
        │             │
        │ 1:N CASCADE │
        ├─────────────┴────────┬─────────────┐
        │                      │             │
        ▼                      ▼             ▼
┌─────────────────┐   ┌──────────────┐  ┌──────────────┐
│   SESSIONS      │   │ CATEGORIES   │  │  CONTACTS    │
├─────────────────┤   ├──────────────┤  ├──────────────┤
│ session_id (PK) │   │ id (PK)      │  │ id (PK)      │
│ user_id (FK)    │   │ name         │  │ name         │
│ created_at      │   │ user_id (FK) │  │ phone (UQ)   │
└─────────────────┘   │ created_at   │  │ address      │
                      └──────────────┘  │ user_id (FK) │
                              ▲         │ category_id  │
                              │         │ (FK-RESTRICT)
                              │ 1:N     │ created_at   │
                              └─────────┤ updated_at   │
                                        └──────────────┘

FK = Foreign Key
UQ = Unique
PK = Primary Key
CASCADE = 부모 삭제 시 자식도 삭제
RESTRICT = 자식이 존재하면 부모 삭제 불가
```

---

## 4. 기능적 기술 요구사항 (Functional Specs / API Specs)

### 4.1. 인증 (Authentication) API

#### **[TR-005] POST /auth/signup - 회원가입**

**요청:**
```http
POST /auth/signup HTTP/1.1
Host: localhost:8001
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePassword123"
}
```

**응답 (201 Created):**
```json
{
  "id": 1,
  "username": "john_doe",
  "created_at": "2026-07-14T12:34:56.789Z"
}
```

**에러 응답:**
- **409 Conflict**: 이미 존재하는 아이디
  ```json
  {
    "detail": "이미 존재하는 아이디입니다."
  }
  ```
- **422 Unprocessable Entity**: 입력값 검증 실패
  ```json
  {
    "detail": [
      {
        "type": "string_too_short",
        "loc": ["body", "username"],
        "msg": "String should have at least 1 characters"
      }
    ]
  }
  ```

**비즈니스 규칙:**
- username: 1~50자, 공백 제거 후 공백만 있으면 거부
- password: 1자 이상 (클라이언트에서 추가 강도 검증 권장)
- 회원가입 성공 즉시 기본 카테고리 3종 자동 생성:
  - "가족"
  - "친구"
  - "기타"

---

#### **[TR-006] POST /auth/login - 로그인**

**요청:**
```http
POST /auth/login HTTP/1.1
Host: localhost:8001
Content-Type: application/x-www-form-urlencoded

username=john_doe&password=SecurePassword123
```

**응답 (200 OK):**
```json
{
  "message": "로그인에 성공했습니다."
}
```

**응답 헤더:**
```
Set-Cookie: session_id=<UUID>; Path=/; HttpOnly; Max-Age=86400; SameSite=Lax
```

**에러 응답:**
- **401 Unauthorized**: 아이디/비밀번호 오류
  ```json
  {
    "detail": "아이디 또는 비밀번호가 올바르지 않습니다."
  }
  ```

**비즈니스 규칙:**
- 비밀번호 검증: Argon2 해시 비교 (타이밍 공격 방어)
- 세션 토큰: UUID v4 무작위 생성
- 세션 유효 기간: 24시간
- 쿠키 옵션:
  - `httponly=True`: XSS 공격 차단
  - `samesite="lax"`: CSRF 공격 방어

---

#### **[TR-006] POST /auth/logout - 로그아웃**

**요청:**
```http
POST /auth/logout HTTP/1.1
Host: localhost:8001
Cookie: session_id=<UUID>
```

**응답 (200 OK):**
```json
{
  "message": "로그아웃이 완료되었습니다."
}
```

**비즈니스 규칙:**
- DB sessions 테이블에서 해당 토큰 영구 삭제
- 브라우저 쿠키 만료 처리

---

### 4.2. 카테고리 (Category) API

#### **[NFR-04] GET /categories - 카테고리 목록 조회**

**요청:**
```http
GET /categories HTTP/1.1
Host: localhost:8001
Cookie: session_id=<UUID>
```

**응답 (200 OK):**
```json
[
  {
    "id": 1,
    "name": "가족",
    "user_id": 1,
    "created_at": "2026-07-14T12:34:56.789Z"
  },
  {
    "id": 2,
    "name": "친구",
    "user_id": 1,
    "created_at": "2026-07-14T12:34:56.789Z"
  },
  {
    "id": 3,
    "name": "기타",
    "user_id": 1,
    "created_at": "2026-07-14T12:34:56.789Z"
  }
]
```

**비즈니스 규칙:**
- 현재 로그인 사용자의 카테고리만 반환
- 타 사용자의 카테고리는 쿼리 레벨에서 필터링
- 기본 3종 카테고리("가족", "친구", "기타") 포함

---

#### **[TR-007] POST /categories - 카테고리 생성**

**요청:**
```http
POST /categories HTTP/1.1
Host: localhost:8001
Content-Type: application/json
Cookie: session_id=<UUID>

{
  "name": "동료"
}
```

**응답 (201 Created):**
```json
{
  "id": 4,
  "name": "동료",
  "user_id": 1,
  "created_at": "2026-07-14T12:34:56.789Z"
}
```

**에러 응답:**
- **422 Unprocessable Entity**: name이 공백 또는 50자 초과
  ```json
  {
    "detail": "카테고리 이름은 공백일 수 없습니다."
  }
  ```

**비즈니스 규칙:**
- name: 1~50자, 공백 제거 후 공백만 있으면 거부
- 동일 사용자 내에서 카테고리명 중복 허용 (현재 구현상)

---

#### **[TR-004] DELETE /categories/{id} - 카테고리 삭제**

**요청:**
```http
DELETE /categories/4 HTTP/1.1
Host: localhost:8001
Cookie: session_id=<UUID>
```

**응답 (204 No Content):**
```
(빈 응답)
```

**에러 응답:**
- **404 Not Found**: 카테고리 없거나 접근 권한 없음
  ```json
  {
    "detail": "해당 카테고리를 찾을 수 없거나 접근 권한이 없습니다."
  }
  ```
- **409 Conflict**: 연락처가 남아있음 (RESTRICT)
  ```json
  {
    "detail": "해당 카테고리에 등록된 연락처가 존재하여 삭제할 수 없습니다. 연락처를 먼저 정리하세요."
  }
  ```

**비즈니스 규칙:**
- 사용자 소유권 검증 필수
- 외래키 제약조건(RESTRICT): 연락처가 1개라도 남아있으면 삭제 불가
- 삭제 전 모든 연락처를 다른 카테고리로 이동하거나 삭제해야 함

---

### 4.3. 연락처 (Contact) API

#### **[TR-008~010] POST /contacts - 연락처 생성**

**요청:**
```http
POST /contacts HTTP/1.1
Host: localhost:8001
Content-Type: application/json
Cookie: session_id=<UUID>

{
  "name": "김철수",
  "phone": "01012345678",
  "address": "서울시",
  "category_id": 1
}
```

**응답 (201 Created):**
```json
{
  "id": 1,
  "name": "김철수",
  "phone": "01012345678",
  "address": "서울시",
  "user_id": 1,
  "category_id": 1,
  "created_at": "2026-07-14T12:34:56.789Z",
  "updated_at": "2026-07-14T12:34:56.789Z"
}
```

**입력 데이터 검증 (정규식):**
- **name**: `^[가-힣]{1,5}$`
  - 한글만 1~5자
  - 예: "김철수" (3자) ✓, "Kim" (영문) ✗, "김철수길동" (5자 초과) ✗
- **phone**: `^010\d{8}$`
  - 010으로 시작하는 11자리 숫자 (하이픈 제외)
  - 예: "01012345678" ✓, "010-1234-5678" (하이픈 있음) ✗, "02031234567" (010 아님) ✗
- **address**: `^.*시$`
  - 반드시 "시"로 종결
  - 예: "서울시" ✓, "서울시 강남구" ✗, "경기도 수원" ✗

**에러 응답:**
- **409 Conflict**: 전화번호 중복 (시스템 전체)
  ```json
  {
    "detail": "이미 시스템에 등록된 전화번호입니다."
  }
  ```
- **404 Not Found**: 지정한 카테고리 없거나 타 사용자 소유
  ```json
  {
    "detail": "지정한 카테고리를 찾을 수 없거나 접근 권한이 없습니다."
  }
  ```
- **422 Unprocessable Entity**: 정규식 미부합
  ```json
  {
    "detail": [
      {
        "type": "string_pattern_mismatch",
        "loc": ["body", "phone"],
        "msg": "String should match pattern '^010\\d{8}$'"
      }
    ]
  }
  ```

**비즈니스 규칙:**
- 전화번호는 시스템 전체에서 유일해야 함 (unique 제약)
- 카테고리 소유권 검증 필수 (타 사용자 카테고리 선택 방지)
- created_at, updated_at 자동 생성

---

#### **[NFR-04] GET /contacts - 연락처 목록 조회**

**요청:**
```http
GET /contacts?search=김&page=1&limit=10 HTTP/1.1
Host: localhost:8001
Cookie: session_id=<UUID>
```

**쿼리 파라미터:**
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|------|------|
| `search` | string | null | 이름 또는 전화번호 부분 일치 검색 |
| `page` | int | 1 | 페이지 번호 (1부터 시작) |
| `limit` | int | 10 | 페이지당 개수 (1~100) |

**응답 (200 OK):**
```json
[
  {
    "id": 1,
    "name": "김철수",
    "phone": "01012345678",
    "address": "서울시",
    "user_id": 1,
    "category_id": 1,
    "created_at": "2026-07-14T12:34:56.789Z",
    "updated_at": "2026-07-14T12:34:56.789Z"
  }
]
```

**비즈니스 규칙:**
- 현재 로그인 사용자의 연락처만 반환
- 검색: name 또는 phone의 부분 일치 (대소문자 무시 예상)
- 페이지네이션: offset = (page - 1) * limit
- 정렬: id 내림차순 (최신 먼저)

---

#### **[NFR-04] GET /contacts/{id} - 연락처 상세 조회**

**요청:**
```http
GET /contacts/1 HTTP/1.1
Host: localhost:8001
Cookie: session_id=<UUID>
```

**응답 (200 OK):**
```json
{
  "id": 1,
  "name": "김철수",
  "phone": "01012345678",
  "address": "서울시",
  "user_id": 1,
  "category_id": 1,
  "created_at": "2026-07-14T12:34:56.789Z",
  "updated_at": "2026-07-14T12:34:56.789Z"
}
```

**에러 응답:**
- **404 Not Found**: 연락처 없거나 타 사용자 소유
  ```json
  {
    "detail": "해당 연락처를 찾을 수 없거나 접근 권한이 없습니다."
  }
  ```

**비즈니스 규칙:**
- 타인의 연락처 ID를 억지로 지정해도 404 반환 (데이터 격리 보장)

---

#### **[NFR-04] PATCH /contacts/{id} - 연락처 수정**

**요청:**
```http
PATCH /contacts/1 HTTP/1.1
Host: localhost:8001
Content-Type: application/json
Cookie: session_id=<UUID>

{
  "name": "김철수",
  "phone": "01098765432",
  "address": "부산시",
  "category_id": 2
}
```

**모든 필드는 선택 사항 (Optional):**
```json
{
  "name": "김철수"
}
```

**응답 (200 OK):**
```json
{
  "id": 1,
  "name": "김철수",
  "phone": "01098765432",
  "address": "부산시",
  "user_id": 1,
  "category_id": 2,
  "created_at": "2026-07-14T12:34:56.789Z",
  "updated_at": "2026-07-14T13:00:00.000Z"
}
```

**에러 응답:**
- **404 Not Found**: 연락처 없음 또는 타 사용자 소유
- **409 Conflict**: 변경할 전화번호가 시스템에 이미 존재
  ```json
  {
    "detail": "변경하려는 전화번호가 이미 시스템에 존재합니다."
  }
  ```
- **422 Unprocessable Entity**: 정규식 미부합

**비즈니스 규칙:**
- 제공된 필드만 업데이트 (PATCH 방식)
- phone 변경 시 기존값과 다를 때만 중복 검사
- category_id 변경 시 사용자 소유권 재검증
- updated_at 자동 갱신

---

#### **[NFR-04] DELETE /contacts/{id} - 연락처 삭제**

**요청:**
```http
DELETE /contacts/1 HTTP/1.1
Host: localhost:8001
Cookie: session_id=<UUID>
```

**응답 (204 No Content):**
```
(빈 응답)
```

**에러 응답:**
- **404 Not Found**: 연락처 없거나 타 사용자 소유

**비즈니스 규칙:**
- 사용자 소유권 검증 필수

---

### 4.4. 모니터링 (Monitoring) API

#### **GET /health - 헬스체크**

**요청:**
```http
GET /health HTTP/1.1
Host: localhost:8001
```

**응답 (200 OK):**
```json
{
  "status": "ok"
}
```

**용도:** 운영 시 서버 정상 상태 확인, 로드 밸런서 헬스 체크

---

## 5. 비기능적 요구사항 (Non-Functional Specs)

### 5.1. 성능 (Performance)

| 요구사항 | 목표값 | 설명 |
|---------|------|------|
| **API 응답 시간** | < 200ms | 평균 응답 시간 (캐시 미포함) |
| **동시 사용자** | 100명 | 예상 동시 활성 사용자 |
| **처리량 (TPS)** | 50 TPS | 초당 최대 거래 건수 |
| **데이터베이스 쿼리** | < 50ms | 개별 쿼리 실행 시간 |

**최적화 전략:**
- SQLAlchemy 쿼리 인덱싱 (username, phone, user_id)
- 연결 풀 관리 (`pool_pre_ping=True`)
- 페이지네이션 강제 (기본 10개, 최대 100개)

---

### 5.2. 보안 (Security)

#### **[NFR-03] 비밀번호 암호화**
- **알고리즘**: Argon2id (NIST 권장)
- **구현**: `passlib` + `argon2-cffi`
- **특징**:
  - GPU 무차별 대입 공격 방어
  - Salt 자동 생성 및 관리
  - 자동 복잡도 조정
- **코드**:
  ```python
  pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
  hashed_pwd = pwd_context.hash(plain_password)
  ```

#### **[NFR-04] 테넌트 격리 (Multi-tenant Isolation)**
- **원칙**: 모든 쿼리에 `user_id` 필터 적용
- **구현**:
  ```python
  # 안전한 패턴:
  db.query(Contact).filter(
    Contact.id == contact_id,
    Contact.user_id == current_user.id  # ← 필수
  ).first()
  ```
- **위반 시 결과**: 401/404 에러 반환 (데이터 노출 차단)

#### **[NFR-05] CORS 설정**
- **허용 출처**:
  - `http://127.0.0.1:5500` (Live Server)
  - `http://localhost:5500`
  - `http://127.0.0.1:8001` (HTTPS 준비)
  - `http://localhost:8001`
- **쿠키 허용**: `allow_credentials=True` (세션 쿠키 공유)
- **메서드**: `["*"]` (GET, POST, PATCH, DELETE 모두 허용)

**프로덕션 준비:**
```python
# 개발 환경 (현재):
allow_origins=["http://127.0.0.1:5500", ...]

# 프로덕션 (예정):
allow_origins=os.getenv("ALLOWED_ORIGINS").split(",")
```

#### **세션 쿠키 보안**
```python
response.set_cookie(
    key="session_id",
    value=db_session.session_id,
    httponly=True,        # XSS 공격 차단 (JS 접근 불가)
    max_age=3600 * 24,    # 24시간
    samesite="lax"        # CSRF 공격 방어
)
```

#### **SQL 인젝션 방어**
- **방식**: SQLAlchemy ORM 사용 (매개변수화된 쿼리)
- **금지**: 문자열 연결 (`f-string` 불사용)
```python
# 안전: ORM 사용
db.query(Contact).filter(Contact.name.contains(search))

# 위험: 직접 쿼리 (사용 금지)
# db.execute(f"SELECT * FROM contacts WHERE name LIKE '%{search}%'")
```

#### **민감 정보 관리**
- **환경 변수**: `.env` 파일에서 로드
  ```python
  DATABASE_URL = os.getenv("DATABASE_URL")
  ```
- **금지 사항**:
  - 소스 코드에 비밀번호/API 키 하드코딩 금지
  - `.env` 파일을 `.gitignore`에 포함
- **Git 보호**: `backend/.env` (추적 제외)

---

### 5.3. 가용성 (Availability)

#### **데이터베이스 헬스 체크**
```python
# Docker Compose healthcheck
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U contact_user -d contact_db"]
  interval: 10s
  timeout: 5s
  retries: 5
```

#### **연결 풀 관리**
```python
# database.py
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True  # 주기적 연결 체크, 끊김 감지
)
```

#### **자동 재시작**
- Docker Compose: `restart_policy: unless-stopped` (기본값)
- 백엔드: `--reload` 옵션 (개발 환경)
- 운영 환경: Kubernetes / Systemd 관리 권장

---

### 5.4. 신뢰성 (Reliability)

#### **데이터 무결성**
- **트랜잭션**: `autocommit=False` (명시적 커밋)
- **외래키 제약**:
  - User → Session, Category, Contact: CASCADE
  - Category → Contact: RESTRICT (연락처 정리 강제)
- **유니크 제약**: phone (시스템 전체)

#### **에러 처리**
- **글로벌 핸들러**: 모든 예외를 규격화된 JSON으로 반환
  ```python
  @app.exception_handler(Exception)
  async def global_exception_handler(request: Request, exc: Exception):
      return JSONResponse(
          status_code=500,
          content={"detail": "서버 내부에서 처리할 수 없는 오류가 발생했습니다."}
      )
  ```
- **로깅**: `print()` (운영 시 ELK Stack 등으로 전환)

#### **무결성 제약 처리**
```python
# categories.py에서 RESTRICT 위반 처리
try:
    crud.delete_category(db, db_category=category)
except IntegrityError:
    db.rollback()
    raise HTTPException(
        status_code=409,
        detail="해당 카테고리에 등록된 연락처가 존재하여 삭제할 수 없습니다."
    )
```

---

### 5.5. 호환성 (Compatibility)

| 항목 | 지원 | 최소 버전 |
|------|------|---------|
| **Python** | 3.11+ | 3.11 |
| **PostgreSQL** | 12+ | 12 |
| **Docker** | 20.10+ | 20.10 |
| **Docker Compose** | 2.0+ | 2.0 |
| **브라우저** | 최신 2개 버전 | Chrome 120+, Firefox 120+, Safari 17+ |

**개발 환경:**
- Windows 10/11
- macOS (Intel/Apple Silicon)
- Linux (Ubuntu 20.04+)

---

### 5.6. 유지보수성 (Maintainability)

#### **코드 구조**
```
backend/
├─ main.py                # 앱 초기화, 라우터 등록, 정적 파일 서빙
├─ database.py            # DB 연결, 세션 관리
├─ models.py              # SQLAlchemy ORM 모델
├─ schemas.py             # Pydantic 입력/출력 스키마
├─ security.py            # 암호화, 인증 가드
├─ crud.py                # 데이터 조작 함수
├─ routers/
│  ├─ auth.py             # 인증 API
│  ├─ contacts.py         # 연락처 API
│  └─ categories.py       # 카테고리 API
├─ Dockerfile             # 컨테이너 빌드
└─ requirements.txt       # 의존성
```

#### **패키지 관리**
- `requirements.txt`로 의존성 고정
- 버전 명시 (예: `fastapi==0.110.0`)

---

## 6. 예외 처리 규칙 (Exception Handling)

### 6.1. HTTP 상태 코드

| 상태 코드 | 상황 | 응답 예시 |
|----------|------|---------|
| **200 OK** | 성공 (로그인, 조회) | `{"message": "로그인에 성공했습니다."}` |
| **201 Created** | 생성 성공 | 생성된 리소스 객체 |
| **204 No Content** | 삭제/수정 성공 | (빈 응답) |
| **400 Bad Request** | 잘못된 요청 | 파라미터 오류 |
| **401 Unauthorized** | 인증 실패 | `{"detail": "인증을 위한 세션 쿠키가 누락되었습니다."}` |
| **404 Not Found** | 리소스 미존재 | `{"detail": "해당 연락처를 찾을 수 없습니다."}` |
| **409 Conflict** | 충돌 (중복, 제약위배) | `{"detail": "이미 시스템에 등록된 전화번호입니다."}` |
| **422 Unprocessable Entity** | 검증 실패 | Pydantic 에러 목록 |
| **500 Internal Server Error** | 서버 에러 | `{"detail": "서버 내부에서 처리할 수 없는 오류가 발생했습니다."}` |

### 6.2. 에러 응답 포맷

**정규 에러 (4xx):**
```json
{
  "detail": "상세한 에러 메시지"
}
```

**검증 에러 (422):**
```json
{
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": ["body", "phone"],
      "msg": "String should match pattern '^010\\d{8}$'",
      "input": "123"
    }
  ]
}
```

**서버 에러 (500):**
```json
{
  "detail": "서버 내부에서 처리할 수 없는 오류가 발생했습니다."
}
```

### 6.3. 예외 처리 매트릭스

| 시나리오 | 원인 | HTTP 코드 | 에러 메시지 |
|---------|------|---------|-----------|
| 회원가입 시 중복 아이디 | username 조회 실패 | 409 | "이미 존재하는 아이디입니다." |
| 로그인 시 아이디/비밀번호 오류 | 사용자 미존재 또는 비밀번호 불일치 | 401 | "아이디 또는 비밀번호가 올바르지 않습니다." |
| 보호된 엔드포인트 접근 시 세션 없음 | 쿠키 누락 또는 만료 | 401 | "인증을 위한 세션 쿠키가 누락되었습니다." |
| 연락처 생성 시 전화번호 중복 | phone 유니크 제약 위배 | 409 | "이미 시스템에 등록된 전화번호입니다." |
| 연락처 생성 시 카테고리 미존재 | category_id 불일치 또는 타 사용자 소유 | 404 | "지정한 카테고리를 찾을 수 없거나 접근 권한이 없습니다." |
| 카테고리 삭제 시 연락처 남아있음 | ForeignKey RESTRICT 위배 | 409 | "해당 카테고리에 등록된 연락처가 존재하여 삭제할 수 없습니다." |
| 데이터 정규식 미부합 | 입력값이 패턴 불일치 | 422 | Pydantic 검증 메시지 |
| 예기치 않은 서버 에러 | DB 연결 실패, 코드 버그 등 | 500 | "서버 내부에서 처리할 수 없는 오류가 발생했습니다." |

### 6.4. 금지 사항

**절대 하면 안 되는 행동 (PROHIBITION):**

1. **비어있는 Catch 블록**
   ```python
   # ❌ 금지
   try:
       something()
   except Exception:
       pass  # 무시하면 안 됨!
   ```

2. **임의 텍스트/객체 반환**
   ```python
   # ❌ 금지
   try:
       contact = get_contact(...)
   except:
       return "Error occurred"  # 규격화되지 않은 텍스트 반환 금지
       return {}               # 빈 객체 반환 금지
       return None             # null 반환 금지
   ```

3. **에러 로그만 남기고 정상 처리**
   ```python
   # ❌ 금지
   try:
       db.commit()
   except IntegrityError as e:
       print(f"Error: {e}")  # 로그만 남기고 계속 진행하면 안 됨
       # 다음 줄 계속 실행 → 클라이언트는 성공으로 생각
   ```

---

## 7. 인수 조건 및 기능 점검 (Acceptance Criteria / Verification)

### 7.1. 개발 체크리스트

#### **개발 완료 시 검증**
- [ ] **코드 스타일 검증**
  ```bash
  # 린트 검사 (필요시 적용)
  npm run lint  # 또는 pylint, flake8
  ```
  
- [ ] **정적 타입 검사**
  ```bash
  npm run build  # TypeScript 체크
  # Python: mypy (필요시)
  ```

- [ ] **단위 테스트 및 통합 테스트**
  ```bash
  npm run test
  # 또는 pytest (백엔드)
  pytest backend/
  ```

- [ ] **로컬 빌드 및 실행**
  ```bash
  # 개발 환경
  python -m uvicorn main:app --reload
  
  # Docker 환경
  docker-compose up -d
  docker-compose logs -f backend
  ```

#### **기능 검증**

**[회원가입 & 로그인]**
- [ ] 회원가입: 신규 사용자 정상 가입
- [ ] 회원가입: 중복 아이디 거부 (409)
- [ ] 회원가입: 공백 아이디 거부 (422)
- [ ] 로그인: 정상 로그인 및 세션 쿠키 발급
- [ ] 로그인: 잘못된 비밀번호 거부 (401)
- [ ] 로그아웃: 세션 삭제 및 쿠키 만료

**[카테고리 관리]**
- [ ] GET /categories: 사용자별 격리 조회
- [ ] POST /categories: 신규 카테고리 생성
- [ ] DELETE /categories: 정상 삭제
- [ ] DELETE /categories: 연락처 있을 시 거부 (409)

**[연락처 관리]**
- [ ] POST /contacts: 정규식 검증 (name, phone, address)
- [ ] POST /contacts: 전화번호 중복 거부 (409)
- [ ] GET /contacts: 사용자별 격리 조회
- [ ] GET /contacts?search=...: 검색 기능
- [ ] GET /contacts: 페이지네이션
- [ ] PATCH /contacts/{id}: 부분 수정
- [ ] DELETE /contacts/{id}: 정상 삭제

**[보안 & 인증]**
- [ ] 로그인하지 않은 사용자는 보호 엔드포인트 접근 불가 (401)
- [ ] 타 사용자 데이터 접근 시도 → 404
- [ ] 세션 쿠키 httponly=True 확인
- [ ] CORS 설정 확인 (Live Server 연동)

**[에러 처리]**
- [ ] 예외 발생 시 규격화된 JSON 응답
- [ ] 500 에러 시 스택 트레이스 노출 금지
- [ ] 모든 에러 로깅 확인

### 7.2. 배포 체크리스트

**Docker 배포 전:**
- [ ] `.env` 파일 설정 (DATABASE_URL, etc.)
- [ ] `.gitignore`에 `.env` 포함 확인
- [ ] `docker-compose.yml` 검토
  - [ ] 포트 충돌 확인 (8001, 5432)
  - [ ] 볼륨 설정 확인
  - [ ] 환경 변수 확인
- [ ] Dockerfile 검토
  - [ ] Python 버전
  - [ ] 의존성 설치
  - [ ] 작업 디렉토리

**배포 실행:**
```bash
# 이미지 빌드 및 컨테이너 실행
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs backend

# 헬스 체크
curl http://localhost:8001/health
```

**배포 후 검증:**
- [ ] 웹 애플리케이션 접근 (http://localhost:8001)
- [ ] API 문서 접근 (http://localhost:8001/docs)
- [ ] 회원가입 & 로그인 테스트
- [ ] 연락처 CRUD 테스트
- [ ] PostgreSQL 데이터 확인
  ```bash
  docker-compose exec postgres psql -U contact_user -d contact_db -c "SELECT * FROM users;"
  ```

### 7.3. 성능 테스트 (권장)

**부하 테스트:**
```bash
# Apache Bench (AB) 또는 wrk 사용
ab -n 1000 -c 100 http://localhost:8001/health

# 또는 Python Locust
pip install locust
locust -f locustfile.py --headless -u 100 -r 10 -t 60s
```

**목표:**
- 평균 응답 시간 < 200ms
- p95 응답 시간 < 500ms
- 에러율 < 1%

---

## 8. 부록 (Appendix)

### 8.1. 데이터베이스 스키마

#### **USERS 테이블**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
```

#### **SESSIONS 테이블**
```sql
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### **CATEGORIES 테이블**
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### **CONTACTS 테이블**
```sql
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(10) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    address VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
);
```

### 8.2. 관련 참고 문서

- **FastAPI 공식 문서**: https://fastapi.tiangolo.com
- **SQLAlchemy 공식 문서**: https://docs.sqlalchemy.org
- **Pydantic 공식 문서**: https://docs.pydantic.dev
- **Docker Compose 공식 문서**: https://docs.docker.com/compose
- **OWASP Top 10**: https://owasp.org/www-project-top-ten

### 8.3. 용어 정의

| 용어 | 정의 |
|------|------|
| **테넌트 격리** | 사용자별로 독립된 데이터 공간 제공 (멀티테넌트) |
| **원자성 (Atomicity)** | 트랜잭션 전체 성공 또는 전체 실패 (부분 반영 불가) |
| **CRUD** | Create(생성), Read(조회), Update(수정), Delete(삭제) |
| **정규식 (Regex)** | 텍스트 패턴 매칭 규칙 (예: `^010\d{8}$`) |
| **유니크 제약 (Unique)** | 데이터베이스 컬럼의 값이 유일해야 함 |
| **외래키 (Foreign Key)** | 다른 테이블의 기본키를 참조하는 제약 |
| **CASCADE** | 부모 삭제 시 자식도 자동 삭제 |
| **RESTRICT** | 자식이 존재하면 부모 삭제 불가 |

---

## 버전 히스토리

| 버전 | 작성일 | 변경 사항 |
|------|--------|---------|
| 2.1 | 2026-07-14 | 최초 작성 |

---

**문서 작성**: Claude Code  
**최종 검토**: -  
**승인**: -

