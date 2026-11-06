from src.model_client import GroqClient


class AIAnalyzer:

    def __init__(self):
        self.client = GroqClient()

    def analyze(self, profile):

        prompt = f"""
You are an expert career advisor for college students. Analyze the profile and
return recommendations that are specific, realistic, and supported by the
provided information. Do not invent experience, qualifications, or facts.
When information is missing, keep the recommendation cautious and explain the
uncertainty in the relevant text.

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

Return ONLY valid JSON: no Markdown, code fences, or text outside the JSON.
Use exactly the keys and value types in this schema. Include every key, use an
empty string when a string value is unavailable, and use an empty array when
there are no suitable items. Never return null.

student_summary should be a concise summary of the student's background and
career direction. match_score must be an integer from 0 to 100. Each item in
alternative_pathways must have a title and an integer match_score. Items in
skill_gaps, recommended_projects, recommended_certifications, internships,
and resources must be concise strings.

{{
    "student_summary": "",

    "suggested_pathway": {{
        "title": "",
        "match_score": 0,
        "why_fit": "",
        "weekly_action": ""
    }},

    "alternative_pathways": [
        {{
            "title": "",
            "match_score": 0
        }}
    ],

    "skill_gaps": [],

    "recommended_projects": [],

    "recommended_certifications": [],

    "internships": [],

    "resources": []
}}
"""

        return self.client.generate(prompt)