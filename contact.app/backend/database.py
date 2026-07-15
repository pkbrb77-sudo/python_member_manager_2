import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. 데이터베이스 연결 URL 설정
# 환경 변수에서 DATABASE_URL을 읽거나, 기본값으로 SQLite 사용
DATABASE_URL = os.getenv("DATABASE_URL")

# 만약 환경 변수가 설정되지 않았으면 SQLite 사용 (개발 환경용)
if not DATABASE_URL:
    db_path = os.path.join(os.path.dirname(__file__), "contact_app.db")
    DATABASE_URL = f"sqlite:///{db_path}"

# 만약 SQLite를 사용하는 경우, 스레드 간 충돌 방지를 위한 설정을 추가합니다.
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

# 2. SQLAlchemy Engine 생성
# 전 계층 한글 입출력 및 연결 풀(Connection Pool) 최적화를 관리합니다.
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True  # NFR-01 준수: 주기적으로 DB 연결을 체크하여 끊김 현상 방지
)

# 3. 데이터베이스 세션 팩토리 설정
# autocommit=False: 명시적으로 db.commit()을 호출할 때만 반영되도록 원자성 보장
# autoflush=False: 쿼리 실행 전 불필요하게 데이터가 먼저 밀려 들어가는 현상 제어
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# 4. ORM 매핑 모델용 베이스 클래스 선언
Base = declarative_base()

# 5. 의존성 주입(Dependency Injection)을 위한 세션 공급 함수
# FastAPI 엔드포인트(Routers)에서 DB 연결이 필요할 때 Depends(get_db) 형태로 안전하게 사용됩니다.
def get_db():
    """
    HTTP 요청이 들어올 때마다 독립된 DB 세션을 생성하고, 
    처리가 끝나면(성공/실패 관계없이) 세션을 자동으로 닫아줍니다(Context Manager).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # 연결 누수(Connection Leak) 방지