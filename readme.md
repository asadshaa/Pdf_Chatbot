# 🧠 CogniPDF AI — Enterprise Multi-PDF Research & Neural Voice Assistant

An enterprise-grade, multi-document **Retrieval-Augmented Generation (RAG)** application built with **Flask**, **LangChain**, **Groq LPUs**, **ChromaDB**, **RapidOCR**, and **Neural Speech Synthesis (Edge-TTS + ElevenLabs)**.

CogniPDF allows users to upload multiple PDF documents simultaneously—including scanned/image documents—index their contents into a local semantic vector store, and interact via chat and voice with source citations, passage inspection, and follow-up generation.

---

## ✨ Features

- 📄 **Multi-Engine PDF & Local OCR Extraction**:
  - **Tier 1**: Microsecond text extraction via `PyMuPDF (fitz)`.
  - **Tier 2**: Stream table parsing with `pdfplumber`.
  - **Tier 3 (OCR Fallback)**: Automatically runs `RapidOCR (ONNX Runtime)` on image-only scanned PDFs without external cloud fees.
- ⚡ **Local Semantic Embeddings**: Powered by ChromaDB's ONNX-based `all-MiniLM-L6-v2` (runs 100% locally and free, zero embedding API keys required).
- 🤖 **Sub-Second Groq LLM Reasoning**: Powered by `llama-3.3-70b-versatile`, `groq/compound-mini`, `openai/gpt-oss-120b`, and `qwen/qwen3.6-27b`.
- 📑 **Interactive Source Citation Inspector**: Click any citation tag to open a slide-out frosted glass drawer showing the exact extracted passage, page preview, and copy action.
- 🎙️ **Dual-Engine Speech Synthesis**:
  - **100% Free & Unlimited**: Microsoft Studio Neural Voices (*Aria, Guy, Jenny, Christopher, Sonia, Ryan*).
  - **Hyper-Realistic Studio**: ElevenLabs API integration (*Rachel, Adam, Antoni, Bella, Josh*).
- 🎙️ **Voice Dictation (Speech-to-Text)**: Hands-free microphone input using native Web Speech recognition.
- 💡 **Dynamic Smart Follow-Up Question Chips**: The LLM automatically generates 3 contextual follow-up questions tailored to your document.
- 📥 **Research Session Export Suite**: One-click download of your entire conversation history as a formatted Markdown (`.md`) report.
- 🎨 **Ambient Aurora Fluid Mesh UI**: Hardware-accelerated fluid orbs, frosted glassmorphism, instant 60/120 FPS light/dark mode switcher, and interactive mouse parallax spotlight.
- 🗑️ **Granular Document Management**: Delete individual files or clear the entire workspace session with one click.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask, Werkzeug
- **RAG & Orchestration**: LangChain, ChromaDB
- **LLM Engine**: Groq Cloud LPUs (`llama-3.3-70b-versatile`)
- **PDF & OCR**: `PyMuPDF`, `pdfplumber`, `rapidocr-onnxruntime`
- **Voice Synthesis**: `edge-tts`, ElevenLabs API, Web Speech API
- **Frontend**: Vanilla CSS (Glassmorphism & Native View Transitions), JavaScript (ES6+), `marked.js`, `highlight.js`

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/asadshaa/Pdf_Chatbot.git
cd Pdf_Chatbot
```

### 2. Configure Environment Variables
Create a `.env` file in the root folder (or use `.env.example`):

```env
GROQ_API_KEY = "your_groq_api_key_here"
GROQ_MODEL = "llama-3.3-70b-versatile"
ELEVENLABS_API_KEY = "optional_elevenlabs_key_here"
```

> **Note:** You can get a free Groq API key at [Groq Console](https://console.groq.com/keys). API keys can also be configured directly in the in-app Settings modal.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Flask Server
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📁 Project Structure

```
├── app.py                  # Main Flask application and RAG pipeline
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore configuration
├── uploads/                # Directory for uploaded PDF documents
├── templates/
│   └── index.html          # Modern Ambient Glassmorphism SPA UI
└── README.md               # Project documentation
```

---

## 💡 How the Architecture Works

1. **Document Ingestion**: Uploaded PDFs are parsed via `PyMuPDF` or `RapidOCR` if scanned.
2. **Semantic Chunking**: `RecursiveCharacterTextSplitter` segments text into 1,000-character chunks with a 200-character overlap.
3. **Local Vectorization**: Chunks are embedded into 384-dimensional vectors with `all-MiniLM-L6-v2` and indexed in ChromaDB.
4. **Context Retrieval**: User queries perform Top-K Cosine Similarity search to extract the most relevant passages.
5. **LLM Synthesis**: Groq LPUs synthesize the answer with source citations and 3 intelligent follow-up questions.
6. **Voice Synthesis**: Text is converted to MP3 audio on the fly via `edge-tts` or ElevenLabs.
