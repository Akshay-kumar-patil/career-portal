"""Analytics API routes."""
from datetime import datetime, timedelta
from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.models.application import Application
from backend.models.resume import Resume
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    apps = db.query(Application).filter(Application.user_id == current_user.id).all()
    total = len(apps)

    status_counts = Counter(a.status for a in apps)
    responded = sum(1 for a in apps if a.status not in ("saved", "applied"))
    interviews = sum(1 for a in apps if a.status in ("interview", "technical", "final_round"))
    offers = sum(1 for a in apps if a.status in ("offer", "accepted"))

    # Monthly trend
    now = datetime.utcnow()
    monthly = {}
    for a in apps:
        if a.created_at:
            key = a.created_at.strftime("%Y-%m")
            monthly[key] = monthly.get(key, 0) + 1

    # Source distribution
    source_counts = Counter(a.source or "direct" for a in apps)

    # Top companies
    company_counts = Counter(a.company for a in apps)
    top_companies = [{"company": c, "count": n} for c, n in company_counts.most_common(10)]

    # Resume performance
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_active == 1).all()
    resume_perf = []
    for r in resumes:
        linked_apps = [a for a in apps if a.resume_id == r.id]
        responded_apps = [a for a in linked_apps if a.status not in ("saved", "applied")]
        resume_perf.append({
            "id": r.id,
            "title": r.title,
            "ats_score": r.ats_score,
            "applications": len(linked_apps),
            "responses": len(responded_apps),
            "response_rate": round(len(responded_apps) / max(len(linked_apps), 1) * 100, 1),
        })

    # This month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = sum(1 for a in apps if a.created_at and a.created_at >= month_start)

    avg_excitement = sum(a.excitement_level or 3 for a in apps) / max(total, 1)

    return {
        "total_applications": total,
        "applications_by_status": dict(status_counts),
        "response_rate": round(responded / max(total, 1) * 100, 1),
        "interview_rate": round(interviews / max(total, 1) * 100, 1),
        "offer_rate": round(offers / max(total, 1) * 100, 1),
        "avg_excitement": round(avg_excitement, 1),
        "applications_this_month": this_month,
        "top_companies": top_companies,
        "application_trend": [{"month": k, "count": v} for k, v in sorted(monthly.items())],
        "source_distribution": dict(source_counts),
        "resume_performance": resume_perf,
    }
