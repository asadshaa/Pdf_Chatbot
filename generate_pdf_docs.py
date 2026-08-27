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
    """Adds running headers and 'Page X of Y' footers across all pages."""
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
        # Suppress on page 1 (cover)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#4F46E5"))
            self.drawString(54, 11 * 72 - 36, "CogniPDF AI — System Architecture & Technical Documentation")
            
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(8.5 * 72 - 54, 11 * 72 - 36, "Enterprise RAG Workspace")

            # Top divider
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

            # Bottom footer
            self.line(54, 45, 8.5 * 72 - 54, 45)
            self.setFont("Helvetica", 8)
            self.drawString(54, 32, "CogniPDF AI — Confidential & Technical Reference Guide")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(8.5 * 72 - 54, 32, page_text)
        self.restoreState()

def build_pdf(filename="CogniPDF_AI_System_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Harmonious Executive Color Palette
    primary_color = colors.HexColor("#0F172A")    # Deep Slate / Navy
    accent_indigo = colors.HexColor("#4F46E5")    # Vibrant Modern Indigo
    accent_teal = colors.HexColor("#0D9488")      # Teal for Highlights
    text_dark = colors.HexColor("#1E293B")        # High-contrast readable text
    text_muted = colors.HexColor("#64748B")       # Secondary text
    bg_light = colors.HexColor("#F8FAFC")         # Clean table row background
    bg_callout = colors.HexColor("#EEF2F6")       # Callout box background
    border_color = colors.HexColor("#E2E8F0")     # Subtle divider lines

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11.5,
        leading=15,
        textColor=accent_indigo,
        spaceAfter=10
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=text_muted,
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=17,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=accent_indigo,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.5,
        textColor=text_dark,
        leftIndent=12,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=primary_color
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

    # =========================================================================
    # Header & Cover Title
    # =========================================================================
    story.append(Paragraph("CogniPDF AI", title_style))
    story.append(Paragraph("Enterprise Multi-Document Research & Neural Voice Workspace", subtitle_style))
    story.append(Paragraph("<b>System Documentation & Technical Guide</b> &nbsp;|&nbsp; <b>Version:</b> 2.4.0 &nbsp;|&nbsp; <b>Stack:</b> Flask / Groq / ChromaDB", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_indigo, spaceAfter=10))

    # =========================================================================
    # 1. Executive Overview (Plain English)
    # =========================================================================
    story.append(Paragraph("1. Overview & What This Application Does", h1_style))
    story.append(Paragraph(
        "<b>CogniPDF AI</b> is an intelligent document assistant that lets you upload one or multiple PDF documents "
        "(such as research papers, user manuals, financial reports, legal contracts, or scanned paper forms) and ask questions "
        "about them in natural human language.",
        body_style
    ))
    story.append(Paragraph(
        "Instead of reading through hundreds of pages manually, CogniPDF instantly searches across all your files, pulls out the exact "
        "relevant passages, and uses state-of-the-art Artificial Intelligence to write clear, direct answers with page citations. "
        "You can type your questions or use your voice, and you can listen to the answers read aloud like an audiobook.",
        body_style
    ))

    # Callout Highlight Box
    callout_data = [[Paragraph(
        "💡 <b>Key Benefit:</b> Built on a modern <b>RAG (Retrieval-Augmented Generation)</b> architecture, "
        "the AI never makes up facts or hallucinates. It answers questions strictly grounded in the content of your uploaded PDFs "
        "and provides exact clickable page references.",
        callout_style
    )]]
    t_callout = Table(callout_data, colWidths=[504])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_callout),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_callout)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 2. How the System Works from Start to End (Simple Plain English)
    # =========================================================================
    story.append(Paragraph("2. How the System Works (End-to-End Flow)", h1_style))
    story.append(Paragraph(
        "The application processes your documents in six simple, automated stages:",
        body_style
    ))

    flow_steps = [
        ("Step 1: Document Ingestion (The Eyes)", 
         "When you upload a PDF, the app reads the text in sub-milliseconds using <b>PyMuPDF</b>. If the document is a scanned image or photo with no digital text, the built-in <b>RapidOCR</b> engine scans the image like human eyes and extracts the printed words."),
        
        ("Step 2: Slicing into Paragraphs (The Slicer)", 
         "An AI cannot read a 500-page book all at once. The app cuts the document into bite-sized chunks (~1,000 characters each, with a 200-character overlap so sentences aren't cut mid-thought). Each piece is labeled with its exact <b>File Name</b> and <b>Page Number</b>."),
        
        ("Step 3: Converting Words to Meaning (The Translator)", 
         "The app uses a dense embedding model (<b>all-MiniLM-L6-v2</b>) running locally on your computer. It converts each text chunk into a list of mathematical numbers (vectors) that represent the <i>concept and meaning</i> of the words."),
        
        ("Step 4: Storing in Memory (The Memory Vault)", 
         "These numerical representations are stored inside <b>ChromaDB</b> (an in-memory vector database). This allows the system to search by topic and meaning (for example, finding 'revenue' when you ask about 'income or profits')."),
        
        ("Step 5: Reasoning & Synthesizing the Answer (The Brain)", 
         "When you ask a question (via text or microphone), the app pulls the <b>top 5 to 8 most relevant paragraphs</b> from ChromaDB and passes them to <b>llama-3.3-70b-versatile on Groq LPUs</b>. The AI reads those pieces and writes a clear answer with exact citations and 3 smart follow-up suggestions in less than one second."),
        
        ("Step 6: Voice Playback (The Voice)", 
         "When you click 'Read Aloud', <b>Microsoft Neural Speech (Edge-TTS)</b> or <b>ElevenLabs</b> turns the written answer into human-like audio and plays it instantly.")
    ]

    for step_title, step_desc in flow_steps:
        story.append(Paragraph(f"• <b>{step_title}:</b> {step_desc}", bullet_style))

    story.append(Spacer(1, 10))

    # =========================================================================
    # 3. AI Models Reference & Plain English Purpose
    # =========================================================================
    story.append(Paragraph("3. AI Models & Tools Reference", h1_style))
    story.append(Paragraph(
        "Here is a simple summary of every model and tool used in the application and its exact purpose:",
        body_style
    ))

    models_data = [
        [Paragraph("Role / Model", table_header), Paragraph("Category", table_header), Paragraph("Provider", table_header), Paragraph("Plain English Purpose", table_header)],
        [
            Paragraph("<b>llama-3.3-70b-versatile</b><br/><font color='#64748B' size='7'>The Main Brain</font>", table_cell),
            Paragraph("Reasoning LLM", table_cell),
            Paragraph("Meta / Groq", table_cell),
            Paragraph("The primary intelligence engine. Reads retrieved passages, writes accurate answers, generates exact citations, and suggests follow-up questions.", table_cell)
        ],
        [
            Paragraph("<b>groq/compound-mini</b><br/><font color='#64748B' size='7'>Fast Summarizer</font>", table_cell),
            Paragraph("Ultra-Fast LLM", table_cell),
            Paragraph("Groq", table_cell),
            Paragraph("Ultra-low-latency model for instant executive summaries and quick prompt chips.", table_cell)
        ],
        [
            Paragraph("<b>openai/gpt-oss-120b</b><br/><font color='#64748B' size='7'>Flagship Model</font>", table_cell),
            Paragraph("Deep Reasoning LLM", table_cell),
            Paragraph("Groq", table_cell),
            Paragraph("High-capacity model for complex cross-document comparisons and deep technical analysis.", table_cell)
        ],
        [
            Paragraph("<b>qwen/qwen3.6-27b</b><br/><font color='#64748B' size='7'>Math & Multilingual</font>", table_cell),
            Paragraph("Specialized LLM", table_cell),
            Paragraph("Qwen / Groq", table_cell),
            Paragraph("Specialized for mathematical calculations, tables, formulas, and non-English documents.", table_cell)
        ],
        [
            Paragraph("<b>all-MiniLM-L6-v2</b><br/><font color='#64748B' size='7'>The Meaning Model</font>", table_cell),
            Paragraph("Vector Embeddings", table_cell),
            Paragraph("Local ONNX", table_cell),
            Paragraph("Converts text into 384-dimensional math vectors for semantic search. Runs 100% locally and free with zero API charges.", table_cell)
        ],
        [
            Paragraph("<b>RapidOCR (PP-OCRv4)</b><br/><font color='#64748B' size='7'>Image Reader</font>", table_cell),
            Paragraph("Local OCR Engine", table_cell),
            Paragraph("ONNX Runtime", table_cell),
            Paragraph("Reads printed text from scanned PDFs and photos directly without third-party cloud fees.", table_cell)
        ],
        [
            Paragraph("<b>en-US-AriaNeural</b><br/><font color='#64748B' size='7'>The Voice</font>", table_cell),
            Paragraph("Neural TTS", table_cell),
            Paragraph("Microsoft", table_cell),
            Paragraph("Default natural, expressive voice for reading out AI answers clearly.", table_cell)
        ],
        [
            Paragraph("<b>ElevenLabs Multilingual</b><br/><font color='#64748B' size='7'>Studio Narrator</font>", table_cell),
            Paragraph("Voice Cloning", table_cell),
            Paragraph("ElevenLabs", table_cell),
            Paragraph("Optional hyper-realistic voice personalities (Rachel, Adam, Antoni, Bella) for audiobook-style playback.", table_cell)
        ]
    ]

    t_models = Table(models_data, colWidths=[115, 80, 75, 234])
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

    story.append(Spacer(1, 10))

    # =========================================================================
    # 4. Full Technology Stack Breakdown
    # =========================================================================
    story.append(Paragraph("4. Technology Stack Breakdown", h1_style))
    tech_items = [
        "<b>Backend Server:</b> Python 3.10+, Flask 3.1.3 (RESTful API architecture)",
        "<b>Production WSGI Server:</b> Gunicorn 26.2.0 (configured with <code>--workers 1 --threads 4 --timeout 120</code> for thread-safe vector state)",
        "<b>Concurrency & State Protection:</b> Python <code>threading.Lock()</code> mutex ensuring reliable uploads and deletions",
        "<b>RAG & AI Framework:</b> LangChain Core, LangChain Groq, and ChromaDB 1.5+ (In-Memory Vector Store)",
        "<b>Document Parsing:</b> PyMuPDF 1.28+ (C-accelerated fast text), pdfplumber 0.11+ (tables), pypdf 6.16+",
        "<b>Local OCR:</b> RapidOCR 1.4+ running on ONNX Runtime (zero cloud fees)",
        "<b>Speech Technologies:</b> edge-tts 7.2+, ElevenLabs API, and browser Web Speech API (Voice Dictation)",
        "<b>Frontend Interface:</b> Single Page Application (SPA) with Vanilla JavaScript and Modern Responsive CSS (Segmented Mobile Tab Controls for phones and tablets)"
    ]
    for item in tech_items:
        story.append(Paragraph(f"• {item}", bullet_style))

    story.append(Spacer(1, 10))

    # =========================================================================
    # 5. REST API Endpoints Reference
    # =========================================================================
    story.append(Paragraph("5. REST API Endpoints Reference", h1_style))
    
    api_data = [
        [Paragraph("Endpoint", table_header), Paragraph("Method", table_header), Paragraph("Payload", table_header), Paragraph("What It Does", table_header)],
        [Paragraph("<b>/status</b>", table_cell_bold), Paragraph("GET", table_cell), Paragraph("None", table_cell), Paragraph("Checks system health, loaded documents, page counts, chunk counts, and Groq status.", table_cell)],
        [Paragraph("<b>/upload</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("multipart/form-data", table_cell), Paragraph("Ingests a PDF, runs text/OCR extraction, splits into chunks, embeds, and stores in ChromaDB.", table_cell)],
        [Paragraph("<b>/ask</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("JSON {question, model}", table_cell), Paragraph("Performs semantic search, sends relevant context to Groq LLM, and returns answer + citations.", table_cell)],
        [Paragraph("<b>/tts</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("JSON {text, voice}", table_cell), Paragraph("Generates and streams an MP3 audio file of the answer for voice playback.", table_cell)],
        [Paragraph("<b>/delete-file</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("JSON {filename}", table_cell), Paragraph("Removes a specific PDF from disk and deletes its vector embeddings from ChromaDB.", table_cell)],
        [Paragraph("<b>/clear</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("None", table_cell), Paragraph("Clears all uploaded PDFs, resets the vector database, and wipes chat memory.", table_cell)],
        [Paragraph("<b>/clear-history</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("None", table_cell), Paragraph("Clears the chat conversation history without deleting your uploaded documents.", table_cell)],
        [Paragraph("<b>/update-config</b>", table_cell_bold), Paragraph("POST", table_cell), Paragraph("JSON {api_key, model}", table_cell), Paragraph("Saves a new Groq API key or changes the active default model in runtime.", table_cell)]
    ]

    t_api = Table(api_data, colWidths=[85, 45, 110, 264])
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

    # =========================================================================
    # 6. Quick Setup & Deployment Guide
    # =========================================================================
    story.append(Paragraph("6. Quick Setup & Deployment Guide", h1_style))
    story.append(Paragraph(
        "<b>Environment Configuration (<code>.env</code> file):</b><br/>"
        "• <code>GROQ_API_KEY = gsk_your_groq_key_here</code> (Get free key at <font color='#4F46E5'>console.groq.com</font>)<br/>"
        "• <code>GROQ_MODEL = llama-3.3-70b-versatile</code><br/>"
        "• <code>ELEVENLABS_API_KEY = optional_key</code> (Optional for studio voice cloning)",
        body_style
    ))
    story.append(Paragraph(
        "<b>Running Locally:</b><br/>"
        "1. Install packages: <code>pip install -r requirements.txt</code><br/>"
        "2. Start server: <code>python app.py</code><br/>"
        "3. Open in browser: <b>http://127.0.0.1:5000</b><br/><br/>"
        "<b>Deploying on Render Cloud:</b><br/>"
        "• <b>Build Command:</b> <code>pip install -r requirements.txt</code><br/>"
        "• <b>Start Command:</b> <code>gunicorn app:app --workers 1 --threads 4 --timeout 120</code><br/>"
        "• <b>Environment Variable:</b> Set <code>GROQ_API_KEY</code> in Render's Environment tab.",
        body_style
    ))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Professional PDF Documentation successfully built: {filename}")

if __name__ == "__main__":
    out_name = os.path.join(os.path.dirname(__file__), "CogniPDF_AI_System_Documentation.pdf")
    build_pdf(out_name)
