from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import get_db
import models

# 1. 암호화 컨텍스트 설정 (NFR-03 준수)
# NIST에서 권장하고 GPU 무차별 대입 공격에 강력한 Argon2id 알고리즘을 사용합니다.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ==========================================
# [비밀번호 암호화 및 검증 기능]
# ==========================================

def get_password_hash(password: str) -> str:
    """
    평문 패스워드를 받아 Argon2 해시 텍스트로 변환합니다.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    타이밍 공격(Timing Attack)을 방지하는 안전한 방식으로 
    평문 패스워드와 데이터베이스의 해시 비밀번호를 비교합니다.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==========================================
# [쿠키 세션 인증 가드 (의존성 주입 전용)]
# ==========================================

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    """
    [NFR-04 / TR-006 준수] 
    HTTP 요청의 쿠키(Cookie) 헤더에서 session_id를 추출하여 사용자를 검증합니다.
    
    - 세션이 없거나 만료된 경우: 401 Unauthorized 반환
    - 유효한 세션인 경우: 해당 User 객체를 반환하여 라우터에 주입
    """
    # 1. 브라우저 쿠키 영역에서 'session_id' 키값을 가진 토큰을 꺼냅니다.
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증을 위한 세션 쿠키가 누락되었습니다."
        )

    # 2. SESSIONS 테이블을 조회하여 세션 토큰이 존재하는지 검증합니다.
    db_session = (
        db.query(models.Session)
        .filter(models.Session.session_id == session_id)
        .first()
    )
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 세션입니다."
        )

    # 3. 세션과 연결된 USERS 정보를 가져옵니다.
    current_user = db_session.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="해당 세션에 매핑된 사용자를 찾을 수 없습니다."
        )

    # 인증 통과: 주소록/카테고리 라우터에 로그인한 유저 정보 객체를 리턴
    return current_user