import json
import logging
import asyncio
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Global variable to load the Hugging Face text generation pipeline
phi3_flashcards_pipeline = None

def get_phi3_pipeline():
    """
    Lazy loads the local Hugging Face microsoft/Phi-3-mini-4k-instruct pipeline.
    """
    global phi3_flashcards_pipeline
    if settings.LLM_PROVIDER == "mock":
        return None

    if phi3_flashcards_pipeline is None:
        try:
            import torch
            from transformers import pipeline, AutoTokenizer
            
            logger.info("Initializing Hugging Face Phi-3 pipeline for flashcard service...")
            model_id = "microsoft/Phi-3-mini-4k-instruct"
            
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            device = 0 if torch.cuda.is_available() else -1
            
            phi3_flashcards_pipeline = pipeline(
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
            
    return phi3_flashcards_pipeline


class FlashcardGenerationService:
    """
    Service to generate structured QA flashcards from lecture transcripts.
    Configures metadata properties (difficulty, tags) and deduplicates redundant topics.
    """

    SYSTEM_PROMPT = (
        "You are an AI learning assistant. Extract key concepts from the transcript and build study flashcards.\n"
        "Generate a strict JSON array of objects conforming to the schema:\n"
        "[\n"
        "  {\n"
        "    \"question\": \"Short active-recall question about a concept.\",\n"
        "    \"answer\": \"Concise and clear answer.\",\n"
        "    \"difficulty\": \"Easy\" | \"Medium\" | \"Hard\",\n"
        "    \"tag\": \"Single word topic tag (e.g. database, syntax, theory)\"\n"
        "  }\n"
        "]\n"
        "Do not include any conversational introduction or codeblock fences. Return only the JSON list."
    )

    # Fallback mock items
    MOCK_CARDS = [
        {
            "question": "What does CPU stand for?",
            "answer": "Central Processing Unit",
            "difficulty": "Easy",
            "tag": "Hardware"
        },
        {
            "question": "What is the time complexity of looking up a value in a hash map on average?",
            "answer": "O(1) - Constant Time",
            "difficulty": "Medium",
            "tag": "DataStructures"
        },
        {
            "question": "What is a deadlock in concurrent programming?",
            "answer": "A state where two or more threads are blocked forever, each waiting for the other to release resources.",
            "difficulty": "Hard",
            "tag": "Concurrency"
        }
    ]

    def _deduplicate_flashcards(self, cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicates cards based on simple question normalized text lookup.
        Filters out redundant items.
        """
        seen_questions = set()
        unique_cards = []
        
        for card in cards:
            q = card.get("question", "").strip().lower()
            # Basic normalizer - remove question marks and spaces
            normalized = "".join([c for c in q if c.isalnum()])
            if normalized and normalized not in seen_questions:
                seen_questions.add(normalized)
                unique_cards.append(card)
                
        return unique_cards

    async def generate_flashcards(self, transcript_text: str) -> List[Dict[str, Any]]:
        """
        Extracts conceptual flashcards from the transcript text using Phi-3.
        """
        if not transcript_text.strip():
            return []

        if settings.LLM_PROVIDER == "mock":
            await asyncio.sleep(1.0)
            return self.MOCK_CARDS

        pipe = get_phi3_pipeline()
        if not pipe:
            raise RuntimeError("Phi-3 pipeline failed to initialize.")

        formatted_prompt = f"<|system|>\n{self.SYSTEM_PROMPT}<|end|>\n<|user|>\nTranscript:\n{transcript_text}<|end|>\n<|assistant|>\n"
        
        loop = asyncio.get_running_loop()
        def _run():
            outputs = pipe(
                formatted_prompt,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.3,
                top_p=0.9
            )
            return outputs[0]["generated_text"].replace(formatted_prompt, "").strip()

        raw_output = await loop.run_in_executor(None, _run)
        
        try:
            # Parse JSON response
            cards = json.loads(raw_output)
            if isinstance(cards, list):
                # Clean up and deduplicate before returning
                return self._deduplicate_flashcards(cards)
            return self.MOCK_CARDS
        except Exception:
            logger.warning("Failed to parse flashcard array. Returning default mock cards.")
            return self.MOCK_CARDS
