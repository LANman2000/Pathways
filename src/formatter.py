import json


class InvalidAnalysisResponse(ValueError):
    """Raised when the model response does not match the public API schema."""


_TOP_LEVEL_KEYS = {
    "student_summary",
    "suggested_pathway",
    "alternative_pathways",
    "skill_gaps",
    "recommended_projects",
    "recommended_certifications",
    "internships",
    "resources",
}

_PATHWAY_KEYS = {"title", "match_score", "why_fit", "weekly_action"}
_ALTERNATIVE_KEYS = {"title", "match_score"}
_LIST_KEYS = {
    "skill_gaps",
    "recommended_projects",
    "recommended_certifications",
    "internships",
    "resources",
}


def _require_exact_keys(value, expected_keys):
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise InvalidAnalysisResponse


def _require_string(value):
    if not isinstance(value, str):
        raise InvalidAnalysisResponse


def _require_match_score(value):
    if type(value) is not int or not 0 <= value <= 100:
        raise InvalidAnalysisResponse


def parse_response(response_text):
    if not isinstance(response_text, str):
        raise InvalidAnalysisResponse

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise InvalidAnalysisResponse from error

    _require_exact_keys(result, _TOP_LEVEL_KEYS)
    _require_string(result["student_summary"])

    pathway = result["suggested_pathway"]
    _require_exact_keys(pathway, _PATHWAY_KEYS)
    for key in ("title", "why_fit", "weekly_action"):
        _require_string(pathway[key])
    _require_match_score(pathway["match_score"])

    alternatives = result["alternative_pathways"]
    if not isinstance(alternatives, list):
        raise InvalidAnalysisResponse
    for alternative in alternatives:
        _require_exact_keys(alternative, _ALTERNATIVE_KEYS)
        _require_string(alternative["title"])
        _require_match_score(alternative["match_score"])

    for key in _LIST_KEYS:
        values = result[key]
        if not isinstance(values, list) or any(
            not isinstance(value, str) for value in values
        ):
            raise InvalidAnalysisResponse

    return result
