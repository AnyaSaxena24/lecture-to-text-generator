import json
import logging
import asyncio
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Global variable to load the Hugging Face text generation pipeline
phi3_quiz_pipeline = None

def get_phi3_pipeline():
    """
    Lazy loads the local Hugging Face microsoft/Phi-3-mini-4k-instruct pipeline.
    """
    global phi3_quiz_pipeline
    if settings.LLM_PROVIDER == "mock":
        return None

    if phi3_quiz_pipeline is None:
        try:
            import torch
            from transformers import pipeline, AutoTokenizer
            
            logger.info("Initializing Hugging Face Phi-3 pipeline for quiz service...")
            model_id = "microsoft/Phi-3-mini-4k-instruct"
            
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            device = 0 if torch.cuda.is_available() else -1
            
            phi3_quiz_pipeline = pipeline(
                "text-generation",
                model=model_id,
                tokenizer=tokenizer,
                device=device,
                torch_dtype="auto",
                trust_remote_code=True
            )
            logger.info("Hugging Face Phi-3 pipeline loaded successfully.")
        except Exception as e:
            logger.exception(f"Failed to load local Phi-3 pipeline: {e}. Using mock mode.")
            settings.LLM_PROVIDER = "mock"
            
    return phi3_quiz_pipeline


class QuizGenerationService:
    """
    Service to generate structured academic quizzes from lecture transcripts using Phi-3.
    Extracts MCQs, True/False, and Short Answer items with answer keys and difficulty scales.
    """

    SYSTEM_PROMPT = (
        "You are an AI academic examiner. Create a practice quiz based on the transcript.\n"
        "Generate a strict JSON array of objects conforming to the schema:\n"
        "[\n"
        "  {\n"
        "    \"question\": \"Clear question text.\",\n"
        "    \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"],\n"
        "    \"correct_answer\": \"The exact correct option string (or correct answer description for short answers).\",\n"
        "    \"difficulty\": \"Easy\" | \"Medium\" | \"Hard\",\n"
        "    \"type\": \"mcq\" | \"true_false\" | \"short_answer\"\n"
        "  }\n"
        "]\n"
        "Requirements:\n"
        "1. For 'true_false' type: options must be [\"True\", \"False\"].\n"
        "2. For 'short_answer' type: options must be an empty list [].\n"
        "Do not write preamble. Return only valid JSON."
    )

    # Fallback mock items
    MOCK_QUIZ = [
        {
            "question": "FastAPI routes are synchronously run by default.",
            "options": ["True", "False"],
            "correct_answer": "False",
            "difficulty": "Easy",
            "type": "true_false"
        },
        {
            "question": "Which of the following database options is recommended for async operations in FastAPI?",
            "options": ["SQLite", "MongoDB via Motor", "Standard PyMongo", "Oracle DB"],
            "correct_answer": "MongoDB via Motor",
            "difficulty": "Medium",
            "type": "mcq"
        },
        {
            "question": "What is the purpose of Pydantic schemas in FastAPI request parsing?",
            "options": [],
            "correct_answer": "Pydantic schemas enforce type validation, schema definitions, and serialize incoming request payloads.",
            "difficulty": "Hard",
            "type": "short_answer"
        }
    ]

    def _deduplicate_quiz_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicates quiz items based on question text normalization.
        """
        seen_questions = set()
        unique_items = []
        
        for item in items:
            q = item.get("question", "").strip().lower()
            normalized = "".join([c for c in q if c.isalnum()])
            if normalized and normalized not in seen_questions:
                seen_questions.add(normalized)
                unique_items.append(item)
                
        return unique_items

    async def generate_quiz(self, transcript_text: str) -> List[Dict[str, Any]]:
        """
        Generates a quiz from the transcript text using the Phi-3 pipeline.
        """
        if not transcript_text.strip():
            return []

        if settings.LLM_PROVIDER == "mock":
            await asyncio.sleep(1.0)
            return self.MOCK_QUIZ

        pipe = get_phi3_pipeline()
        if not pipe:
            raise RuntimeError("Phi-3 pipeline failed to initialize.")

        formatted_prompt = f"<|system|>\n{self.SYSTEM_PROMPT}<|end|>\n<|user|>\nTranscript:\n{transcript_text}<|end|>\n<|assistant|>\n"
        
        loop = asyncio.get_running_loop()
        def _run():
            outputs = pipe(
                formatted_prompt,
                max_new_tokens=1200,
                do_sample=True,
                temperature=0.3,
                top_p=0.9
            )
            return outputs[0]["generated_text"].replace(formatted_prompt, "").strip()

        raw_output = await loop.run_in_executor(None, _run)
        
        try:
            items = json.loads(raw_output)
            if isinstance(items, list):
                return self._deduplicate_quiz_items(items)
            return self.MOCK_QUIZ
        except Exception:
            logger.warning("Failed to parse quiz array from Phi-3 output. Returning mock quiz.")
            return self.MOCK_QUIZ
