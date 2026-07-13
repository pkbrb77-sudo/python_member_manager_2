from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
import schemas
import crud
import security
import models

router = APIRouter(prefix="/auth")

# ==========================================
# 1. 회원가입 API (POST /auth/signup)
# ==========================================
@router.post(
    "/signup", 
    response_model=schemas.UserResponse, 
    status_code=status.HTTP_201_CREATED
)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    [TR-005 / TR-011 준수] 신규 회원가입 엔드포인트
    - 중복된 아이디 검사 (존재 시 409 Conflict)
    - 비밀번호 Argon2 단방향 안전 해싱 암호화
    - 가입 즉시 '가족', '친구', '기타' 기본 카테고리 3종 자동 생성 및 바인딩
    """
    # 1. 아이디 중복 체크
    existing_user = crud.get_user_by_username(db, username=user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 존재하는 아이디입니다."
        )
    
    # 2. 패스워드 암호화 (Argon2 해싱 적용)
    hashed_pwd = security.get_password_hash(user_in.password)
    
    # 3. 유저 생성 및 기본 카테고리 원자적 생성 실행
    new_user = crud.create_user_with_defaults(db, user_in=user_in, hashed_password=hashed_pwd)
    return new_user


# ==========================================
# 2. 로그인 API (POST /auth/login)
# ==========================================
@router.post("/login", status_code=status.HTTP_200_OK)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    [TR-006 / NFR-04 준수] 로그인 및 세션 쿠키 발급 엔드포인트
    - 폼 데이터(x-www-form-urlencoded) 형식으로 아이디/비밀번호 수신 (app.js 규격 부합)
    - 비밀번호 검증 실패 시 401 Unauthorized 반환
    - 검증 성공 시 UUID 기반의 세션 생성 후 브라우저 쿠키(session_id)에 주입
    """
    # 1. 유저 존재 여부 확인
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다."
        )
    
    # 2. 패스워드 타이밍 공격 방어 검증 (Plain vs Hash)
    if not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다."
        )
    
    # 3. DB 세션 레코드 생성 및 UUID 토큰 발급
    db_session = crud.create_session(db, user_id=user.id)
    
    # 4. 응답 헤더에 세션 쿠키 설정 (Set-Cookie)
    # httponly=True 설정으로 자바스크립트를 통한 XSS 쿠키 탈취 공격을 차단합니다.
    response.set_cookie(
        key="session_id",
        value=db_session.session_id,
        httponly=True,
        max_age=3600 * 24, # 24시간 유지
        samesite="lax"     # CSRF 공격 방어 설정
    )
    
    return {"message": "로그인에 성공했습니다."}


# ==========================================
# 3. 로그아웃 API (POST /auth/logout)
# ==========================================
@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user) # 로그인 검증 가드 작동
):
    """
    [TR-006 준수] 로그아웃 엔드포인트
    - 요청 쿠키에서 session_id 획득 후 DB 세션 테이블에서 완전 제거 (서버 측 세션 무효화)
    - 브라우저 쿠키의 세션 토큰 강제 삭제(만료) 처리
    """
    session_id = request.cookies.get("session_id")
    if session_id:
        # DB에서 세션 레코드 영구 삭제
        crud.delete_session(db, session_id=session_id)
    
    # 브라우저 쿠키 값 비우기 및 만료 처리
    response.delete_cookie(key="session_id", httponly=True, samesite="lax")
    return {"message": "로그아웃이 완료되었습니다."}