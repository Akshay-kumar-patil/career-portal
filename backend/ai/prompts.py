"""
Prompt templates for all AI features.
Each prompt is designed for structured JSON output where possible.
"""

RESUME_GENERATION_PROMPT = """You are an expert resume writer specializing in ATS-optimized resumes.

Given the following job description and user information, generate a professional, ATS-optimized resume.

**Job Description:**
{job_description}

**User's Existing Resume / Information:**
{existing_resume}

**Additional Context:**
{additional_context}

Generate a complete resume in the following JSON format:
{{
    "full_name": "...",
    "contact": {{"email": "...", "phone": "...", "linkedin": "...", "location": "..."}},
    "summary": "A 2-3 sentence professional summary tailored to the job",
    "experience": [
        {{
            "title": "...",
            "company": "...",
            "location": "...",
            "dates": "...",
            "bullets": ["Achievement-oriented bullet using metrics and action verbs", ...]
        }}
    ],
    "education": [
        {{"degree": "...", "school": "...", "dates": "...", "gpa": "...", "highlights": [...]}}
    ],
    "skills": {{
        "technical": ["..."],
        "tools": ["..."],
        "soft_skills": ["..."]
    }},
    "projects": [
        {{"name": "...", "description": "...", "technologies": ["..."], "link": "..."}}
    ],
    "certifications": ["..."]
}}

Important rules:
1. Use strong action verbs (Led, Developed, Implemented, Optimized, etc.)
2. Include quantifiable metrics wherever possible
3. Match keywords from the job description naturally
4. Keep bullet points concise (1-2 lines each)
5. Prioritize most relevant experience
6. Return ONLY the JSON, no other text
"""

RESUME_ANALYSIS_PROMPT = """You are an expert ATS (Applicant Tracking System) analyzer and career coach.

Analyze the following resume and provide a detailed assessment.

**Resume:**
{resume_text}

**Target Job Description (if provided):**
{job_description}

Provide your analysis in the following JSON format:
{{
    "ats_score": 0-100,
    "section_feedback": [
        {{
            "section": "summary/experience/education/skills/etc",
            "score": 0-100,
            "feedback": "Detailed feedback",
            "suggestions": ["Specific improvement suggestion"]
        }}
    ],
    "keyword_analysis": {{
        "present_keywords": ["keywords found"],
        "missing_keywords": ["keywords that should be added"],
        "keyword_density_score": 0-100
    }},
    "improvement_suggestions": [
        "Specific, actionable suggestion 1",
        "Specific, actionable suggestion 2"
    ],
    "overall_feedback": "2-3 sentence overall assessment",
    "formatting_issues": ["Any formatting concerns"],
    "strengths": ["Key strengths of the resume"]
}}

Be specific, actionable, and constructive. Return ONLY the JSON.
"""

COVER_LETTER_PROMPT = """You are an expert cover letter writer.

Write a personalized cover letter for the following position.

**Company:** {company_name}
**Role:** {role}
**Job Description:** {job_description}
**Key Skills to Highlight:** {key_skills}
**Tone:** {tone}
**Additional Context:** {additional_context}

**User Profile:**
{user_profile}

Write a compelling cover letter that:
1. Opens with a hook that shows genuine interest
2. Highlights 2-3 most relevant experiences/skills
3. Connects past achievements to the role's requirements
4. Shows knowledge of the company
5. Closes with a confident call to action

Tone guide:
- formal: Professional, traditional structure
- concise: Short, direct, impact-focused (under 250 words)
- creative: Shows personality while remaining professional

Return ONLY the cover letter text, properly formatted with paragraphs.
"""

RECRUITER_SIM_PROMPT = """You are a senior technical recruiter at a top company reviewing applications.

**Resume:**
{resume_text}

**Job Description:**
{job_description}

Evaluate this candidate as a real recruiter would. Provide your assessment in JSON:
{{
    "decision": "shortlisted" or "rejected",
    "confidence": 0.0-1.0,
    "reasoning": [
        "Reason 1 for the decision",
        "Reason 2..."
    ],
    "strengths": ["Candidate strength 1", ...],
    "weaknesses": ["Candidate weakness 1", ...],
    "suggestions": ["What would make this candidate stronger", ...],
    "comparison_notes": "How this candidate compares to the ideal profile"
}}

Be realistic and honest. Consider ATS compatibility, relevance, experience level match, and presentation quality. Return ONLY the JSON.
"""

INTERVIEW_QUESTION_PROMPT = """You are an expert interviewer for the role of {role} at {company}.

Generate {num_questions} interview questions for a {difficulty} difficulty {interview_type} interview.

Interview types:
- hr: Behavioral, situational, culture-fit questions
- technical: Technical knowledge, system design, problem-solving
- mixed: Combination of both

Provide questions in JSON format:
{{
    "questions": [
        {{
            "id": 1,
            "question": "The interview question",
            "type": "hr" or "technical",
            "difficulty": "easy/medium/hard",
            "category": "behavioral/technical/situational/system_design",
            "tips": "Brief tip for answering well",
            "expected_duration_minutes": 3-10
        }}
    ]
}}

Make questions realistic and role-specific. Return ONLY the JSON.
"""

INTERVIEW_EVAL_PROMPT = """You are an expert interviewer evaluating a candidate's answer.

**Question:** {question}
**Candidate's Answer:** {answer}
**Role:** {role}

Evaluate the answer in JSON format:
{{
    "score": 0-10,
    "feedback": "Detailed constructive feedback",
    "strengths": ["What the candidate did well"],
    "improvements": ["What could be improved"],
    "sample_answer": "A strong sample answer for reference"
}}

Be constructive and specific. Return ONLY the JSON.
"""

SKILL_GAP_PROMPT = """You are a career development advisor.

Compare the user's skills against the job requirements and provide a skill gap analysis.

**Job Description:**
{job_description}

**User's Current Skills:**
{user_skills}

Provide analysis in JSON format:
{{
    "missing_skills": [
        {{
            "skill": "Skill name",
            "importance": "critical/important/nice_to_have",
            "estimated_learning_time": "2 weeks / 1 month / 3 months",
            "resources": ["Course or resource suggestion"]
        }}
    ],
    "matched_skills": ["Skills the user already has"],
    "skill_score": 0-100,
    "learning_roadmap": [
        {{
            "phase": 1,
            "title": "Phase title",
            "duration": "2 weeks",
            "skills": ["Skills to learn"],
            "resources": ["Specific courses/tutorials"]
        }}
    ],
    "suggested_projects": [
        "Project idea that demonstrates the missing skills"
    ]
}}

Be specific with learning resources (recommend real platforms like Coursera, Udemy, freeCodeCamp, etc.). Return ONLY the JSON.
"""

EMAIL_GENERATION_PROMPT = """You are an expert at writing professional emails for job seekers.

**Email Type:** {email_type}
**Recipient:** {recipient_name}
**Company:** {company}
**Role:** {role}
**Context:** {context}
**Tone:** {tone}

Email type descriptions:
- cold_email: Reaching out to someone you don't know at the company
- referral_request: Asking someone you know (or loosely know) for a referral
- follow_up: Following up after an application or interview
- thank_you: Thank you email after an interview

Provide the email in JSON format:
{{
    "subject": "Email subject line",
    "body": "Full email body with proper formatting"
}}

Rules:
1. Keep it concise (under 200 words for cold emails)
2. Be respectful of the recipient's time
3. Include a clear ask or purpose
4. Sound human, not robotic
5. Return ONLY the JSON
"""

GITHUB_ANALYSIS_PROMPT = """You are a technical resume writer analyzing GitHub projects.

**GitHub Repositories:**
{repos_data}

For each significant repository, generate resume-ready bullet points that:
1. Start with a strong action verb
2. Describe what was built and why
3. Mention technologies used
4. Include impact/metrics where possible

Provide analysis in JSON format:
{{
    "resume_points": [
        "Built a [project type] using [technologies] that [achievement/impact]",
        ...
    ],
    "tech_stack": ["Technology 1", "Technology 2", ...],
    "project_highlights": [
        {{
            "repo_name": "...",
            "description": "Enhanced description",
            "technologies": ["..."],
            "suggested_bullet": "Resume-ready bullet point"
        }}
    ]
}}

Focus on the most impressive and relevant projects. Return ONLY the JSON.
"""

JD_EXTRACTION_PROMPT = """You are an expert at parsing job descriptions.

**Job Description Text:**
{jd_text}

Extract structured information in JSON format:
{{
    "company": "Company name if mentioned",
    "role": "Job title",
    "skills": ["Required skill 1", "Required skill 2", ...],
    "responsibilities": ["Key responsibility 1", ...],
    "requirements": ["Requirement 1", ...],
    "tools": ["Tool/technology 1", ...],
    "experience_required": "e.g., 3-5 years",
    "education_required": "e.g., Bachelor's in CS",
    "nice_to_haves": ["Nice to have 1", ...],
    "benefits": ["Benefit 1", ...],
    "salary_range": "if mentioned",
    "location": "if mentioned",
    "job_type": "remote/hybrid/onsite if mentioned"
}}

Extract everything available. Return ONLY the JSON.
"""
