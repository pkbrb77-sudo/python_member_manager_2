from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from security import get_current_user
from sqlalchemy.exc import IntegrityError
import schemas
import crud
import models

router = APIRouter(prefix="/categories", tags=["Categories"])

# ==========================================
# 1. 카테고리 생성 API (POST /categories)
# ==========================================
@router.post(
    "", 
    response_model=schemas.CategoryResponse, 
    status_code=status.HTTP_201_CREATED
)
def create_new_category(
    category_in: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    [NFR-04 준수] 신규 카테고리 생성 엔드포인트
    - 입력값 공백 여부는 Pydantic 스키마(schemas.py) 수준에서 1차 차단
    - 현재 로그인한 사용자의 소유로 카테고리를 바인딩하여 생성
    """
    return crud.create_category(db, category_in=category_in, user_id=current_user.id)


# ==========================================
# 2. 카테고리 목록 조회 API (GET /categories)
# ==========================================
@router.get("", response_model=list[schemas.CategoryResponse])
def read_categories_list(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    [NFR-04 준수] 현재 로그인한 사용자의 카테고리 목록 격리 조회
    - 가입 시 자동 생성된 기본 3종("가족", "친구", "기타") 및 추가 생성한 목록만 반환
    - 타인의 카테고리 목록은 데이터베이스 쿼리 레벨에서 철저히 격리되어 노출되지 않음
    """
    return crud.get_categories_by_user(db, user_id=current_user.id)


# ==========================================
# 3. 카테고리 삭제 API (DELETE /categories/{id})
# ==========================================
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_info(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    [TR-004 / NFR-04 준수] 카테고리 삭제 엔드포인트
    - 본인 소유의 카테고리만 삭제 요청 가능 (타인 자원 요청 시 404 차단)
    - 무결성 가드: 해당 카테고리에 소속된 연락처(Contacts)가 1개라도 남아있는 경우,
      데이터베이스의 RESTRICT 외래키 제약조건에 의해 에러가 유도되며, 409 Conflict 예외를 반환합니다.
    """
    # 1. 삭제 대상 카테고리가 존재하고 현재 유저의 소유가 맞는지 검증 (격리 가드)
    category = crud.get_category_by_id_and_user(db, category_id=category_id, user_id=current_user.id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 카테고리를 찾을 수 없거나 접근 권한이 없습니다."
        )

    # 2. 삭제 트랜잭션 실행 및 무결성 예외 처리 (TR-004 대응)
    try:
        crud.delete_category(db, db_category=category)
    except IntegrityError:
        # models.py의 ForeignKey(..., ondelete="RESTRICT") 제약조건 위배 시 대입됨
        db.rollback() # 실패한 트랜잭션 롤백 처리
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="해당 카테고리에 등록된 연락처가 존재하여 삭제할 수 없습니다. 연락처를 먼저 정리하세요."
        )
    
    return None