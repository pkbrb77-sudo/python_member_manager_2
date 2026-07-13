# 연락처 관리 웹 애플리케이션

> Python 기반의 연락처 관리 시스템의 기술 요구사항 정의 및 구현 프로젝트

## 📋 프로젝트 개요

이 프로젝트는 두 가지 목표를 담고 있습니다:

1. **TRD(기술 요구사항 정의서) 작성**: 연락처 관리 프로그램의 상세한 기술 설계 문서 작성
2. **웹 애플리케이션 구현**: FastAPI 백엔드 + PostgreSQL 데이터베이스 + 프론트엔드로 구성된 완전한 웹 시스템 구현

### 핵심 학습 목표

- CRUD 패턴(Create, Read, Update, Delete) 이해
- 데이터 구조 설계 및 모델링
- 데이터 영속화 및 데이터베이스 관리
- 입력 검증 및 예외 처리
- REST API 설계 및 구현
- 컨테이너 기반 배포

---

## 📁 프로젝트 구조

```
trd수정/
├── README.md (이 파일)
├── CLAUDE.md (프로젝트 안내 및 규칙)
├── TRD_회원관리프로그램_최종.md (기술 요구사항 정의서)
└── 재미나이로만들어봤/
    └── contact.app/ (실제 구현)
        ├── backend/ (FastAPI 백엔드)
        │   ├── crud.py (데이터베이스 CRUD 작업)
        │   ├── main.py (메인 애플리케이션)
        │   ├── models.py (데이터 모델)
        │   ├── schemas.py (API 요청/응답 스키마)
        │   ├── database.py (데이터베이스 설정)
        │   ├── Dockerfile
        │   └── requirements.txt
        ├── frontend/ (프론트엔드)
        ├── docker-compose.yml
        └── DOCKER_README.md (Docker 실행 가이드)
```

---

## 🚀 빠른 시작

### 필수 요구사항

- Docker 20.10 이상
- Docker Compose 2.0 이상

### 설치 및 실행

```bash
# 1. contact.app 디렉토리로 이동
cd 재미나이로만들어봤/contact.app

# 2. Docker Compose로 실행
docker-compose up -d

# 3. 애플리케이션 접속
# - 웹 애플리케이션: http://localhost:8001/
# - API 문서: http://localhost:8001/docs
```

자세한 Docker 실행 방법은 [DOCKER_README.md](재미나이로만들어봤/contact.app/DOCKER_README.md)를 참조하세요.

---

## 📚 핵심 문서

### 1. [TRD_회원관리프로그램_최종.md](TRD_회원관리프로그램_최종.md)

기술 요구사항 정의서로 다음 내용을 포함합니다:

- **목적 및 배경**: 프로젝트 목표와 실무 연계 방안
- **기술 스택**: Python, FastAPI, PostgreSQL, Docker 등
- **시스템 아키텍처**: 3계층 구조(Presentation, Business Logic, Data)
- **기능 명세**: API 엔드포인트, 데이터 모델, 요청/응답 형식
- **비기능 요구사항**: 성능, 보안, 확장성 관련 사항
- **예외 처리**: 에러 코드 및 처리 전략
- **인수 조건**: 완료 기준 및 검증 방법

### 2. [CLAUDE.md](CLAUDE.md)

프로젝트 개발 규칙 및 안내:

- 코드 스타일 및 일관성
- 아키텍처 준수 규칙
- 금지 사항 (보안, 에러 핸들링, 스키마 변경 등)
- 검증 명령어

---

## 🏗️ 시스템 아키텍처

### 3계층 구조

```
┌─────────────────────────────────────┐
│   프론트엔드 (Frontend)              │
│   - HTML/CSS/JavaScript             │
└──────────────────┬──────────────────┘
                   │ HTTP/REST API
┌──────────────────▼──────────────────┐
│   백엔드 (FastAPI)                  │
│   - 라우팅 및 요청 처리             │
│   - 비즈니스 로직                   │
│   - 데이터 검증                     │
└──────────────────┬──────────────────┘
                   │ SQL
┌──────────────────▼──────────────────┐
│   데이터베이스 (PostgreSQL)         │
│   - 데이터 저장 및 검색             │
└─────────────────────────────────────┘
```

### 주요 엔티티

- **Contact**: 연락처 정보 (이름, 전화번호, 이메일, 주소 등)
- **User**: 사용자 계정 정보 (선택사항)

---

## 📦 주요 기술 스택

| 계층 | 기술 | 버전 |
|------|------|------|
| **백엔드** | FastAPI | 최신 |
| **데이터베이스** | PostgreSQL | 15+ |
| **프론트엔드** | HTML/CSS/JavaScript | - |
| **배포** | Docker/Docker Compose | 20.10+ / 2.0+ |

---

## 🔧 개발 가이드

### 코드 스타일 검증

```bash
cd backend

# 린트 검사
npm run lint

# 포맷팅 확인
npm run format

# 빌드 및 타입 체크
npm run build

# 테스트 실행
npm run test
```

### 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
docker-compose exec backend python -c \
  "from database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### API 문서

애플리케이션 실행 후 다음 주소에서 Swagger UI로 API 문서를 확인할 수 있습니다:

- http://localhost:8001/docs (Swagger UI)
- http://localhost:8001/openapi.json (OpenAPI 스키마)

---

## ⚠️ 주요 제약사항 및 규칙

### 금지 사항

1. **보안**: 민감한 정보(비밀번호, 키)를 코드에 하드코딩하지 말 것 (`.env` 사용)
2. **에러 처리**: catch 블록을 비우거나 방치하지 말 것
3. **API 응답**: 정의된 에러 응답 형식을 벗어나지 말 것
4. **Git**: 검증 없이 메인 브랜치에 직접 푸시하지 말 것

자세한 규칙은 [CLAUDE.md](CLAUDE.md)를 참조하세요.

---

## 🐛 트러블슈팅

### 포트 충돌

포트 8001 또는 5432가 이미 사용 중인 경우:

```yaml
# docker-compose.yml에서 포트 변경
ports:
  - "8002:8000"  # 8002로 변경
```

### 데이터베이스 연결 실패

```bash
# 데이터베이스 상태 확인
docker-compose exec postgres pg_isready -U contact_user

# PostgreSQL 로그 확인
docker-compose logs postgres
```

---

## 📞 문의 및 지원

- **프로젝트 규칙**: [CLAUDE.md](CLAUDE.md) 참조
- **기술 설계**: [TRD_회원관리프로그램_최종.md](TRD_회원관리프로그램_최종.md) 참조
- **Docker 실행**: [DOCKER_README.md](재미나이로만들어봤/contact.app/DOCKER_README.md) 참조

---

## 📄 라이센스

이 프로젝트는 교육 목적의 과제 프로젝트입니다.

---

**마지막 수정**: 2026-07-13
