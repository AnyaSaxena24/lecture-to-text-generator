import os
import logging
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Global instances loaded on demand
embeddings_model = None
chroma_client = None

def get_embeddings():
    """
    Lazy loads the Hugging Face sentence-transformers model.
    """
    global embeddings_model
    if settings.LLM_PROVIDER == "mock":
        return None
    if embeddings_model is None:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            logger.info("Loading sentence-transformers/all-MiniLM-L6-v2 embeddings...")
            embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            logger.info("Embeddings model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Hugging Face embeddings: {e}. Switching to mock.")
            embeddings_model = None
    return embeddings_model

def get_chroma_client():
    """
    Lazy loads the local persistent ChromaDB client.
    """
    global chroma_client
    if settings.LLM_PROVIDER == "mock":
        return None
    if chroma_client is None:
        try:
            import chromadb
            persist_dir = os.path.join(os.getcwd(), "chroma_db")
            os.makedirs(persist_dir, exist_ok=True)
            logger.info(f"Initializing ChromaDB persistent client at {persist_dir}")
            chroma_client = chromadb.PersistentClient(path=persist_dir)
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}. Switching to mock.")
            chroma_client = None
    return chroma_client


class VectorStoreService:
    """
    Manages vector embeddings database using ChromaDB.
    Enables semantic document chunk searches and LangChain RAG chat pipelines.
    """

    @staticmethod
    def index_transcript(lecture_id: str, segments: List[Dict[str, Any]]) -> bool:
        """
        Extracts transcript lines, formats text vectors, and stores them in a Chroma collection.
        """
        if settings.LLM_PROVIDER == "mock":
            return True

        try:
            client = get_chroma_client()
            embed = get_embeddings()
            if not client or not embed:
                return False

            # Create or load collection for this specific lecture
            collection_name = f"lecture_{lecture_id}"
            
            # Delete old collection if it exists to refresh indices
            try:
                client.delete_collection(collection_name)
            except Exception:
                pass
                
            collection = client.get_or_create_collection(collection_name)
            
            documents = []
            ids = []
            metadatas = []
            
            for idx, seg in enumerate(segments):
                text = seg.get("text", "").strip()
                if not text:
                    continue
                
                documents.append(text)
                ids.append(f"seg_{idx}")
                metadatas.append({
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "lecture_id": lecture_id
                })
            
            if documents:
                # Generate embeddings and insert into Chroma
                embeddings = embed.embed_documents(documents)
                collection.add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Indexed {len(documents)} segments in Chroma collection: {collection_name}")
            return True
        except Exception as e:
            logger.exception(f"Error indexing transcript in ChromaDB: {e}")
            return False

    @staticmethod
    def semantic_search(lecture_id: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search on the lecture's Chroma database.
        """
        if settings.LLM_PROVIDER == "mock" or get_chroma_client() is None:
            # Fallback mock search results
            return [
                {
                    "text": "This is a mock search result segment talking about FastAPI routers.",
                    "metadata": {"start": 12.0, "end": 18.0, "lecture_id": lecture_id},
                    "distance": 0.15
                }
            ]

        try:
            client = get_chroma_client()
            embed = get_embeddings()
            collection_name = f"lecture_{lecture_id}"
            
            collection = client.get_collection(collection_name)
            query_embedding = embed.embed_query(query)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            formatted_results = []
            if results and "documents" in results and results["documents"]:
                docs = results["documents"][0]
                metas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
                
                for idx in range(len(docs)):
                    formatted_results.append({
                        "text": docs[idx],
                        "metadata": metas[idx],
                        "distance": float(distances[idx])
                    })
                    
            return formatted_results
        except Exception as e:
            logger.error(f"Error during semantic search in ChromaDB: {e}")
            return []

    @staticmethod
    async def chat_with_lecture(lecture_id: str, query: str, context_history: str = "") -> str:
        """
        LangChain RAG pipeline querying the local vector store and generating a response using Phi-3.
        """
        if settings.LLM_PROVIDER == "mock":
            await asyncio.sleep(1.0)
            return f"This is a mock answer to your question: '{query}'. It is based on the local transcript vector chunks stored in ChromaDB."

        try:
            # Retrieve relevant chunks
            chunks = VectorStoreService.semantic_search(lecture_id, query, k=3)
            context_text = "\n".join([f"[{c['metadata'].get('start', 0.0)}s]: {c['text']}" for c in chunks])
            
            # Import generation pipeline lazy loader
            from app.services.ai_generation import run_phi3_prompt
            
            system_prompt = (
                "You are an academic chatbot tutor. Answer the user's question using the provided context chunks.\n"
                "State the timestamps of the context you references when explaining topics."
            )
            
            user_prompt = (
                f"Context from Lecture:\n{context_text}\n\n"
                f"Question: {query}"
            )
            
            response = await run_phi3_prompt(system_prompt, user_prompt)
            return response
            
        except Exception as e:
            logger.error(f"RAG chat failed: {e}")
            return "Could not generate RAG answer from local vectors."
