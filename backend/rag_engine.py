"""
Leo 2.0 - Advanced RAG Engine
=============================
Retrieval-Augmented Generation for knowledge bases.
Supports document ingestion, chunking, embedding, and search.
"""

import os
import re
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
import threading


@dataclass
class DocumentChunk:
    """A chunk of a document."""
    id: str
    content: str
    source: str
    chunk_index: int
    embedding: Optional[List[float]] = None


class SimpleEmbedding:
    """Simple hash-based embedding for demo. Replace with actual embeddings."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    def embed(self, text: str) -> List[float]:
        """Create a simple numerical embedding from text."""
        # Simple hash-based embedding
        text_hash = hashlib.md5(text.encode()).digest()
        
        # Convert to float list
        embedding = []
        for i in range(self.dimension):
            byte_val = text_hash[i % len(text_hash)]
            embedding.append((byte_val - 128) / 128.0)
        
        return embedding
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)


class RAGEngine:
    """Retrieval-Augmented Generation engine."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            base_dir = Path(__file__).parent.parent
            data_dir = base_dir / "data" / "rag"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.documents_file = self.data_dir / "documents.json"
        self.chunks_file = self.data_dir / "chunks.json"
        
        # Load existing data
        self.documents = self._load_json(self.documents_file, {})
        self.chunks = self._load_json(self.chunks_file, {})
        
        # Embedding model
        self.embedding = SimpleEmbedding()
        
        self.lock = threading.Lock()
    
    def _load_json(self, path: Path, default: Any) -> Any:
        """Load JSON file."""
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return default
    
    def _save_json(self, path: Path, data: Any):
        """Save JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def _generate_id(self, text: str) -> str:
        """Generate unique ID for text."""
        return hashlib.md5(text.encode()).hexdigest()[:16]
    
    # ========== DOCUMENT INGESTION ==========
    
    def extract_pdf_text(self, base64_data: str) -> str:
        """Extract text from PDF using PyPDF2."""
        try:
            import io
            import PyPDF2
            import base64
            
            # Decode base64
            pdf_data = base64.b64decode(base64_data)
            pdf_file = io.BytesIO(pdf_data)
            
            # Extract text
            text = ""
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            return text
        except ImportError:
            # PyPDF2 not available
            return "[PDF content - PyPDF2 not installed. Please install: pip install PyPDF2]"
        except Exception as e:
            return f"[Error extracting PDF: {str(e)}]"
    
    def extract_docx_text(self, base64_data: str) -> str:
        """Extract text from DOCX using python-docx."""
        try:
            import io
            import zipfile
            import base64
            import re
            
            # Decode base64
            docx_data = base64.b64decode(base64_data)
            docx_file = io.BytesIO(docx_data)
            
            # DOCX is a zip file - extract text from word/document.xml
            text = ""
            with zipfile.ZipFile(docx_file) as z:
                if 'word/document.xml' in z.namelist():
                    with z.open('word/document.xml') as xml_file:
                        content = xml_file.read().decode('utf-8')
                        # Remove XML tags
                        text = re.sub(r'<[^>]+>', '', content)
                        text = re.sub(r'\s+', ' ', text).strip()
            
            return text
        except ImportError:
            return "[DOCX content - python-docx not installed. Please install: pip install python-docx]"
        except Exception as e:
            return f"[Error extracting DOCX: {str(e)}]"
    
    def add_document(self, content: str, source: str, metadata: Dict = None, is_base64: bool = False, file_type: str = None) -> str:
        """Add a document to the knowledge base."""
        
        # Handle base64-encoded files (PDF, DOC)
        if is_base64 and file_type in ['pdf', 'doc', 'docx']:
            if file_type == 'pdf':
                content = self.extract_pdf_text(content)
            elif file_type in ['doc', 'docx']:
                content = self.extract_docx_text(content)
        
        with self.lock:
            doc_id = self._generate_id(content)
            
            # Store document
            self.documents[doc_id] = {
                "id": doc_id,
                "source": source,
                "content": content,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "chunk_count": 0
            }
            
            # Chunk the document
            chunks = self._chunk_text(content, doc_id, source)
            
            # Store chunks
            for chunk in chunks:
                self.chunks[chunk.id] = {
                    "id": chunk.id,
                    "content": chunk.content,
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                    "doc_id": doc_id,
                    "created_at": datetime.now().isoformat()
                }
            
            # Update document
            self.documents[doc_id]["chunk_count"] = len(chunks)
            
            # Save to disk
            self._save_json(self.documents_file, self.documents)
            self._save_json(self.chunks_file, self.chunks)
            
            return doc_id
    
    def _chunk_text(self, text: str, doc_id: str, source: str, chunk_size: int = 500, overlap: int = 50) -> List[DocumentChunk]:
        """Split text into chunks."""
        # Split by paragraphs first
        paragraphs = re.split(r'\n\n+', text)
        
        chunks = []
        chunk_index = 0
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If single paragraph is too long, split by sentences
            if len(para) > chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    if len(current_chunk) + len(sent) > chunk_size:
                        if current_chunk:
                            chunk = DocumentChunk(
                                id=f"{doc_id}_{chunk_index}",
                                content=current_chunk.strip(),
                                source=source,
                                chunk_index=chunk_index
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                            current_chunk = sent
                        else:
                            # Even single sentence is too long, force split
                            chunk = DocumentChunk(
                                id=f"{doc_id}_{chunk_index}",
                                content=sent[:chunk_size],
                                source=source,
                                chunk_index=chunk_index
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                            sent = sent[chunk_size:]
                    else:
                        current_chunk += " " + sent
            else:
                if len(current_chunk) + len(para) > chunk_size:
                    chunk = DocumentChunk(
                        id=f"{doc_id}_{chunk_index}",
                        content=current_chunk.strip(),
                        source=source,
                        chunk_index=chunk_index
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    
                    # Keep overlap
                    if overlap > 0 and len(current_chunk) > overlap:
                        current_chunk = current_chunk[-overlap:]
                    else:
                        current_chunk = ""
                
                current_chunk += " " + para
        
        # Add remaining chunk
        if current_chunk.strip():
            chunk = DocumentChunk(
                id=f"{doc_id}_{chunk_index}",
                content=current_chunk.strip(),
                source=source,
                chunk_index=chunk_index
            )
            chunks.append(chunk)
        
        return chunks
    
    # ========== RETRIEVAL ==========
    
    def search(self, query: str, top_k: int = 5, source: str = None) -> List[Dict]:
        """Search for relevant chunks."""
        # Create query embedding
        query_embedding = self.embedding.embed(query)
        
        results = []
        
        for chunk_id, chunk_data in self.chunks.items():
            # Filter by source if specified
            if source and chunk_data.get("source") != source:
                continue
            
            # Simple text matching for now
            chunk_content = chunk_data["content"].lower()
            query_lower = query.lower()
            
            # Calculate simple relevance score
            query_words = set(query_lower.split())
            chunk_words = set(chunk_content.split())
            
            # Word overlap score
            overlap = len(query_words & chunk_words)
            score = overlap / max(len(query_words), 1)
            
            # Boost exact phrase matches
            if query_lower in chunk_content:
                score += 0.5
            
            if score > 0:
                results.append({
                    "chunk_id": chunk_id,
                    "content": chunk_data["content"],
                    "source": chunk_data["source"],
                    "score": score,
                    "doc_id": chunk_data.get("doc_id")
                })
        
        # Sort by score and return top k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def get_context_for_query(self, query: str, max_chars: int = 2000) -> Tuple[str, List[Dict]]:
        """Get combined context for a query."""
        results = self.search(query, top_k=10)
        
        context_parts = []
        sources = []
        
        for result in results:
            if sum(len(p) for p in context_parts) + len(result["content"]) > max_chars:
                break
            context_parts.append(result["content"])
            sources.append(result["source"])
        
        context = "\n\n".join(context_parts)
        return context, sources
    
    # ========== MANAGEMENT ==========
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get a document by ID."""
        return self.documents.get(doc_id)
    
    def list_documents(self) -> List[Dict]:
        """List all documents."""
        return list(self.documents.values())
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its chunks."""
        with self.lock:
            if doc_id not in self.documents:
                return False
            
            # Delete chunks
            chunks_to_delete = [
                chunk_id for chunk_id, chunk in self.chunks.items()
                if chunk.get("doc_id") == doc_id
            ]
            for chunk_id in chunks_to_delete:
                del self.chunks[chunk_id]
            
            # Delete document
            del self.documents[doc_id]
            
            # Save
            self._save_json(self.documents_file, self.documents)
            self._save_json(self.chunks_file, self.chunks)
            
            return True
    
    def get_stats(self) -> Dict:
        """Get RAG statistics."""
        sources = {}
        for chunk in self.chunks.values():
            source = chunk.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "document_count": len(self.documents),
            "chunk_count": len(self.chunks),
            "sources": sources
        }


# Singleton
_rag_engine = None

def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine


# Convenience functions
def add_document(content: str, source: str, metadata: Dict = None) -> str:
    """Add a document."""
    return get_rag_engine().add_document(content, source, metadata)


def search_knowledge_base(query: str, top_k: int = 5) -> List[Dict]:
    """Search the knowledge base."""
    return get_rag_engine().search(query, top_k)


def get_rag_stats() -> Dict:
    """Get RAG statistics."""
    return get_rag_engine().get_stats()
