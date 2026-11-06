from src.resume_parser import parse_resume
from src.transcript_parser import parse_transcript
from src.ai_analyzer import AIAnalyzer
from src.formatter import parse_response


class PathwayEngine:

    def __init__(self):

        self.ai = AIAnalyzer()

    def analyze_student(self, profile,
                        transcript_path=None,
                        resume_path=None):

        if transcript_path:

            profile.transcript_text = parse_transcript(
                transcript_path
            )

        if resume_path:

            profile.resume_text = parse_resume(
                resume_path
            )

        result = self.ai.analyze(profile)

        return parse_response(result)