import json
import logging
import asyncio
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Global variable to load the Hugging Face text generation pipeline
phi3_notes_pipeline = None

def get_phi3_pipeline():
    """
    Lazy loads the local Hugging Face microsoft/Phi-3-mini-4k-instruct pipeline.
    """
    global phi3_notes_pipeline
    if settings.LLM_PROVIDER == "mock":
        return None

    if phi3_notes_pipeline is None:
        try:
            import torch
            from transformers import pipeline, AutoTokenizer
            
            logger.info("Initializing Hugging Face Phi-3 pipeline for notes service...")
            model_id = "microsoft/Phi-3-mini-4k-instruct"
            
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            device = 0 if torch.cuda.is_available() else -1
            
            phi3_notes_pipeline = pipeline(
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
            
    return phi3_notes_pipeline


class LectureNotesService:
    """
    Service to generate structured study materials from transcripts using Phi-3.
    Supports long transcript chunking, prompt templating, and chunk-merging strategies.
    """

    # Structured Prompt templates using Phi-3 special instruct tokens
    SYSTEM_TEMPLATE = (
        "You are an AI academic assistant. Analyze the lecture transcript chunk and extract information.\n"
        "Generate a JSON response conforming strictly to the following schema:\n"
        "{\n"
        "  \"summary\": \"Concise paragraph summarizing the core lessons in this chunk.\",\n"
        "  \"detailed_notes\": [\"Detailed, structured study notes covering details\"],\n"
        "  \"key_concepts\": [\"Name of Concept: Short explanation.\"],\n"
        "  \"formulas\": [\"Formula (e.g., E=mc^2): Context or variables explanation.\"],\n"
        "  \"definitions\": [\"Term: Comprehensive definition.\"],\n"
        "  \"topics\": [\"Extracted topic or subject name\"]\n"
        "}\n"
        "Ensure all JSON syntax is valid. Do not output conversational preamble. Return only the JSON object."
    )

    MERGE_SYSTEM_TEMPLATE = (
        "You are an AI academic editor. Synthesize multiple JSON study guide chunks into a single, cohesive, unified study guide.\n"
        "Remove redundancies and combine summaries.\n"
        "Generate a single JSON response conforming strictly to the schema:\n"
        "{\n"
        "  \"summary\": \"A comprehensive paragraph summarizing the entire lecture.\",\n"
        "  \"detailed_notes\": [\"Deduplicated detailed study notes\"],\n"
        "  \"key_concepts\": [\"Deduplicated Concept: explanation.\"],\n"
        "  \"formulas\": [\"Deduplicated Formula: explanation.\"],\n"
        "  \"definitions\": [\"Deduplicated Term: definition.\"],\n"
        "  \"topics\": [\"Deduplicated Topic names\"]\n"
        "}\n"
        "Return only the valid JSON object."
    )

    def __init__(self, chunk_size_words: int = 1200, overlap_words: int = 150):
        self.chunk_size_words = chunk_size_words
        self.overlap_words = overlap_words

    def _split_into_chunks(self, text: str) -> List[str]:
        """
        Splits text into overlapping sliding-window word chunks.
        This preserves conversational context on borders and fits context boundaries.
        """
        words = text.split()
        if len(words) <= self.chunk_size_words:
            return [text]

        chunks = []
        start = 0
        while start < len(words):
            end = start + self.chunk_size_words
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            
            # Slide window forward, keeping overlap
            start += (self.chunk_size_words - self.overlap_words)
            
        return chunks

    async def _generate_for_chunk(self, chunk_text: str) -> Dict[str, Any]:
        """
        Runs model inference on a single transcript chunk.
        """
        if settings.LLM_PROVIDER == "mock":
            # Fast mock fallback for testing
            return {
                "summary": "This segment introduces key concepts in web API architectures.",
                "detailed_notes": ["FastAPI uses Pydantic for validation.", "Asynchronous routing increases concurrency throughput."],
                "key_concepts": ["Concurrency: Managing multiple tasks at once."],
                "formulas": ["Throughput = Tasks / Time: Measure of server efficiency."],
                "definitions": ["Pydantic: Data parsing and validation library using Python type hints."],
                "topics": ["FastAPI", "Web APIs"]
            }

        pipe = get_phi3_pipeline()
        if not pipe:
            raise RuntimeError("Pipeline failed to initialize.")

        formatted_prompt = f"<|system|>\n{self.SYSTEM_TEMPLATE}<|end|>\n<|user|>\nTranscript Chunk:\n{chunk_text}<|end|>\n<|assistant|>\n"
        
        loop = asyncio.get_running_loop()
        def _run():
            outputs = pipe(
                formatted_prompt,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.2,
                top_p=0.9
            )
            return outputs[0]["generated_text"].replace(formatted_prompt, "").strip()

        raw_output = await loop.run_in_executor(None, _run)
        try:
            return json.loads(raw_output)
        except Exception:
            logger.warning("Failed to parse JSON output from chunk generation. Returning empty schema.")
            return {
                "summary": "",
                "detailed_notes": [],
                "key_concepts": [],
                "formulas": [],
                "definitions": [],
                "topics": []
            }

    async def _merge_chunks(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merges generated chunk dictionaries into a unified study guide structure.
        """
        if len(chunk_results) == 1:
            return chunk_results[0]

        if settings.LLM_PROVIDER == "mock":
            return {
                "summary": "This lecture covers FastAPI architectures, Pydantic validations, and concurrency models.",
                "detailed_notes": [
                    "FastAPI uses Pydantic for clean type validations.",
                    "Asynchronous routing boosts overall request throughput.",
                    "MongoDB handles document persistence natively using JSON structures."
                ],
                "key_concepts": [
                    "Concurrency: The ability to execute multiple tasks simultaneously.",
                    "Type Validation: Enforcing schemas on incoming API payloads."
                ],
                "formulas": [
                    "Throughput = Tasks / Time: Quantifies network service capabilities."
                ],
                "definitions": [
                    "Pydantic: Parsing and validation library utilizing Python type checking.",
                    "Motor: Asynchronous PyMongo driver."
                ],
                "topics": ["FastAPI", "Web APIs", "MongoDB"]
            }

        # Create input representing chunk parts for the compiler template
        merge_input = json.dumps(chunk_results, indent=2)
        pipe = get_phi3_pipeline()
        if not pipe:
            raise RuntimeError("Pipeline failed to initialize.")

        formatted_prompt = f"<|system|>\n{self.MERGE_SYSTEM_TEMPLATE}<|end|>\n<|user|>\nChunk Data:\n{merge_input}<|end|>\n<|assistant|>\n"
        
        loop = asyncio.get_running_loop()
        def _run():
            outputs = pipe(
                formatted_prompt,
                max_new_tokens=1500,
                do_sample=True,
                temperature=0.2,
                top_p=0.9
            )
            return outputs[0]["generated_text"].replace(formatted_prompt, "").strip()

        raw_output = await loop.run_in_executor(None, _run)
        try:
            return json.loads(raw_output)
        except Exception:
            logger.warning("Failed to parse merged JSON. Performing basic fallback list combination.")
            
            # Simple fallback merge mechanism
            combined = {
                "summary": " ".join([c.get("summary", "") for c in chunk_results]),
                "detailed_notes": list(set([n for c in chunk_results for n in c.get("detailed_notes", [])])),
                "key_concepts": list(set([k for c in chunk_results for k in c.get("key_concepts", [])])),
                "formulas": list(set([f for c in chunk_results for f in c.get("formulas", [])])),
                "definitions": list(set([d for c in chunk_results for d in c.get("definitions", [])])),
                "topics": list(set([t for c in chunk_results for t in c.get("topics", [])]))
            }
            return combined

    async def generate_study_guide(self, transcript_text: str) -> Dict[str, Any]:
        """
        Main interface function. Takes a full transcript text, splits it into chunks,
        summarizes each chunk, and synthesizes them into a unified study guide.
        """
        if not transcript_text.strip():
            return {
                "summary": "Empty transcript provided.",
                "detailed_notes": [],
                "key_concepts": [],
                "formulas": [],
                "definitions": [],
                "topics": []
            }

        chunks = self._split_into_chunks(transcript_text)
        logger.info(f"Split transcript into {len(chunks)} chunk(s) for processing.")

        chunk_results = []
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {i}/{len(chunks)}...")
            result = await self._generate_for_chunk(chunk)
            chunk_results.append(result)

        logger.info("Merging chunk outputs into final study guide...")
        final_guide = await self._merge_chunks(chunk_results)
        return final_guide
