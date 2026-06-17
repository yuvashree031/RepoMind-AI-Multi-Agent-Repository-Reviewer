from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class RepositoryCreate(BaseModel):
    url: str
    token: Optional[str] = None

class RepositoryResponse(BaseModel):
    id: str
    url: str
    owner: str
    name: str
    default_branch: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ReportResponse(BaseModel):
    id: str
    review_id: str
    content_md: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReviewDetailResponse(BaseModel):
    id: str
    repository_id: str
    status: str
    overall_score: Optional[int] = None
    security_score: Optional[int] = None
    code_quality_score: Optional[int] = None
    architecture_score: Optional[int] = None
    devops_score: Optional[int] = None
    findings: Optional[Dict[str, Any]] = None
    mermaid_diagram: Optional[str] = None
    created_at: datetime
    repository: RepositoryResponse
    report: Optional[ReportResponse] = None

    class Config:
        from_attributes = True

class ReviewStatusResponse(BaseModel):
    id: str
    repository_id: str
    status: str
    overall_score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
