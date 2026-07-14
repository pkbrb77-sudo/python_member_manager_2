from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from security import get_current_user
import schemas
import crud
import models

router = APIRouter(prefix="/contacts", tags=["Contacts"])

# ==========================================
# 1. 연락처 생성 API (POST /contacts)
# ==========================================
@router.post(
    "", 
    response_model=schemas.ContactResponse, 
    status_code=status.HTTP_201_CREATED
)
def create_new_contact(
    contact_in: schemas.ContactCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # 인증 및 테넌트 격리 가드
):
    """
    [TR-008 ~ TR-010 / NFR-04 준수] 신규 연락처 등록 엔드포인트
    - Pydantic(schemas.py)에 의해 이름(한글1~5자), 번호(010으로 시작하는 11자리 숫자), 주소('시' 종결)가 1차 자동 검증됨
    - 시스템 전체에서 휴대전화 번호 중복 여부 확인 (중복 시 409 Conflict)
    - 요청자가 소유하지 않은 카테고리 ID 지정 시 생성 차단 (404 Not Found)
    """
    # 1. 시스템 전체 전화번호 중복 검증
    existing_contact = crud.get_contact_by_phone(db, phone=contact_in.phone)
    if existing_contact:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 시스템에 등록된 전화번호입니다."
        )

    # 2. 지정한 카테고리가 현재 로그인한 유저의 소유가 맞는지 검증 (소유권 하이재킹 방어)
    category = crud.get_category_by_id_and_user(
        db, category_id=contact_in.category_id, user_id=current_user.id
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="지정한 카테고리를 찾을 수 없거나 접근 권한이 없습니다."
        )

    # 3. 연락처 생성 및 저장
    return crud.create_contact(db, contact_in=contact_in, user_id=current_user.id)


# ==========================================
# 2. 연락처 목록 조회 API (GET /contacts)
# ==========================================
@router.get("", response_model=list[schemas.ContactResponse])
def read_contacts_list(
    search: str = Query(None, description="이름 또는 전화번호 검색어"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    limit: int = Query(10, ge=1, le=100, description="페이지당 노출 개수"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    [NFR-04 준수] 현재 로그인한 사용자의 연락처 목록 격리 조회
    - 다른 사용자의 주소록 데이터는 절대 노출되지 않음
    - 이름 또는 전화번호를 통한 부분 일치 키워드 검색 지원
    - 안전한 페이지네이션(기본값 1페이지, 10개씩) 처리
    """
    return crud.get_contacts_by_user(
        db, user_id=current_user.id, search=search, page=page, limit=limit
    )


# ==========================================
# 3. 연락처 상세 조회 API (GET /contacts/{id})
# ==========================================
@router.get("/{contact_id}", response_model=schemas.ContactResponse)
def read_contact_detail(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    [NFR-04 준수] 연락처 단건 상세 조회
    - 타인의 연락처 ID를 억지로 대입하여 요청하더라도 404 Not Found를 반환하여 데이터 격리 보장
    """
    contact = crud.get_contact_by_id_and_user(db, contact_id=contact_id, user_id=current_user.id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 연락처를 찾을 수 없거나 접근 권한이 없습니다."
        )
    return contact


# ==========================================
# 4. 연락처 수정 API (PATCH /contacts/{id})
# ==========================================
@router.patch("/{contact_id}", response_model=schemas.ContactResponse)
def update_contact_info(
    contact_id: int,
    contact_in: schemas.ContactUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    [NFR-04 준수] 연락처 정보 부분 수정 (PATCH 방식)
    - 본인 소유의 데이터만 수정 가능
    - 새로운 카테고리 ID(`category_id`)로 변경 요청 시, 본인 소유의 카테고리인지 재검증
    - 전화번호 변경 시 시스템 내 중복 여부 체크
    """
    # 1. 수정 타겟 연락처 소유권 검증
    db_contact = crud.get_contact_by_id_and_user(db, contact_id=contact_id, user_id=current_user.id)
    if not db_contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 연락처를 찾을 수 없거나 접근 권한이 없습니다."
        )

    # 2. 번호 수정 요청이 들어온 경우 중복 검증 (내 기존 번호와 다를 때만 체크)
    if contact_in.phone and contact_in.phone != db_contact.phone:
        existing_contact = crud.get_contact_by_phone(db, phone=contact_in.phone)
        if existing_contact:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="변경하려는 전화번호가 이미 시스템에 존재합니다."
            )

    # 3. 소속 카테고리 변경 요청이 들어온 경우 소유권 검증
    if contact_in.category_id:
        category = crud.get_category_by_id_and_user(
            db, category_id=contact_in.category_id, user_id=current_user.id
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="변경하려는 카테고리를 찾을 수 없거나 접근 권한이 없습니다."
            )

    # 4. 최종 데이터 업데이트 실행
    return crud.update_contact(db, db_contact=db_contact, contact_in=contact_in)


# ==========================================
# 5. 연락처 삭제 API (DELETE /contacts/{id})
# ==========================================
@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_info(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    [NFR-04 준수] 연락처 삭제 엔드포인트
    - 본인 소유의 데이터만 삭제 처리가 이뤄집니다.
    """
    db_contact = crud.get_contact_by_id_and_user(db, contact_id=contact_id, user_id=current_user.id)
    if not db_contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 연락처를 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    crud.delete_contact(db, db_contact=db_contact)
    return None