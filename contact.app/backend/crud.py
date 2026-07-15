import uuid
from sqlalchemy.orm import Session
from sqlalchemy import or_
import models
import schemas

# ==========================================
# 1. AUTH / USER / SESSION 도메인 CRUD
# ==========================================

def get_user_by_username(db: Session, username: str) -> models.User:
    """아이디(username)로 특정 유저 정보 조회"""
    return db.query(models.User).filter(models.User.username == username).first()


def create_user_with_defaults(db: Session, user_in: schemas.UserCreate, hashed_password: str) -> models.User:
    """
    [TR-011 준수] 신규 회원을 생성하고, 
    원자적(Atomic) 트랜잭션으로 기본 3종 카테고리("가족", "친구", "기타")를 자동 생성합니다.
    """
    # 1. 사용자 엔티티 생성 및 추가
    db_user = models.User(
        username=user_in.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.flush()  # DB에 유저 정보를 임시 반영하여 생성된 고유 ID(db_user.id)를 획득합니다.

    # 2. 비즈니스 규칙: 가입 즉시 기본 카테고리 3종 자동 바인딩
    default_categories = ["가족", "친구", "기타"]
    for cat_name in default_categories:
        new_cat = models.Category(
            name=cat_name,
            user_id=db_user.id
        )
        db.add(new_cat)

    # 3. 모든 작업이 성공하면 일괄 커밋
    db.commit()
    db.refresh(db_user)
    return db_user


def create_session(db: Session, user_id: int) -> models.Session:
    """로그인 성공 시 무작위 UUID 토큰 기반의 신규 세션을 발급 및 저장합니다."""
    session_token = str(uuid.uuid4())
    db_session = models.Session(
        session_id=session_token,
        user_id=user_id
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def delete_session(db: Session, session_id: str) -> bool:
    """[TR-006 준수] 로그아웃 요청 시 세션 테이블에서 해당 토큰을 영구 제거합니다."""
    db_session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if db_session:
        db.delete(db_session)
        db.commit()
        return True
    return False


# ==========================================
# 2. CATEGORY 도메인 CRUD (테넌트 격리형)
# ==========================================

def get_categories_by_user(db: Session, user_id: int) -> list[models.Category]:
    """[NFR-04 준수] 현재 로그인한 사용자가 소유한 카테고리 목록만 격리 조회"""
    return db.query(models.Category).filter(models.Category.user_id == user_id).all()


def get_category_by_id_and_user(db: Session, category_id: int, user_id: int) -> models.Category:
    """특정 카테고리를 소유자 ID 기반으로 안전하게 1건 조회 (타인 조회 불가 가드)"""
    return db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == user_id
    ).first()


def create_category(db: Session, category_in: schemas.CategoryCreate, user_id: int) -> models.Category:
    """새로운 카테고리를 생성합니다."""
    db_cat = models.Category(
        name=category_in.name,
        user_id=user_id
    )
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat


def delete_category(db: Session, db_category: models.Category) -> None:
    """
    카테고리를 삭제합니다. 
    (※ 만약 해당 카테고리를 참조하는 연락처가 있다면 models.py의 RESTRICT 설정에 의해 
       SQLAlchemy 및 DB 엔진이 자동으로 409 Conflict 계열 무결성 예외를 던집니다.)
    """
    db.delete(db_category)
    db.commit()


# ==========================================
# 3. CONTACT 도메인 CRUD (테넌트 격리 및 데이터 제약형)
# ==========================================

def get_contact_by_phone(db: Session, phone: str) -> models.Contact:
    """시스템 전체에서 휴대전화 번호 중복 검사용 조회"""
    return db.query(models.Contact).filter(models.Contact.phone == phone).first()


def get_contacts_by_user(db: Session, user_id: int, search: str = None, page: int = 1, limit: int = 10) -> list[models.Contact]:
    """
    [NFR-04 준수] 사용자의 연락처 목록을 조회합니다. 
    이름/연락처 검색 파라미터 및 페이지네이션(offset, limit)을 완벽히 지원합니다.
    """
    skip = (page - 1) * limit
    query = db.query(models.Contact).filter(models.Contact.user_id == user_id)
    
    # 검색어 조건이 존재할 때 (이름 혹은 전화번호에 매칭)
    if search:
        query = query.filter(
            or_(
                models.Contact.name.contains(search),
                models.Contact.phone.contains(search)
            )
        )
    
    return query.order_by(models.Contact.id.desc()).offset(skip).limit(limit).all()


def get_contact_by_id_and_user(db: Session, contact_id: int, user_id: int) -> models.Contact:
    """사용자가 소유한 특정 연락처를 안전하게 조회합니다. (ID 도용 차단 가드)"""
    return db.query(models.Contact).filter(
        models.Contact.id == contact_id,
        models.Contact.user_id == user_id
    ).first()


def create_contact(db: Session, contact_in: schemas.ContactCreate, user_id: int) -> models.Contact:
    """신규 연락처 생성 데이터베이스 반영"""
    db_contact = models.Contact(
        name=contact_in.name,
        phone=contact_in.phone,
        address=contact_in.address,
        category_id=contact_in.category_id,
        user_id=user_id
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def update_contact(db: Session, db_contact: models.Contact, contact_in: schemas.ContactUpdate) -> models.Contact:
    """연락처 부분 수정(PATCH) 처리"""
    if contact_in.name is not None:
        db_contact.name = contact_in.name
    if contact_in.phone is not None:
        db_contact.phone = contact_in.phone
    if contact_in.address is not None:
        db_contact.address = contact_in.address
    if contact_in.category_id is not None:
        db_contact.category_id = contact_in.category_id

    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, db_contact: models.Contact) -> None:
    """연락처 삭제"""
    db.delete(db_contact)
    db.commit()