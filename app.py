import os
import time
import shutil
import re
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Multi-engine PDF and OCR
import pymupdf
import pdfplumber

try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_RAPIDOCR = True
except Exception:
    RapidOCR = None
    HAS_RAPIDOCR = False

# LangChain imports
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# Load environment variables
load_dotenv(override=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'rag-pdf-reader-secret-key-2026')

# Support both local environments and Vercel serverless (/tmp)
if os.environ.get('VERCEL') or not os.access(os.path.dirname(os.path.abspath(__file__)), os.W_OK):
    app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'pdf_uploads')
else:
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# State management
history = []  # List of {'role': 'user'|'assistant', 'content': str}
current_files = []  # List of dicts: {'name': str, 'display_name': str, 'pages': int, 'chunks': int, 'size': str}
vector_store = None

DEFAULT_MODEL = "groq/compound-mini"
FALLBACK_ACTIVE_MODELS = [
    "groq/compound-mini",
    "groq/compound",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b"
]

class ChromaLocalEmbeddings:
    """Local ONNX-based MiniLM embeddings (all-MiniLM-L6-v2) that runs 100% locally with zero external API key requirements."""
    def __init__(self):
        self.ef = DefaultEmbeddingFunction()

    def embed_documents(self, texts):
        return self.ef(texts)

    def embed_query(self, text):
        return self.ef([text])[0]

# Embedding caching
_cached_embeddings = None
_cached_embeddings_name = None

def get_embeddings():
    """Retrieve embeddings instance: Instant local MiniLM by default, or Nomic if explicitly enabled and valid."""
    global _cached_embeddings, _cached_embeddings_name
    if _cached_embeddings is not None:
        return _cached_embeddings, _cached_embeddings_name

    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    nomic_key = os.getenv("NOMIC_API_KEY", "").strip().strip('"').strip("'")
    
    if provider == "nomic" and nomic_key and not nomic_key.startswith("nk-placeholder") and not nomic_key.startswith("your_"):
        try:
            from langchain_nomic import NomicEmbeddings
            emb = NomicEmbeddings(model="nomic-embed-text-v1.5", nomic_api_key=nomic_key)
            emb.embed_query("test")
            _cached_embeddings = emb
            _cached_embeddings_name = "Nomic (nomic-embed-text-v1.5)"
            return _cached_embeddings, _cached_embeddings_name
        except Exception as e:
            print(f"Nomic unavailable ({e}), using local MiniLM ONNX.")

    _cached_embeddings = ChromaLocalEmbeddings()
    _cached_embeddings_name = "Local MiniLM-L6-v2 (ONNX)"
    return _cached_embeddings, _cached_embeddings_name

# Lazy OCR initialization
_ocr_engine = None
def get_ocr_engine():
    global _ocr_engine
    if not HAS_RAPIDOCR or RapidOCR is None:
        return None
    if _ocr_engine is None:
        try:
            _ocr_engine = RapidOCR()
        except Exception as e:
            print(f"Could not load RapidOCR: {e}")
            _ocr_engine = None
    return _ocr_engine

def get_groq_api_key():
    load_dotenv(override=True)
    key = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
    if not key or key.startswith("your_") or key == "gsk_placeholder":
        return None
    return key

def get_available_models():
    """Queries Groq API dynamically for active models on the user's account."""
    groq_key = get_groq_api_key()
    if not groq_key:
        return FALLBACK_ACTIVE_MODELS
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        all_models = client.models.list().data
        active = []
        for m in all_models:
            mid = m.id
            if any(skip in mid for skip in ['whisper', 'prompt-guard', 'safeguard', 'orpheus', 'allam']):
                continue
            active.append(mid)
        if active:
            return active
    except Exception as e:
        print("Error fetching dynamic models list:", e)
        
    return FALLBACK_ACTIVE_MODELS

def get_current_model():
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    if any(dep in model for dep in ['gemma2', 'llama3-70b-8192', 'llama3-8b-8192', 'mixtral']):
        return DEFAULT_MODEL
    return model

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def format_file_size(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def extract_pdf_documents(file_path, filename):
    """
    Multi-Engine PDF Extractor:
    1. PyMuPDF (fitz) for vector text, CID, subsetted fonts, layout.
    2. pdfplumber for complex stream parsing.
    3. RapidOCR (Local ONNX) for scanned or image-based PDFs without selectable text.
    """
    documents = []
    total_pages = 0

    # Engine 1: PyMuPDF
    try:
        doc = pymupdf.open(file_path)
        if doc.is_encrypted:
            try:
                doc.authenticate('')
            except Exception:
                pass
        total_pages = len(doc)
        for idx, page in enumerate(doc):
            try:
                text = page.get_text("text") or ""
                if text.strip():
                    documents.append(Document(
                        page_content=text.strip(),
                        metadata={"source_file": filename, "page": idx}
                    ))
            except Exception as e:
                print(f"PyMuPDF page {idx} error: {e}")
        doc.close()
    except Exception as e:
        print(f"PyMuPDF open error on {filename}: {e}")
        documents = []

    # Engine 2: pdfplumber fallback if nothing extracted
    if not documents:
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                for idx, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        documents.append(Document(
                            page_content=text.strip(),
                            metadata={"source_file": filename, "page": idx}
                        ))
        except Exception as e:
            print(f"pdfplumber extraction error on {filename}: {e}")

    # Engine 3: pypdf fallback
    if not documents:
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            if total_pages == 0:
                total_pages = len(reader.pages)
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    documents.append(Document(
                        page_content=text.strip(),
                        metadata={"source_file": filename, "page": idx}
                    ))
        except Exception as e:
            print(f"pypdf extraction error on {filename}: {e}")

    # Engine 4: RapidOCR Fallback for Scanned image PDFs
    if not documents and total_pages > 0:
        print(f"No selectable text found in {filename}. Attempting OCR across {total_pages} page(s)...")
        ocr = get_ocr_engine()
        if ocr is not None:
            try:
                import gc
                doc = pymupdf.open(file_path)
                for idx, page in enumerate(doc):
                    try:
                        # Use dpi=90 to conserve memory on 512MB RAM containers
                        pix = page.get_pixmap(dpi=90)
                        img_bytes = pix.tobytes("png")
                        del pix
                        ocr_res, _ = ocr(img_bytes)
                        del img_bytes
                        if ocr_res:
                            page_text = " ".join([item[1] for item in ocr_res if item and len(item) > 1 and item[1]])
                            if page_text.strip():
                                documents.append(Document(
                                    page_content=page_text.strip(),
                                    metadata={"source_file": filename, "page": idx}
                                ))
                        gc.collect()
                    except Exception as page_ocr_err:
                        print(f"OCR error on page {idx}: {page_ocr_err}")
                doc.close()
            except Exception as ocr_err:
                print(f"OCR engine error on {filename}: {ocr_err}")
        else:
            print("OCR engine not available in this environment.")

    # Engine 5: Structural Fallback to guarantee uploads never fail even on purely visual PDFs
    if not documents and total_pages > 0:
        print(f"Creating structural document nodes for {filename} ({total_pages} page(s))...")
        try:
            doc = pymupdf.open(file_path)
            for idx, page in enumerate(doc):
                img_count = len(page.get_images())
                img_desc = f"Contains {img_count} high-resolution image object(s)" if img_count > 0 else "Image-based document page"
                documents.append(Document(
                    page_content=f"Document: {filename} | Page {idx + 1} of {total_pages}. Content: {img_desc}.",
                    metadata={"source_file": filename, "page": idx}
                ))
            doc.close()
        except Exception:
            for idx in range(total_pages):
                documents.append(Document(
                    page_content=f"Document: {filename} | Page {idx + 1} of {total_pages}.",
                    metadata={"source_file": filename, "page": idx}
                ))

    return documents, total_pages

def rebuild_vector_store():
    """Rebuilds the vector store from all files currently registered in current_files."""
    global vector_store, current_files
    
    if not current_files:
        vector_store = None
        return True
    
    all_chunks = []
    emb, _ = get_embeddings()
    
    for file_info in current_files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info['name'])
        if not os.path.exists(file_path):
            continue
        try:
            valid_docs, _ = extract_pdf_documents(file_path, file_info['name'])
            if valid_docs:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
                chunks = splitter.split_documents(valid_docs)
                all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error reading {file_info['name']} during rebuild: {e}")
            
    if all_chunks:
        vector_store = Chroma.from_documents(all_chunks, emb)
    else:
        vector_store = None
    return True

def process_pdf(file_path, filename):
    """Processes a single PDF file and adds its chunks to Chroma vector store."""
    global vector_store, current_files
    
    try:
        valid_docs, total_pages = extract_pdf_documents(file_path, filename)
        
        if not valid_docs:
            return False, "Could not extract readable text or OCR content from this PDF.", total_pages, 0
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_documents(valid_docs)
        
        if not chunks:
            return False, "No text chunks could be generated from this PDF.", total_pages, 0
        
        emb, _ = get_embeddings()
        
        if vector_store is None:
            vector_store = Chroma.from_documents(chunks, emb)
        else:
            vector_store.add_documents(chunks)
            
        chunks_count = len(chunks)
        pages_count = max(total_pages, len(valid_docs))
        return True, "Successfully indexed PDF", pages_count, chunks_count
        
    except Exception as e:
        print(f"Error processing PDF {filename}: {str(e)}")
        return False, f"Error processing PDF: {str(e)}", 0, 0

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    global current_files, history
    groq_key = get_groq_api_key()
    _, emb_name = get_embeddings()
    available_models = get_available_models()
    
    return jsonify({
        'has_file': len(current_files) > 0,
        'files': current_files,
        'total_files': len(current_files),
        'has_api_key': bool(groq_key),
        'current_model': get_current_model(),
        'embedding_type': emb_name,
        'supported_models': available_models,
        'history_count': len(history)
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    global current_files
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part in request'})
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file format. Please upload a .pdf file.'})
        
        display_name = file.filename
        safe_name = secure_filename(file.filename)
        if not safe_name or not safe_name.endswith('.pdf'):
            safe_name = f"doc_{int(time.time())}.pdf"
            
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
        file.save(file_path)
        
        file_size_bytes = os.path.getsize(file_path)
        file_size_str = format_file_size(file_size_bytes)
        
        # Only rebuild vector store if overwriting an existing document
        if any(f['name'] == safe_name for f in current_files):
            current_files = [f for f in current_files if f['name'] != safe_name]
            rebuild_vector_store()
        
        # Process newly saved PDF
        success, message, pages_count, chunks_count = process_pdf(file_path, safe_name)
        
        if success:
            file_meta = {
                'name': safe_name,
                'display_name': display_name,
                'pages': pages_count,
                'chunks': chunks_count,
                'size': file_size_str
            }
            current_files.append(file_meta)
            
            return jsonify({
                'success': True,
                'message': message,
                'file': file_meta,
                'total_files': len(current_files),
                'all_files': current_files
            })
        else:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            rebuild_vector_store()
            return jsonify({'success': False, 'error': message})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f"Upload failed: {str(e)}"})

@app.route('/ask', methods=['POST'])
def ask_question():
    global vector_store, history
    
    data = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()
    selected_model = data.get('model', '').strip() or get_current_model()
    
    if not question:
        return jsonify({'success': False, 'error': 'Please enter a valid question.'})
    
    if not current_files or vector_store is None:
        return jsonify({
            'success': False, 
            'error': 'No active PDF documents found. Please upload at least one PDF document before asking questions.'
        })
    
    groq_api_key = get_groq_api_key()
    if not groq_api_key:
        return jsonify({
            'success': False,
            'needs_api_key': True,
            'error': 'Groq API Key is missing or not configured. Please create a key at console.groq.com and paste it in Settings.'
        })
    
    try:
        start_time = time.time()
        # Retrieve top relevant context chunks
        k_val = min(8, max(4, len(current_files) * 3))
        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k_val})
        retrieved_docs = retriever.invoke(question)
        
        if not retrieved_docs:
            return jsonify({
                'success': True,
                'answer': "I could not find any relevant information in the uploaded PDF documents to answer your question.",
                'sources': [],
                'latency': 0.1,
                'model_used': selected_model,
                'chunks_count': 0,
                'follow_ups': []
            })
        
        # Build structured context and source citations
        context_parts = []
        sources = []
        for i, doc in enumerate(retrieved_docs, start=1):
            src_file = doc.metadata.get('source_file', 'Document')
            raw_page = doc.metadata.get('page', 0)
            page_num = raw_page + 1 if isinstance(raw_page, int) else 1
            snippet = doc.page_content.strip()
            
            context_parts.append(f"--- [Source {i}] File: {src_file} | Page: {page_num} ---\n{snippet}")
            sources.append({
                'id': i,
                'file': src_file,
                'page': page_num,
                'snippet': snippet[:220] + ("..." if len(snippet) > 220 else ""),
                'full_text': snippet
            })
            
        context_str = "\n\n".join(context_parts)
        
        # Build conversation history summary
        history_parts = []
        for msg in history[-6:]:
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_parts.append(f"{role}: {msg['content']}")
            
        history_str = "\n".join(history_parts) if history_parts else "No previous conversation."
        
        prompt_template = PromptTemplate(
            template="""You are an expert AI Document Research Assistant.
Answer the user's question accurately, thoroughly, and comprehensively based on the provided PDF context and conversation history.

Context from Uploaded PDFs:
{context}

Conversation History:
{history}

User Question: {question}

Instructions:
1. Provide a detailed, well-structured answer using facts from the Context above.
2. Format your response with clean Markdown (headings, bullet points, bold key terms, tables where helpful).
3. Cite the source document name and page number when referencing information (e.g. `[Document: filename.pdf, Page X]`).
4. At the very end of your response, provide exactly 3 intelligent, highly specific follow-up questions the user might want to ask next based on this document, formatted EXACTLY like this:
---FOLLOW_UPS---
- First specific follow-up question?
- Second specific follow-up question?
- Third specific follow-up question?

Answer:""",
            input_variables=["context", "history", "question"]
        )
        
        formatted_prompt = prompt_template.format(
            context=context_str,
            history=history_str,
            question=question
        )
        
        available_models = get_available_models()
        models_to_try = [selected_model] + [m for m in available_models if m != selected_model]
        
        last_error = None
        answer_text = None
        actual_model_used = selected_model
        follow_ups = []
        
        for model_name in models_to_try:
            try:
                llm = ChatGroq(
                    model=model_name,
                    temperature=0.3,
                    groq_api_key=groq_api_key,
                    max_retries=1
                )
                response = llm.invoke(formatted_prompt)
                raw_answer = response.content.strip()
                
                cleaned_answer = re.sub(r'<think>.*?</think>', '', raw_answer, flags=re.DOTALL).strip()
                
                # Parse ---FOLLOW_UPS--- from the output
                if "---FOLLOW_UPS---" in cleaned_answer:
                    parts = cleaned_answer.split("---FOLLOW_UPS---")
                    answer_text = parts[0].strip()
                    follow_up_lines = parts[1].strip().split("\n")
                    for line in follow_up_lines:
                        cleaned_line = re.sub(r'^[-*•\d\.\s]+', '', line).strip()
                        if cleaned_line and len(cleaned_line) > 5 and "?" in cleaned_line:
                            follow_ups.append(cleaned_line)
                else:
                    answer_text = cleaned_answer
                    
                actual_model_used = model_name
                break
            except Exception as model_err:
                last_error = model_err
                err_str = str(model_err).lower()
                if "invalid api key" in err_str or "unauthorized" in err_str or "401" in err_str:
                    return jsonify({
                        'success': False,
                        'needs_api_key': True,
                        'error': 'Invalid Groq API Key. Please create a new key at console.groq.com and update it in Settings.'
                    })
                continue
        
        if answer_text is None:
            return jsonify({
                'success': False,
                'error': f"Failed to get response from Groq LLM: {str(last_error)}"
            })
            
        latency = round(time.time() - start_time, 2)
        history.append({'role': 'user', 'content': question})
        history.append({'role': 'assistant', 'content': answer_text})
        
        # Fallback follow-ups if model didn't provide 3 questions
        if len(follow_ups) < 2:
            follow_ups = [
                f"Can you elaborate in more detail on {question[:35]}...?",
                "What are the main risks, limitations, or best practices mentioned in the text?",
                "Can you organize these insights into a structured comparison table?"
            ]
        else:
            follow_ups = follow_ups[:3]
        
        return jsonify({
            'success': True,
            'answer': answer_text,
            'sources': sources,
            'latency': latency,
            'model_used': actual_model_used,
            'chunks_count': len(retrieved_docs),
            'follow_ups': follow_ups
        })
        
    except Exception as e:
        print(f"Error during question answering: {str(e)}")
        return jsonify({'success': False, 'error': f"An error occurred: {str(e)}"})

@app.route('/delete-file', methods=['POST'])
def delete_file():
    global current_files
    data = request.get_json(silent=True) or {}
    filename = data.get('filename', '').strip()
    
    if not filename:
        return jsonify({'success': False, 'error': 'No filename provided.'})
        
    matching = [f for f in current_files if f['name'] == filename]
    if not matching:
        return jsonify({'success': False, 'error': f"File '{filename}' not found."})
        
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            
    current_files = [f for f in current_files if f['name'] != filename]
    rebuild_vector_store()
    
    return jsonify({
        'success': True,
        'message': f"File '{filename}' deleted successfully.",
        'total_files': len(current_files),
        'all_files': current_files
    })

@app.route('/clear-history', methods=['POST'])
def clear_history():
    global history
    history = []
    return jsonify({'success': True, 'message': 'Conversation history cleared successfully.'})

@app.route('/clear', methods=['POST'])
def clear_all():
    global current_files, vector_store, history
    
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass
                
        if vector_store is not None:
            try:
                vector_store.delete_collection()
            except Exception:
                pass
                
        current_files = []
        vector_store = None
        history = []
        
        return jsonify({'success': True, 'message': 'All documents and chat session cleared.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_elevenlabs_api_key():
    key = os.getenv('ELEVENLABS_API_KEY', '').strip()
    if not key:
        load_dotenv(override=True)
        key = os.getenv('ELEVENLABS_API_KEY', '').strip()
    return key

@app.route('/tts', methods=['POST'])
def generate_tts():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    voice = data.get('voice', 'en-US-AriaNeural').strip()
    
    if not text:
        return jsonify({'success': False, 'error': 'No text provided.'}), 400
        
    try:
        import requests as py_requests
        import edge_tts
        import asyncio
        
        # Clean markdown formatting so speech sounds completely natural
        clean_text = re.sub(r'[\*\_#\`~\[\]\(\)>]', ' ', text)
        clean_text = re.sub(r'http\S+', '', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        clean_text = clean_text[:3500]  # Cap length for instant playback
        
        if not clean_text:
            return jsonify({'success': False, 'error': 'No readable speech text.'}), 400

        # Handle ElevenLabs Studio Voices
        if voice.startswith('elevenlabs:'):
            voice_id = voice.replace('elevenlabs:', '').strip()
            elevenlabs_key = get_elevenlabs_api_key()
            
            if elevenlabs_key:
                try:
                    el_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                    el_headers = {
                        "xi-api-key": elevenlabs_key,
                        "Content-Type": "application/json"
                    }
                    el_payload = {
                        "text": clean_text[:2500],
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75
                        }
                    }
                    el_res = py_requests.post(el_url, json=el_payload, headers=el_headers, timeout=15)
                    if el_res.status_code == 200:
                        return Response(el_res.content, mimetype="audio/mpeg")
                    else:
                        print(f"ElevenLabs error ({el_res.status_code}): {el_res.text}")
                except Exception as el_err:
                    print(f"ElevenLabs request error: {el_err}, falling back to edge-tts.")
            
            # Fallback to natural neural voice if no ElevenLabs key configured
            voice = 'en-US-AriaNeural'

        # Microsoft Studio Neural Voice (100% Free)
        def fetch_audio():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                communicate = edge_tts.Communicate(clean_text, voice)
                async def fetch_all():
                    audio_data = bytearray()
                    async for chunk in communicate.stream():
                        if chunk['type'] == 'audio':
                            audio_data.extend(chunk['data'])
                    return bytes(audio_data)
                return loop.run_until_complete(fetch_all())
            finally:
                loop.close()
                
        audio_bytes = fetch_audio()
        return Response(audio_bytes, mimetype="audio/mpeg")
    except Exception as e:
        print(f"TTS Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
def handle_config():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    if request.method == 'GET':
        groq_key = get_groq_api_key()
        masked_key = ""
        if groq_key:
            masked_key = groq_key[:7] + "..." + groq_key[-4:] if len(groq_key) > 12 else "***"
            
        el_key = get_elevenlabs_api_key()
        masked_el_key = ""
        if el_key:
            masked_el_key = el_key[:6] + "..." + el_key[-4:] if len(el_key) > 10 else "***"
            
        return jsonify({
            'has_groq_key': bool(groq_key),
            'masked_key': masked_key,
            'has_elevenlabs_key': bool(el_key),
            'masked_elevenlabs_key': masked_el_key,
            'current_model': get_current_model(),
            'supported_models': get_available_models()
        })
        
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        new_key = data.get('groq_api_key', '').strip()
        new_model = data.get('model', '').strip()
        new_el_key = data.get('elevenlabs_api_key', '').strip()
        
        env_lines = {}
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            env_lines[k.strip()] = v.strip().strip('"').strip("'")
            except Exception as read_err:
                print(f"Could not read .env: {read_err}")
                        
        if new_key:
            env_lines['GROQ_API_KEY'] = new_key
            os.environ['GROQ_API_KEY'] = new_key
            
        if new_model:
            env_lines['GROQ_MODEL'] = new_model
            os.environ['GROQ_MODEL'] = new_model
            
        if new_el_key:
            env_lines['ELEVENLABS_API_KEY'] = new_el_key
            os.environ['ELEVENLABS_API_KEY'] = new_el_key
            
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                for k, v in env_lines.items():
                    f.write(f'{k} = "{v}"\n')
        except Exception as write_err:
            print(f"Serverless mode: cannot write .env to disk ({write_err}). Variables updated in-memory.")
                
        load_dotenv(override=True)
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully!',
            'current_model': get_current_model(),
            'has_groq_key': bool(get_groq_api_key()),
            'has_elevenlabs_key': bool(get_elevenlabs_api_key())
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting AI PDF Reader Flask App on port {port} ...")
    app.run(host='0.0.0.0', port=port, debug=False)