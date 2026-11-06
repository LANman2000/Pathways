# converts Groq text into python dictionary format

import json

def parse_response(response_text):

    try:
        return json.loads(response_text)

    except Exception:

        return {
            "error": "Model did not return valid JSON",
            "raw_response": response_text
        }