"""Resume analyzer API routes."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.models.user import User
from backend.schemas.resume import ResumeAnalyzeRequest
from backend.utils.auth import get_current_user
from backend.services.analyzer_service import analyzer_service
from backend.utils.pdf_parser import extract_text_from_file

router = APIRouter(prefix="/api/analyzer", tags=["Analyzer"])


@router.post("/analyze")
def analyze_resume(req: ResumeAnalyzeRequest, current_user: User = Depends(get_current_user)):
    try:
        result = analyzer_service.analyze(req.resume_text, req.job_description or "")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/upload")
async def upload_and_analyze(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a resume file (PDF/DOCX) and get analysis."""
    content = await file.read()
    text = extract_text_from_file(content, file.filename)
    if text.startswith("Error"):
        raise HTTPException(status_code=400, detail=text)
    result = analyzer_service.analyze(text)
    result["extracted_text"] = text
    return result


@router.post("/quick-score")
def quick_score(req: ResumeAnalyzeRequest, current_user: User = Depends(get_current_user)):
    """Quick keyword-based scoring without AI."""
    if not req.job_description:
        raise HTTPException(status_code=400, detail="Job description required for quick score")
    return analyzer_service.quick_score(req.resume_text, req.job_description)
