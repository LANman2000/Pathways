from dataclasses import dataclass, field

@dataclass
class StudentProfile:

    # Required
    major: str

    # Optional
    interests: str = ""
    goals: str = ""
    skills: list = field(default_factory=list)

    volunteer_experience: str = ""

    transcript_text: str = ""
    resume_text: str = ""

    certifications: list = field(default_factory=list)