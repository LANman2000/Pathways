# Handles the interaction with the Groq API for generating responses based on prompts.
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class GroqClient:

    def __init__(self):
        
            api_key=os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError(
                    "GROQ_API_KEY not found in environment variables."
                )   

            self.client = Groq(api_key=api_key)

    def generate(self, prompt):

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content