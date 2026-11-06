from src.model_client import GroqClient


class AIAnalyzer:

    def __init__(self):
        self.client = GroqClient()

    def analyze(self, profile):

        prompt = f"""
You are an expert career advisor for college students.

Analyze this student profile.

MAJOR:
{profile.major}

INTERESTS:
{profile.interests}

CAREER GOALS:
{profile.goals}

CURRENT SKILLS:
{profile.skills}

VOLUNTEER EXPERIENCE:
{profile.volunteer_experience}

TRANSCRIPT:
{profile.transcript_text}

RESUME:
{profile.resume_text}

CERTIFICATIONS:
{profile.certifications}

Return ONLY valid JSON.

{{
    "suggested_pathway": {{
        "title": "",
        "match_score": 0,
        "why_fit": "",
        "weekly_action": ""
    }},

    "alternative_pathways": [],

    "skill_gaps": [],

    "recommended_projects": [],

    "recommended_certifications": [],

    "internships": [],

    "resources": []
}}
"""

        return self.client.generate(prompt)