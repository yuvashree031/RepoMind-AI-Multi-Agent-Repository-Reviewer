from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, EmailStr, BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class User(MongoBaseModel):
    email: EmailStr = Field(...)
    password_hash: str = Field(...)
    full_name: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)

class Repository(MongoBaseModel):
    url: str = Field(...)
    owner: str = Field(...)
    name: str = Field(...)
    default_branch: str = Field(default="main")
    description: Optional[str] = Field(default=None)

class Review(MongoBaseModel):
    repository_id: str = Field(...)
    user_id: Optional[str] = Field(default=None)
    status: str = Field(default="PENDING")
    overall_score: Optional[int] = Field(default=None)
    security_score: Optional[int] = Field(default=None)
    code_quality_score: Optional[int] = Field(default=None)
    architecture_score: Optional[int] = Field(default=None)
    devops_score: Optional[int] = Field(default=None)
    findings: Optional[Dict[str, Any]] = Field(default=None)
    mermaid_diagram: Optional[str] = Field(default=None)

class Report(MongoBaseModel):
    review_id: str = Field(...)
    content_md: str = Field(...)

class AnalysisHistory(MongoBaseModel):
    repository_id: str = Field(...)
    review_id: str = Field(...)
    summary: str = Field(...)
    score: int = Field(...)
