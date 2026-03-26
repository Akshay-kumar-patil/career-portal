"""Mock interview service."""
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models.template import InterviewSession
from backend.services.ai_service import ai_service


class InterviewService:

    def generate_questions(self, role: str, company: str = "", interview_type: str = "mixed",
                           difficulty: str = "medium", num_questions: int = 5) -> dict:
        return ai_service.generate_interview_questions(role, company, interview_type, difficulty, num_questions)

    def evaluate_answer(self, question: str, answer: str, role: str) -> dict:
        return ai_service.evaluate_answer(question, answer, role)

    def save_session(self, db: Session, user_id: int, role: str, company: str,
                     interview_type: str, questions: list, answers: list, scores: list) -> InterviewSession:
        overall = sum(s.get("score", 0) for s in scores) / max(len(scores), 1) if scores else 0
        session = InterviewSession(
            user_id=user_id,
            role=role,
            company=company or "",
            interview_type=interview_type,
            questions=json.dumps(questions),
            answers=json.dumps(answers),
            scores=json.dumps(scores),
            overall_score=overall,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_sessions(self, db: Session, user_id: int) -> List[InterviewSession]:
        return db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id
        ).order_by(InterviewSession.created_at.desc()).all()


interview_service = InterviewService()
