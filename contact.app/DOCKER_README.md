# Docker를 사용한 연락처 관리 시스템 실행 가이드

## 개요
이 프로젝트는 Docker Compose를 사용하여 PostgreSQL 데이터베이스와 FastAPI 백엔드를 컨테이너로 관리합니다.

## 필수 설치 사항
- **Docker** (버전 20.10 이상)
- **Docker Compose** (버전 2.0 이상)

## 빠른 시작

### 1. Docker Compose로 프로젝트 실행

```bash
# contact.app 디렉토리로 이동
cd contact.app

# Docker 이미지 빌드 및 컨테이너 실행
docker-compose up -d
```

### 2. 초기 데이터베이스 설정 (옵션)

```bash
# 데이터베이스 마이그레이션 (필요시)
docker-compose exec backend python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 3. 애플리케이션 접속

- **웹 애플리케이션**: http://localhost:8001/
- **백엔드 API 문서**: http://localhost:8001/docs
- **데이터베이스**: localhost:5432 (PostgreSQL)

## 주요 컨테이너 정보

### PostgreSQL (contact_app_db)
- **이미지**: postgres:15-alpine
- **컨테이너명**: contact_app_db
- **사용자명**: contact_user
- **비밀번호**: contact_pass
- **데이터베이스명**: contact_db
- **포트**: 5432 (외부 접속)
- **데이터 저장소**: postgres_data (볼륨)

### FastAPI 백엔드 (contact_app_backend)
- **이미지**: contact.app/backend (로컬 빌드)
- **컨테이너명**: contact_app_backend
- **포트**: 8001 (외부 접속, 내부 8000)
- **환경변수**: 
  - DATABASE_URL: postgresql://contact_user:contact_pass@postgres:5432/contact_db
  - APP_ENV: development

## 자주 사용하는 명령어

### 컨테이너 상태 확인
```bash
docker-compose ps
```

### 로그 확인
```bash
# 모든 서비스 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs postgres

# 실시간 로그 (tail -f)
docker-compose logs -f backend
```

### 컨테이너 재시작
```bash
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart backend
```

### 컨테이너 중지
```bash
docker-compose down
```

### 컨테이너 중지 및 데이터 삭제
```bash
docker-compose down -v
```

### 컨테이너 내부 명령 실행
```bash
# 백엔드 컨테이너에서 Python 스크립트 실행
docker-compose exec backend python script.py

# PostgreSQL에 직접 접속
docker-compose exec postgres psql -U contact_user -d contact_db
```

## 데이터 보관

### 데이터 지속성
- PostgreSQL 데이터는 `postgres_data` 볼륨에 저장됩니다
- `docker-compose down` 명령으로 컨테이너를 중지해도 데이터는 유지됩니다
- `docker-compose down -v` 명령으로 데이터를 완전히 삭제할 수 있습니다

### 데이터베이스 백업
```bash
# PostgreSQL 데이터베이스 백업
docker-compose exec postgres pg_dump -U contact_user contact_db > backup.sql

# 백업 복원
docker-compose exec -T postgres psql -U contact_user contact_db < backup.sql
```

## 개발 모드

### 핫 리로드 (자동 재시작)
docker-compose.yml에서 `--reload` 옵션이 활성화되어 있으므로, 백엔드 코드 변경 시 자동으로 재시작됩니다.

### 로컬 개발용 SQLite 사용
```bash
# backend/.env 파일 수정
DATABASE_URL=sqlite:///./contact_app.db
```

## 트러블슈팅

### 포트 충돌
이미 포트 8001이나 5432가 사용 중인 경우:

```yaml
# docker-compose.yml에서 포트 변경
ports:
  - "8002:8000"  # 8002로 변경
  - "5433:5432"  # 5433으로 변경
```

### 데이터베이스 연결 실패
```bash
# 데이터베이스 상태 확인
docker-compose exec postgres pg_isready -U contact_user

# PostgreSQL 로그 확인
docker-compose logs postgres
```

### 백엔드 오류
```bash
# 백엔드 로그 확인
docker-compose logs -f backend

# 컨테이너 재빌드
docker-compose build --no-cache backend
```

## 프로덕션 배포 시 주의사항

현재 설정은 개발 환경용입니다. 프로덕션 배포 시에는:

1. **보안 설정 변경**
   - `.env` 파일의 비밀번호 변경
   - PostgreSQL 비밀번호 강화
   - JWT 시크릿 키 설정

2. **성능 최적화**
   - `--reload` 옵션 제거
   - 연결 풀 설정 조정
   - 캐싱 전략 수립

3. **모니터링**
   - 로그 수집 (ELK Stack, Splunk 등)
   - 성능 모니터링 (Prometheus, Grafana 등)
   - 헬스체크 설정

## 추가 정보

### 데이터베이스 접속 정보
- **호스트**: postgres (docker 내부) 또는 localhost (외부)
- **포트**: 5432
- **사용자**: contact_user
- **비밀번호**: contact_pass
- **데이터베이스**: contact_db

### 백엔드 접속 정보
- **주소**: http://localhost:8001
- **API 문서**: http://localhost:8001/docs (Swagger UI)
- **API 스키마**: http://localhost:8001/openapi.json

### 네트워크
- 모든 서비스는 `contact_network` 브릿지 네트워크에 연결되어 있습니다
- 컨테이너 간 통신은 서비스명으로 가능합니다 (예: `postgres:5432`)
