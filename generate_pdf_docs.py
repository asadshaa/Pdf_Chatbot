import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        # Suppress on first page (cover)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#4F46E5"))
            self.drawString(54, 11 * 72 - 36, "CogniPDF AI — System Architecture & Technical Documentation")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(8.5 * 72 - 54, 11 * 72 - 36, "Enterprise RAG System")

            # Top divider rule
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

            # Bottom footer rule
            self.line(54, 45, 8.5 * 72 - 54, 45)
            self.setFont("Helvetica", 8)
            self.drawString(54, 32, "Confidential — For Internal & Technical Use Only")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(8.5 * 72 - 54, 32, page_text)
        self.restoreState()

def build_pdf(filename="CogniPDF_AI_Technical_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1E1B4B")
    accent_indigo = colors.HexColor("#4F46E5")
    text_dark = colors.HexColor("#0F172A")
    text_muted = colors.HexColor("#475569")
    bg_light = colors.HexColor("#F8FAFC")
    border_color = colors.HexColor("#E2E8F0")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=accent_indigo,
        spaceAfter=14
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_muted,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=accent_indigo,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_dark,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_dark,
        leftIndent=14,
        spaceAfter=4
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=text_dark
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=primary_color
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # Title Banner Box
    story.append(Paragraph("CogniPDF AI", title_style))
    story.append(Paragraph("Enterprise Multi-Document RAG & Neural Voice Assistant — Master Technical Documentation", subtitle_style))
    story.append(Paragraph("<b>Version:</b> 2.4.0 &nbsp;|&nbsp; <b>Framework:</b> Flask / LangChain / Groq &nbsp;|&nbsp; <b>Date:</b> August 2026", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_indigo, spaceAfter=14))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "<b>CogniPDF AI</b> is a production-ready, multi-document <b>Retrieval-Augmented Generation (RAG)</b> application. "
        "It provides high-performance document ingestion, local vectorization, and sub-second natural language inference across "
        "heterogeneous PDF files (including native digital PDFs, scanned documents, contracts, scientific papers, and financial spreadsheets). "
        "The system incorporates local OCR fallbacks, local dense vector embeddings, sub-second LPU reasoning via Groq Cloud, "
        "and dual-engine neural speech synthesis.",
        body_style
    ))

    # 2. Architecture & Pipeline Workflow
    story.append(Paragraph("2. System Architecture & Ingestion Pipeline", h1_style))
    story.append(Paragraph(
        "The architecture is organized into four decoupled processing layers:",
        body_style
    ))

    steps = [
        "<b>1. Multi-Tier Ingestion & OCR:</b> Uploaded PDFs are parsed via <i>PyMuPDF (fitz)</i> for sub-millisecond text extraction. "
        "If a scanned image-only PDF is detected (zero text layer), the engine automatically triggers local <i>RapidOCR (ONNX Runtime)</i> to perform image character recognition.",
        "<b>2. Semantic Chunking:</b> Cleaned textual passages are partitioned using LangChain's <i>RecursiveCharacterTextSplitter</i> (chunk size = 1,000 characters, overlap = 200 characters).",
        "<b>3. Local Embedding & Vector Store:</b> Dense 384-dimensional vector representations are generated via <i>all-MiniLM-L6-v2</i> running on local ONNX Runtime (zero cloud embedding costs), and indexed into in-memory <i>ChromaDB</i> with metadata (filename, page number, chunk ID).",
        "<b>4. Retrieval & LLM Synthesis:</b> User queries undergo cosine similarity search. Top-K relevant contexts are injected into a structured system prompt dispatched to <i>Groq LPUs</i> for sub-second synthesis with exact source citations and 3 contextual follow-up questions.",
        "<b>5. Neural Speech Synthesis:</b> AI responses can be synthesized into studio-quality audio streams using Microsoft Neural Voices (Edge-TTS) or ElevenLabs."
    ]
    for s in steps:
        story.append(Paragraph(f"• {s}", bullet_style))

    story.append(Spacer(1, 10))

    # 3. AI Models & Purpose Table
    story.append(Paragraph("3. AI Models & Purpose Reference", h1_style))
    
    models_data = [
        [Paragraph("Model Name", table_header), Paragraph("Category", table_header), Paragraph("Provider", table_header), Paragraph("Role & Purpose", table_header)],
        [
            Paragraph("<b>llama-3.3-70b-versatile</b>", table_cell_bold),
            Paragraph("LLM (Reasoning)", table_cell),
            Paragraph("Meta / Groq", table_cell),
            Paragraph("Primary reasoning engine. Synthesizes answers, quotes exact passages, and generates citations.", table_cell)
        ],
        [
            Paragraph("<b>groq/compound-mini</b>", table_cell_bold),
            Paragraph("LLM (Fast)", table_cell),
            Paragraph("Groq", table_cell),
            Paragraph("Ultra-low latency reasoning model for quick summaries and quick prompt chips.", table_cell)
        ],
        [
            Paragraph("<b>openai/gpt-oss-120b</b>", table_cell_bold),
            Paragraph("LLM (Flagship)", table_cell),
            Paragraph("Groq", table_cell),
            Paragraph("Flagship open-weight model for complex document comparisons and multi-document reasoning.", table_cell)
        ],
        [
            Paragraph("<b>qwen/qwen3.6-27b</b>", table_cell_bold),
            Paragraph("LLM (Math/Multi)", table_cell),
            Paragraph("Qwen / Groq", table_cell),
            Paragraph("Multilingual & mathematical reasoning across technical formulas and foreign language texts.", table_cell)
        ],
        [
            Paragraph("<b>all-MiniLM-L6-v2</b>", table_cell_bold),
            Paragraph("Embedding (384-dim)", table_cell),
            Paragraph("ONNX / Local", table_cell),
            Paragraph("Local semantic vectorization model. Generates dense embeddings offline with zero API cost.", table_cell)
        ],
        [
            Paragraph("<b>nomic-embed-text-v1.5</b>", table_cell_bold),
            Paragraph("Embedding (768-dim)", table_cell),
            Paragraph("Nomic AI", table_cell),
            Paragraph("Optional cloud vector embedding with 8,192-token context window for long documents.", table_cell)
        ],
        [
            Paragraph("<b>RapidOCR (PP-OCRv4)</b>", table_cell_bold),
            Paragraph("OCR Engine", table_cell),
            Paragraph("ONNX Runtime", table_cell),
            Paragraph("Extracts text from scanned/image-only PDFs locally without external cloud API charges.", table_cell)
        ],
        [
            Paragraph("<b>en-US-AriaNeural</b>", table_cell_bold),
            Paragraph("Neural TTS", table_cell),
            Paragraph("Microsoft", table_cell),
            Paragraph("Default studio-quality neural voice for hands-free audio playback.", table_cell)
        ],
        [
            Paragraph("<b>ElevenLabs Multilingual v2</b>", table_cell_bold),
            Paragraph("Voice Cloning", table_cell),
            Paragraph("ElevenLabs", table_cell),
            Paragraph("Optional hyper-realistic voice personalities for custom narration.", table_cell)
        ]
    ]

    t_models = Table(models_data, colWidths=[120, 85, 75, 224])
    t_models.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), accent_indigo),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light])
    ]))
    story.append(t_models)

    story.append(Spacer(1, 12))

    # 4. Tech Stack Breakdown
    story.append(Paragraph("4. Complete Technology Stack", h1_style))
    tech_bullets = [
        "<b>Backend Framework:</b> Flask 3.1.3 (REST API), Werkzeug 3.1.8",
        "<b>Production WSGI Server:</b> Gunicorn 26.2.0 (Configured with <code>--workers 1 --threads 4 --timeout 120</code> for synchronized thread-safe state)",
        "<b>RAG Pipeline:</b> LangChain 0.1+, LangChain Groq, ChromaDB 1.5+ (In-Memory Vector DB)",
        "<b>Concurrency Control:</b> Python <code>threading.Lock()</code> mutex protecting parallel upload/delete transactions",
        "<b>PDF Extraction:</b> PyMuPDF 1.28+ (C-accelerated), pdfplumber 0.11+, pypdf 6.16+",
        "<b>Local OCR Engine:</b> RapidOCR 1.4+ (ONNX Runtime, PP-OCRv4 model)",
        "<b>Speech Synthesis:</b> edge-tts 7.2+, ElevenLabs REST API, Web Speech API (Browser Voice Dictation)",
        "<b>Frontend:</b> Vanilla HTML5 / ES6+ JavaScript / Modern CSS Design Tokens (Segmented Mobile Tab Navigation)",
        "<b>Markdown & Code Highlighting:</b> Marked.js with Highlight.js"
    ]
    for tb in tech_bullets:
        story.append(Paragraph(f"• {tb}", bullet_style))

    story.append(Spacer(1, 10))

    # 5. REST API Endpoints Table
    story.append(Paragraph("5. REST API Endpoints Reference", h1_style))
    api_data = [
        [Paragraph("Endpoint", table_header), Paragraph("Method", table_header), Paragraph("Payload", table_header), Paragraph("Description", table_header)],
        [Paragraph("<b>/status</b>", table_cell_bold), Paragraph("GET", table_cell), Paragraph("None", table_cell), Paragraph("Returns system health, document list, page/chunk stats, and Groq status.", table_cell)],
        [Paragraph("<b>/upload</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("multipart/form-data", table_cell), Paragraph("Ingests, parses, chunks, embeds, and indexes a PDF document into ChromaDB.", table_cell)],
        [Paragraph("<b>/ask</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("JSON {question, model}", table_cell), Paragraph("Performs Top-K search and returns answer with citations, latency, and follow-ups.", table_cell)],
        [Paragraph("<b>/tts</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("JSON {text, voice}", table_cell), Paragraph("Generates and streams high-fidelity MP3 neural audio.", table_cell)],
        [Paragraph("<b>/delete-file</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("JSON {filename}", table_cell), Paragraph("Removes document and purges its vector embeddings from ChromaDB.", table_cell)],
        [Paragraph("<b>/clear</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("None", table_cell), Paragraph("Purges all documents, resets vector store, and clears chat history.", table_cell)],
        [Paragraph("<b>/clear-history</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("None", table_cell), Paragraph("Resets conversational memory without deleting indexed documents.", table_cell)],
        [Paragraph("<b>/update-config</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("JSON {api_key, model}", table_cell), Paragraph("Dynamically updates runtime Groq API Key and default model.", table_cell)]
    ]
    t_api = Table(api_data, colWidths=[90, 50, 110, 254])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light])
    ]))
    story.append(t_api)

    story.append(Spacer(1, 10))

    # 6. Deployment & Environment Configuration
    story.append(Paragraph("6. Setup & Deployment Guide", h1_style))
    story.append(Paragraph(
        "<b>Environment Variables (.env):</b><br/>"
        "<code>GROQ_API_KEY = gsk_your_key_here</code> &nbsp;|&nbsp; "
        "<code>GROQ_MODEL = llama-3.3-70b-versatile</code> &nbsp;|&nbsp; "
        "<code>ELEVENLABS_API_KEY = optional_key</code>",
        body_style
    ))
    story.append(Paragraph(
        "<b>Local Execution:</b><br/>"
        "1. <code>pip install -r requirements.txt</code><br/>"
        "2. <code>python app.py</code> (Server runs at http://127.0.0.1:5000)<br/>"
        "<b>Render Cloud Production:</b><br/>"
        "• Start Command: <code>gunicorn app:app --workers 1 --threads 4 --timeout 120</code><br/>"
        "• Build Command: <code>pip install -r requirements.txt</code>",
        body_style
    ))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF documentation successfully built: {filename}")

if __name__ == "__main__":
    out_name = os.path.join(os.path.dirname(__file__), "CogniPDF_AI_System_Documentation.pdf")
    build_pdf(out_name)
