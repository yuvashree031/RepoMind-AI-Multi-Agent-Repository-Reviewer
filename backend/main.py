import os
import json
import logging
import traceback
from typing import List, Optional
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from backend.database.mongodb import (
    connect_to_mongodb,
    close_mongodb_connection,
    get_database
)
from backend.database.indexes import create_indexes
from backend.database.collections import (
    USERS_COLLECTION,
    REPOSITORIES_COLLECTION,
    REVIEWS_COLLECTION,
    REPORTS_COLLECTION,
    ANALYSIS_HISTORY_COLLECTION
)

from backend.repositories.user import UserRepository
from backend.repositories.repository import RepositoryRepository
from backend.repositories.review import ReviewRepository
from backend.repositories.report import ReportRepository

from backend.models.models import Repository, Review, Report, User
from backend.schemas.schemas import (
    RepositoryCreate,
    RepositoryResponse,
    ReviewDetailResponse,
    ReportResponse
)

from backend.api.auth import router as auth_router, get_current_user

from backend.agents.workflow import workflow_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("RepoMindAI")

app = FastAPI(
    title="RepoMind AI Backend",
    description="Multi-Agent Automated Repository Auditing Platform running on MongoDB Atlas"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.on_event("startup")
async def on_startup():
    """
    FastAPI startup event. Initializes the database connection pool,
    verifies/creates indexes, and logs collection count metrics.
    """
    logger.info("Starting up RepoMind AI Backend...")
    try:
        await connect_to_mongodb()
        await create_indexes()
        
        db = get_database()
        logger.info(f"MongoDB Connected Successfully. Database: {db.name}")
        
        collections = await db.list_collection_names()
        logger.info(f"Discovered {len(collections)} collections in database.")
        for col_name in collections:
            count = await db[col_name].count_documents({})
            logger.info(f"Collection: {col_name:<25} | Documents Count: {count}")
            
    except Exception as e:
        logger.error(f"Startup check failed: {e}", exc_info=True)

@app.on_event("shutdown")
async def on_shutdown():
    """
    FastAPI shutdown event. Cleans up connection pools.
    """
    logger.info("Shutting down RepoMind AI Backend...")
    await close_mongodb_connection()

@app.get("/health")
async def health_check():
    """
    Health check endpoint to monitor MongoDB connection.
    """
    try:
        db = get_database()
        await db.command("ping")
        return {
            "status": "healthy",
            "mongodb": "connected",
            "database": db.name
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "mongodb": "disconnected",
                "error": str(e)
            }
        )

async def execute_analysis_workflow(review_id: str, repo_url: str, token: Optional[str]):
    """
    Asynchronous background runner executing multi-agent repository evaluation.
    """
    db = get_database()
    review_repo = ReviewRepository(db)
    report_repo = ReportRepository(db)
    
    try:
        logger.info(f"Background thread starting review {review_id} for {repo_url}")
        
        review = await review_repo.find_by_id(review_id)
        if not review:
            logger.error(f"Review {review_id} not found in database.")
            return
            
        await review_repo.update(review_id, {
            "status": "RUNNING",
            "findings": {"logs": ["Initializing agents..."]}
        })
        
        initial_state = {
            "repo_url": repo_url,
            "token": token,
            "repo_path": "",
            "clone_error": None,
            "files_list": [],
            "languages": {},
            "frameworks": [],
            "code_quality_findings": [],
            "security_findings": [],
            "architecture_components": {},
            "devops_findings": [],
            "scores": {
                "security": 100,
                "code_quality": 100,
                "architecture": 100,
                "devops": 100,
                "overall": 100
            },
            "mermaid_diagram": "",
            "report_markdown": "",
            "summary": "",
            "logs": ["Analysis job started."],
            "status": "RUNNING"
        }
        
        import asyncio
        loop = asyncio.get_running_loop()
        final_state = await loop.run_in_executor(None, workflow_app.invoke, initial_state)
        
        if final_state.get("status") == "FAILED" or final_state.get("clone_error"):
            await review_repo.update(review_id, {
                "status": "FAILED",
                "findings": {
                    "logs": final_state.get("logs", []),
                    "error": final_state.get("clone_error", "Unknown agent workflow error")
                }
            })
            return
            
        findings_payload = {
            "code_quality": final_state.get("code_quality_findings", []),
            "security": final_state.get("security_findings", []),
            "architecture": final_state.get("architecture_components", {}),
            "devops": final_state.get("devops_findings", []),
            "logs": final_state.get("logs", []),
            "languages": final_state.get("languages", {}),
            "frameworks": final_state.get("frameworks", []),
            "summary": final_state.get("summary", "")
        }
        
        await review_repo.update(review_id, {
            "status": "COMPLETED",
            "overall_score": final_state["scores"].get("overall", 100),
            "security_score": final_state["scores"].get("security", 100),
            "code_quality_score": final_state["scores"].get("code_quality", 100),
            "architecture_score": final_state["scores"].get("architecture", 100),
            "devops_score": final_state["scores"].get("devops", 100),
            "findings": findings_payload,
            "mermaid_diagram": final_state.get("mermaid_diagram", "")
        })
        
        new_report = Report(
            review_id=review_id,
            content_md=final_state.get("report_markdown", "No report content generated.")
        )
        await report_repo.create(new_report)
        logger.info(f"Background analysis completed successfully for review {review_id}")
        
    except Exception as e:
        logger.error(f"Error in background workflow execution: {e}")
        logger.error(traceback.format_exc())
        
        await review_repo.update(review_id, {
            "status": "FAILED",
            "findings": {
                "logs": [f"Execution crashed: {str(e)}"],
                "error": traceback.format_exc()
            }
        })

@app.post("/api/analyze", status_code=status.HTTP_201_CREATED)
async def analyze_repository(
    payload: RepositoryCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Submits a GitHub repository for automated auditing.
    Cloning and evaluation run in the background. (Auth Required)
    """
    url = payload.url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository URL. Must start with http:// or https://"
        )
        
    clean_url = url.rstrip("/")
    parts = clean_url.split("/")
    if len(parts) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL structure. Must be https://github.com/owner/name"
        )
        
    owner = parts[-2]
    name = parts[-1].replace(".git", "")
    
    repo_repo = RepositoryRepository(db)
    review_repo = ReviewRepository(db)
    
    repository = await repo_repo.find_by_url(url)
    if not repository:
        new_repo = Repository(
            url=url,
            owner=owner,
            name=name,
            default_branch="main",
            description=f"GitHub repository for {owner}/{name}"
        )
        repository = await repo_repo.create(new_repo)
        
    new_review = Review(
        repository_id=str(repository.id),
        user_id=str(current_user.id),
        status="PENDING"
    )
    review = await review_repo.create(new_review)
    
    background_tasks.add_task(execute_analysis_workflow, str(review.id), url, payload.token)
    
    return {
        "review_id": str(review.id),
        "status": "PENDING",
        "repository": {
            "id": str(repository.id),
            "owner": repository.owner,
            "name": repository.name,
            "url": repository.url
        }
    }

@app.get("/api/reviews")
async def get_reviews(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Fetches list of all recent repository reviews, sorted by creation date. (Auth Required)
    """
    review_repo = ReviewRepository(db)
    repo_repo = RepositoryRepository(db)
    
    reviews = await review_repo.find_all(
        query={"user_id": str(current_user.id)},
        sort=[("created_at", -1)]
    )
    
    result = []
    for r in reviews:
        repo = await repo_repo.find_by_id(r.repository_id)
        repo_data = {
            "id": str(repo.id) if repo else "",
            "url": repo.url if repo else "",
            "owner": repo.owner if repo else "",
            "name": repo.name if repo else ""
        } if repo else {"id": "", "url": "", "owner": "", "name": ""}
        
        result.append({
            "id": str(r.id),
            "repository_id": r.repository_id,
            "status": r.status,
            "overall_score": r.overall_score,
            "created_at": r.created_at,
            "repository": repo_data
        })
    return result

@app.get("/api/reviews/{review_id}", response_model=ReviewDetailResponse)
async def get_review_detail(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Fetches detailed metrics, scores, findings, and diagrams for a review session. (Auth Required)
    """
    review_repo = ReviewRepository(db)
    repo_repo = RepositoryRepository(db)
    report_repo = ReportRepository(db)
    
    review = await review_repo.find_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review session not found"
        )
        
    repository = await repo_repo.find_by_id(review.repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
        
    report = await report_repo.find_by_review_id(review_id)
    
    repo_resp = RepositoryResponse(
        id=str(repository.id),
        url=repository.url,
        owner=repository.owner,
        name=repository.name,
        default_branch=repository.default_branch,
        description=repository.description,
        created_at=repository.created_at
    )
    
    report_resp = ReportResponse(
        id=str(report.id),
        review_id=report.review_id,
        content_md=report.content_md,
        created_at=report.created_at
    ) if report else None
    
    return ReviewDetailResponse(
        id=str(review.id),
        repository_id=review.repository_id,
        status=review.status,
        overall_score=review.overall_score,
        security_score=review.security_score,
        code_quality_score=review.code_quality_score,
        architecture_score=review.architecture_score,
        devops_score=review.devops_score,
        findings=review.findings or {},
        mermaid_diagram=review.mermaid_diagram,
        created_at=review.created_at,
        repository=repo_resp,
        report=report_resp
    )

@app.get("/api/reviews/{review_id}/status")
async def get_review_status(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Lightweight endpoint for polling active analysis execution status and logs. (Auth Required)
    """
    review_repo = ReviewRepository(db)
    review = await review_repo.find_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review session not found"
        )
        
    logs = []
    error = None
    if review.findings:
        logs = review.findings.get("logs", [])
        error = review.findings.get("error", None)
        
    return {
        "id": str(review.id),
        "status": review.status,
        "overall_score": review.overall_score,
        "logs": logs,
        "error": error
    }

@app.get("/api/reviews/{review_id}/download")
async def download_report(
    review_id: str,
    token: Optional[str] = None,
    current_user: Optional[User] = None,
    db = Depends(get_database)
):
    """
    Generates the final PDF review report for download.
    Token can be passed in headers (Authorization) or query parameters (token) for direct link support.
    """
    if token:
        from backend.utils.auth import decode_access_token
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid download token")
    elif current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token required")

    review_repo = ReviewRepository(db)
    repo_repo = RepositoryRepository(db)
    report_repo = ReportRepository(db)
    
    review = await review_repo.find_by_id(review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review session not found")
        
    if review.status != "COMPLETED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review report is still in progress")
        
    repo = await repo_repo.find_by_id(review.repository_id)
    report = await report_repo.find_by_review_id(review_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Markdown report document not found")
        
    import tempfile
    from markdown_pdf import MarkdownPdf, Section
    
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, f"repomind_{review_id}.pdf")
    
    try:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(report.content_md))
        pdf.save(pdf_path)
        
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)}"
        )
    finally:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass
                
    filename = f"repomind_report_{repo.owner if repo else 'repo'}_{repo.name if repo else 'name'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
