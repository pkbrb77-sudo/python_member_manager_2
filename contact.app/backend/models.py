from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class User(Base):
    """
    [USERS 엔티티] 
    시스템 사용자 정보를 저장하며, 사용자가 삭제되면 연관된 세션, 카테고리, 연락처가 함께 삭제됩니다 (CASCADE).
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 1:N 관계 정의 (사용자 탈퇴 시 종속 데이터 완전 삭제)
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    categories: Mapped[list["Category"]] = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """
    [SESSIONS 엔티티]
    사용자의 로그인 세션 토큰(UUID 규격)을 관리하는 테이블입니다.
    """
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # N:1 역참조 관계 정의
    user: Mapped["User"] = relationship("User", back_populates="sessions")


class Category(Base):
    """
    [CATEGORIES 엔티티]
    사용자 정의 카테고리(그룹 분류)를 관리합니다. 
    동일한 유저 내에서 카테고리명 중복을 제한하는 비즈니스 규칙을 따릅니다.
    """
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 관계 및 제약 사항 정의
    user: Mapped["User"] = relationship("User", back_populates="categories")
    
    # TR-004 준수: 연락처가 연결되어 있는 카테고리는 삭제가 거부되도록 RESTRICT 제약을 설정합니다.
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="category", passive_deletes="all")


class Contact(Base):
    """
    [CONTACTS 엔티티]
    핵심 비즈니스 데이터인 연락처 정보를 저장합니다.
    전화번호(phone)는 시스템 전체에서 유일해야 합니다 (unique=True).
    """
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(10), nullable=False)  # TRD 정규식 스펙에 맞춘 길이 제한
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False) # 시스템 전체 중복 차단
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 카테고리가 삭제되려 할 때 외래키 제약조건에 의해 에러(409 Conflict)를 발생시켜 무결성을 보호합니다.
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # N:1 역참조 관계 정의
    user: Mapped["User"] = relationship("User", back_populates="contacts")
    category: Mapped["Category"] = relationship("Category", back_populates="contacts")