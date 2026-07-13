from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

# ==========================================
# 1. AUTH (사용자 인증 및 세션) 도메인 스키마
# ==========================================

class UserCreate(BaseModel):
    """회원가입 요청 DTO (TR-005 공백 차단 반영)"""
    username: str = Field(..., min_length=1, max_length=50, description="로그인 ID")
    password: str = Field(..., min_length=1, description="평문 패스워드")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        # 앞뒤 공백 제거 후 빈 문자열이거나 공백만 있는 경우 에러 처리
        stripped = v.strip()
        if not stripped:
            raise ValueError("아이디는 공백 문자로만 구성될 수 없습니다.")
        return stripped

class UserLogin(BaseModel):
    """로그인 요청 DTO"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class UserResponse(BaseModel):
    """사용자 정보 응답 DTO"""
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# 2. CATEGORY (카테고리 분류) 도메인 스키마
# ==========================================

class CategoryCreate(BaseModel):
    """카테고리 생성 요청 DTO"""
    name: str = Field(..., min_length=1, max_length=50, description="카테고리 이름")

    @field_validator('name')
    @classmethod
    def validate_category_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("카테고리 이름은 공백일 수 없습니다.")
        return stripped

class CategoryUpdate(BaseModel):
    """카테고리 수정 요청 DTO"""
    name: str = Field(..., min_length=1, max_length=50)

class CategoryResponse(BaseModel):
    """카테고리 결과 응답 DTO"""
    id: int
    name: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# 3. CONTACT (연락처 주소록) 도메인 스키마
# ==========================================

class ContactCreate(BaseModel):
    """
    연락처 생성 요청 DTO 
    TRD 기술 스펙 문서의 도메인 정규식 제약 조건을 엄격히 강제합니다.
    """
    # TRD 스펙: 정규식 ^[가-힣]{1,5}$ (1~5자 한글만 허용)
    name: str = Field(
        ..., 
        pattern=r"^[가-힣]{1,5}$", 
        description="이름 (1~5자 한글만 가능)"
    )
    
    # TRD 스펙: 정규식 ^010\d{8}$ (010으로 시작하는 11자리 숫자, 하이픈 제외)
    phone: str = Field(
        ..., 
        pattern=r"^010\d{8}$", 
        description="휴대폰 번호 (하이픈 제외 11자리)"
    )
    
    # TRD 스펙: 정규식 ^.*시$ (반드시 '시'로 종결되어야 함, TR-010 반영)
    address: str = Field(
        ..., 
        pattern=r"^.*시$", 
        description="주소 (반드시 '시'로 끝나야 함, 예: 서울시)"
    )
    
    category_id: int = Field(..., description="소속 카테고리 ID")

class ContactUpdate(BaseModel):
    """
    연락처 부분 수정(PATCH) 요청 DTO
    모든 필드는 선택 사항(Optional)이지만, 입력 시에는 정규식 제약을 동일하게 받습니다.
    """
    name: Optional[str] = Field(None, pattern=r"^[가-힣]{1,5}$")
    phone: Optional[str] = Field(None, pattern=r"^010\d{8}$")
    address: Optional[str] = Field(None, pattern=r"^.*시$")
    category_id: Optional[int] = None

class ContactResponse(BaseModel):
    """연락처 결과 응답 DTO (카테고리 중첩 정보 포함 가능)"""
    id: int
    name: str
    phone: str
    address: str
    user_id: int
    category_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True