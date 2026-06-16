import json
import logging
import asyncio
from app.config import settings

logger = logging.getLogger(__name__)

# Global variable to hold the Hugging Face text generation pipeline
phi3_pipeline_instance = None

def get_phi3_pipeline():
    """
    Lazy loads the local Hugging Face microsoft/Phi-3-mini-4k-instruct pipeline.
    Avoids slow server startup and saves memory if not used.
    """
    global phi3_pipeline_instance
    if settings.LLM_PROVIDER == "mock":
        return None

    if phi3_pipeline_instance is None:
        try:
            import torch
            from transformers import pipeline, AutoTokenizer
            
            logger.info("Initializing Hugging Face Phi-3 pipeline...")
            model_id = "microsoft/Phi-3-mini-4k-instruct"
            
            # Load tokenizer and model pipeline
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            device = 0 if torch.cuda.is_available() else -1
            
            phi3_pipeline_instance = pipeline(
                "text-generation",
                model=model_id,
                tokenizer=tokenizer,
                device=device,
                torch_dtype="auto",
                trust_remote_code=True
            )
            logger.info("Hugging Face Phi-3 pipeline loaded successfully.")
        except Exception as e:
            logger.exception(f"Failed to load local Phi-3 pipeline: {e}. Falling back to mock generator.")
            settings.LLM_PROVIDER = "mock"
            
    return phi3_pipeline_instance

async def run_phi3_prompt(system_prompt: str, user_prompt: str) -> str:
    """
    Formulates prompt using Phi-3 templates and runs inference in a threadpool.
    """
    if settings.LLM_PROVIDER == "mock":
        await asyncio.sleep(1.5)
        return ""

    loop = asyncio.get_running_loop()
    try:
        pipe = get_phi3_pipeline()
        if pipe is None:
            return ""

        # Phi-3 special tokens formatting
        formatted_prompt = f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{user_prompt}<|end|>\n<|assistant|>\n"

        def _generate():
            logger.info("Running Phi-3 text-generation model...")
            outputs = pipe(
                formatted_prompt,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.3,
                top_k=50,
                top_p=0.9
            )
            generated_text = outputs[0]["generated_text"]
            # Extract only the assistant's response part
            response = generated_text.replace(formatted_prompt, "").strip()
            return response

        return await loop.run_in_executor(None, _generate)
    except Exception as e:
        logger.error(f"Error during Phi-3 text generation: {e}")
        return ""

# DYNAMIC FALLBACK GENERATOR FROM TRANSCRIPT
def generate_dynamic_fallback(transcript_text: str):
    import re
    # Clean and split into sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', transcript_text) if len(s.strip()) > 10]
    
    if not sentences:
        sentences = ["No transcript content was provided to generate notes."]
        
    # Generate summary: use the full transcript text as requested
    summary = transcript_text
    
    # Generate bullet notes: use sentences as bullet notes
    bullet_notes = []
    for s in sentences[:8]:
        cleaned = s[0].upper() + s[1:]
        if not cleaned.endswith(('.', '?', '!')):
            cleaned += '.'
        bullet_notes.append(cleaned)
        
    # Generate flashcards: make question/answer pair from sentences
    flashcards = []
    common_concepts = [
        ("FastAPI", "FastAPI"),
        ("MongoDB", "MongoDB"),
        ("Python", "Python"),
        ("Next.js", "Next.js"),
        ("React", "React"),
        ("Whisper", "Whisper"),
        ("model", "model"),
        ("API", "API"),
        ("data", "data"),
        ("server", "server")
    ]
    
    for i, s in enumerate(sentences):
        matched_concept = None
        for concept, kw in common_concepts:
            if kw.lower() in s.lower():
                matched_concept = concept
                break
        
        if matched_concept:
            question = f"What is discussed regarding {matched_concept} in this lecture?"
            answer = s[0].upper() + s[1:]
            if not answer.endswith('.'):
                answer += '.'
            flashcards.append({"question": question, "answer": answer})
        else:
            snippet = s[:40] + "..." if len(s) > 40 else s
            question = f"What is the key point regarding: '{snippet}'?"
            answer = s[0].upper() + s[1:]
            if not answer.endswith('.'):
                answer += '.'
            flashcards.append({"question": question, "answer": answer})
            
        if len(flashcards) >= 5:
            break
            
    if len(flashcards) < 2:
        flashcards = [
            {"question": "What is the primary topic of the lecture?", "answer": sentences[0]},
            {"question": "What is a key detail mentioned in the lecture?", "answer": sentences[-1] if len(sentences) > 1 else sentences[0]}
        ]
        
    # Generate quizzes: multiple choice questions based on sentences
    quizzes = []
    stopwords = {"about", "there", "their", "would", "could", "should", "these", "those", "which", "where", "under", "using", "first", "hello", "welcome", "today", "lecture", "build", "learn"}
    
    for i, s in enumerate(sentences):
        words = [w.strip(',.()[]{}":;') for w in s.split() if len(w.strip(',.()[]{}":;')) > 4]
        words = [w for w in words if w.lower() not in stopwords]
        
        if words:
            blank_word = words[len(words) // 2]
            question_text = s.replace(blank_word, "_______")
            
            correct = blank_word
            alt_options = ["alternative", "mechanism", "framework", "component", "process", "approach", "module", "system"]
            options = [correct]
            for alt in alt_options:
                if alt.lower() != correct.lower() and len(options) < 4:
                    options.append(alt)
            
            # Sort options by length for simple ordering
            options = sorted(list(set(options)), key=lambda x: len(x))
            
            # Ensure we have 4 options
            while len(options) < 4:
                options.append(f"option_{len(options) + 1}")
            
            quizzes.append({
                "question": f"Fill in the blank: \"{question_text}\"",
                "options": options,
                "correct_answer": correct,
                "explanation": f"Based on the transcript: \"{s}\""
            })
            
        if len(quizzes) >= 4:
            break
            
    if not quizzes:
        quizzes = [
            {
                "question": "What was the main theme of this lecture?",
                "options": ["Technical details of the subject", "Introduction and history", "Future scope", "None of the above"],
                "correct_answer": "Technical details of the subject",
                "explanation": "The transcript discusses technical aspects of the topic."
            }
        ]
        
    return summary, bullet_notes, flashcards, quizzes

async def generate_notes(transcript_text: str) -> dict:
    """
    Generates a dictionary containing 'summary' (str) and 'bullet_notes' (list of str).
    """
    if settings.LLM_PROVIDER == "gemini":
        try:
            from app.services.gemini_service import generate_notes_with_gemini
            return await generate_notes_with_gemini(transcript_text)
        except Exception as e:
            logger.error(f"Gemini notes generation failed: {e}")
            summary, bullet_notes, _, _ = generate_dynamic_fallback(transcript_text)
            return {"summary": summary, "bullet_notes": bullet_notes}

    if settings.LLM_PROVIDER == "mock":
        summary, bullet_notes, _, _ = generate_dynamic_fallback(transcript_text)
        return {"summary": summary, "bullet_notes": bullet_notes}

    system_prompt = (
        "You are an AI teaching assistant. Summarize the transcript and extract bullet points.\n"
        "Format the output strictly as a JSON object with keys: 'summary' (string) and 'bullet_notes' (list of strings)."
    )
    user_prompt = f"Transcript:\n{transcript_text}"
    
    response = await run_phi3_prompt(system_prompt, user_prompt)
    try:
        data = json.loads(response)
        return {
            "summary": data.get("summary", ""),
            "bullet_notes": data.get("bullet_notes", [])
        }
    except Exception:
        logger.warning("Failed to parse JSON response from Phi-3 for notes generation. Using fallbacks.")
        summary, bullet_notes, _, _ = generate_dynamic_fallback(transcript_text)
        return {"summary": summary, "bullet_notes": bullet_notes}

async def generate_flashcards(transcript_text: str) -> list:
    """
    Generates a list of flashcard objects: [{'question': str, 'answer': str}]
    """
    if settings.LLM_PROVIDER == "gemini":
        try:
            from app.services.gemini_service import generate_flashcards_with_gemini
            return await generate_flashcards_with_gemini(transcript_text)
        except Exception as e:
            logger.error(f"Gemini flashcards generation failed: {e}")
            _, _, flashcards, _ = generate_dynamic_fallback(transcript_text)
            return flashcards

    if settings.LLM_PROVIDER == "mock":
        _, _, flashcards, _ = generate_dynamic_fallback(transcript_text)
        return flashcards

    system_prompt = (
        "You are an AI teaching assistant. Extract key terms and concept QA pairs from the transcript.\n"
        "Format the output strictly as a JSON list of objects, where each object has: 'question' and 'answer'."
    )
    user_prompt = f"Transcript:\n{transcript_text}"
    
    response = await run_phi3_prompt(system_prompt, user_prompt)
    try:
        data = json.loads(response)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "flashcards" in data:
            return data["flashcards"]
        raise ValueError("Invalid format")
    except Exception:
        logger.warning("Failed to parse JSON response from Phi-3 for flashcards. Using fallbacks.")
        _, _, flashcards, _ = generate_dynamic_fallback(transcript_text)
        return flashcards

async def generate_quiz(transcript_text: str) -> list:
    """
    Generates a list of quiz items: [{'question': str, 'options': [...], 'correct_answer': str, 'explanation': str}]
    """
    if settings.LLM_PROVIDER == "gemini":
        try:
            from app.services.gemini_service import generate_quiz_with_gemini
            return await generate_quiz_with_gemini(transcript_text)
        except Exception as e:
            logger.error(f"Gemini quiz generation failed: {e}")
            _, _, _, quizzes = generate_dynamic_fallback(transcript_text)
            return quizzes

    if settings.LLM_PROVIDER == "mock":
        _, _, _, quizzes = generate_dynamic_fallback(transcript_text)
        return quizzes

    system_prompt = (
        "You are an AI teaching assistant. Create a practice multiple-choice quiz based on the transcript.\n"
        "Format the output strictly as a JSON list of objects, where each object has:\n"
        "- 'question' (string)\n"
        "- 'options' (list of 4 strings)\n"
        "- 'correct_answer' (string matching one of the options)\n"
        "- 'explanation' (string detail why the answer is correct)"
    )
    user_prompt = f"Transcript:\n{transcript_text}"
    
    response = await run_phi3_prompt(system_prompt, user_prompt)
    try:
        data = json.loads(response)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "quizzes" in data:
            return data["quizzes"]
        raise ValueError("Invalid format")
    except Exception:
        logger.warning("Failed to parse JSON response from Phi-3 for quiz. Using fallbacks.")
        _, _, _, quizzes = generate_dynamic_fallback(transcript_text)
        return quizzes

async def generate_lecture_notes(transcript_text: str) -> tuple:
    """
    Wrapper function to compile notes, flashcards, and quizzes sequentially from the transcript.
    Used for compatibility with background pipeline routes.
    """
    if settings.LLM_PROVIDER == "mock":
        return generate_dynamic_fallback(transcript_text)

    # For gemini and all other providers, call individual generators
    notes = await generate_notes(transcript_text)
    flashcards = await generate_flashcards(transcript_text)
    quizzes = await generate_quiz(transcript_text)
    return notes["summary"], notes["bullet_notes"], flashcards, quizzes

