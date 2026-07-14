import os
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 데이터베이스 초기화 및 라우터 불러오기
from database import engine, Base
from routers.auth import router as auth_router 
from routers.contacts import router as contacts_router
from routers.categories import router as categories_router

# 1. 시스템 부동 시 데이터베이스 테이블 자동 생성 (TR-001 준수)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f" 데이터베이스 테이블 생성 중 오류 발생: {e}")

app = FastAPI(
    title="연락처 관리 웹 서비스",
    description="기술 요구사항 정의서(TRD) 표준 규격을 준수하는 풀스택 연락처 관리 시스템",
    version="2.1"
)

# CORS 미들웨어 설정 (필요 시 확장 가능)
app.add_middleware(
    CORSMiddleware,
    # 기존 ["*"] 대신 Live Server 주소를 정확히 적어줍니다.
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:8001", "http://localhost:8001"],
    allow_credentials=True,  # 로그인 세션 쿠키 공유를 위해 True 필수
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 글로벌 예외 핸들러 (NFR-01 및 예외 처리 매트릭스 500 에러 준수)
# 시스템 런타임 에러가 발생해도 Traceback을 숨기고 규격화된 JSON을 리턴하여 크래시를 방지합니다.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 실제 서버 로그에는 에러 기록
    print(f" [글로벌 에러 발생] 경로: {request.url.path} | 내용: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "서버 내부에서 처리할 수 없는 오류가 발생했습니다."},
        headers={"Content-Type": "application/json; charset=utf-8"} # NFR-05 준수
    )

# 3. 백엔드 비즈니스 로직 라우터 등록
app.include_router(auth_router)
app.include_router(contacts_router)
app.include_router(categories_router)

# 4. 프론트엔드 정적 파일(SPA 구조) 서빙 설정
# main.py 파일 위치 기준으로 상위 폴더의 frontend 디렉토리 경로를 계산합니다.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# 헬스체크 엔드포인트 (운영 모니터링용)
@app.get("/health", tags=["Monitoring"])
def health_check():
    return {"status": "ok"}

# 사용자가 루트(/) 브라우저 주소로 접근했을 때 index.html을 강제로 리턴합니다.
@app.get("/", include_in_schema=False)
async def read_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        status_code=404, 
        content={"detail": "frontend/index.html 파일을 찾을 수 없습니다. 경로를 확인하세요."}
    )

# styles.css, app.js 등 나머지 정적 자원들을 마운트합니다.
# 이 설정 덕분에 HTML 내부에서 <link href="styles.css"> 나 <script src="app.js">로 바로 불러올 수 있습니다.
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    print(f"⚠️ 경고: 프론트엔드 폴더가 존재하지 않습니다. 경로를 확인하세요: {FRONTEND_DIR}")