"""
Safe RAG system that doesn't import ChromaDB at module level.
"""
import os
from django.conf import settings
import PyPDF2
from typing import List, Dict, Any
from openai import OpenAI
from .logger import log_success, log_error, log_info


class DocumentProcessor:
    """Handles document processing and text extraction."""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            log_error("PDF text extraction failed", exception=e, extra_data={"file_path": file_path})
            return ""
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extract text from any supported file type."""
        try:
            if file_path.endswith('.pdf'):
                return DocumentProcessor.extract_text_from_pdf(file_path)
            else:
                # Handle text files (md, txt, etc.)
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                    return text.strip()
        except Exception as e:
            log_error("Text extraction failed", exception=e, extra_data={"file_path": file_path})
            return ""
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > start + chunk_size // 2:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks


class SafeRAGSystem:
    """Safe RAG system that tries ChromaDB but falls back to simple system."""
    
    def __init__(self):
        self.processor = DocumentProcessor()
        try:
            self.openai_client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=30.0
            )
        except Exception as e:
            log_error("OpenAI client initialization failed in RAG system", exception=e)
            self.openai_client = None
        
        # Try to initialize ChromaDB
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.PersistentClient(
                path=str(settings.CHROMA_PERSIST_DIRECTORY),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            self.use_chromadb = True
            log_success("ChromaDB initialized successfully in RAG system")
        except Exception as e:
            log_error("ChromaDB initialization failed, using simple RAG system", exception=e)
            self.use_chromadb = False
            self._init_simple_system()
    
    def _init_simple_system(self):
        """Initialize simple RAG system as fallback."""
        import json
        self.documents_file = os.path.join(settings.BASE_DIR, 'simple_documents.json')
        self.documents = self._load_documents()
    
    def _load_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load documents from file storage."""
        if os.path.exists(self.documents_file):
            try:
                import json
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                log_error("Error loading documents from file", exception=e, extra_data={"documents_file": self.documents_file})
                pass
        return {}
    
    def _save_documents(self):
        """Save documents to file storage."""
        try:
            import json
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log_error("Error saving documents to file", exception=e, extra_data={"documents_file": self.documents_file})
            pass
    
    def ingest_document(self, file_path: str, document_type: str, document_id: str):
        """Ingest a document into the storage system."""
        # Extract text from file (PDF, MD, TXT, etc.)
        text = self.processor.extract_text_from_file(file_path)
        if not text:
            raise ValueError(f"Could not extract text from {file_path}")
        
        # Chunk the text
        chunks = self.processor.chunk_text(text)
        log_info("Document processed for ingestion", extra_data={
            "document_type": document_type,
            "document_id": document_id,
            "text_length": len(text),
            "chunks_count": len(chunks)
        })
        
        if self.use_chromadb:
            # Use ChromaDB
            documents = []
            for i, chunk in enumerate(chunks):
                documents.append({
                    'id': f"{document_id}_chunk_{i}",
                    'text': chunk,
                    'metadata': {
                        'document_type': document_type,
                        'document_id': document_id,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                })
            
            texts = [doc['text'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]
            ids = [doc['id'] for doc in documents]
            
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
        else:
            # Use simple storage
            if document_type not in self.documents:
                self.documents[document_type] = []
            
            for i, chunk in enumerate(chunks):
                self.documents[document_type].append({
                    'id': f"{document_id}_chunk_{i}",
                    'text': chunk,
                    'document_id': document_id,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })
            
            self._save_documents()
        
        log_success("Document ingested successfully", extra_data={
            "document_type": document_type,
            "document_id": document_id,
            "chunks_ingested": len(chunks),
            "storage_type": "ChromaDB" if self.use_chromadb else "Simple file storage"
        })
        
        return len(chunks)
    
    def retrieve_relevant_context(self, query: str, document_types: List[str] = None, 
                                 n_results: int = 5) -> str:
        """Retrieve relevant context for a query."""
        if self.use_chromadb:
            # Use ChromaDB
            where_clause = {}
            if document_types:
                where_clause = {"document_type": {"$in": document_types}}
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
            
            context_parts = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    context_parts.append(f"[{results['metadatas'][0][i]['document_type']}]: {doc}")
            
            return "\n\n".join(context_parts)
        else:
            # Use simple text matching
            if document_types is None:
                document_types = list(self.documents.keys())
            
            relevant_chunks = []
            
            for doc_type in document_types:
                if doc_type in self.documents:
                    for doc in self.documents[doc_type]:
                        # Simple keyword matching
                        if any(keyword.lower() in doc['text'].lower() 
                               for keyword in query.lower().split()):
                            relevant_chunks.append(doc)
            
            # Sort by relevance (simple scoring)
            relevant_chunks.sort(key=lambda x: sum(
                1 for keyword in query.lower().split() 
                if keyword in x['text'].lower()
            ), reverse=True)
            
            # Take top results
            top_chunks = relevant_chunks[:n_results]
            
            context_parts = []
            for doc in top_chunks:
                context_parts.append(f"[{doc.get('document_type', 'unknown')}]: {doc['text']}")
            
            return "\n\n".join(context_parts)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        if not self.openai_client:
            log_error("OpenAI client not available for embedding generation")
            return []
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            log_error("Error generating embedding", exception=e, extra_data={"text_length": len(text)})
            return []
