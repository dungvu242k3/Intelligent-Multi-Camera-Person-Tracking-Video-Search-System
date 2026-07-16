from sqlalchemy import CheckConstraint, Column, Index, Integer, String, Text, text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Role(Base):  # type: ignore[misc,valid-type]
    """SQLAlchemy model representing system security roles."""
    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_roles_name_not_blank"),
        Index("uq_roles_name_lower", text("lower(name)"), unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True) # e.g. admin, operator, user
    description = Column(Text, nullable=True)
