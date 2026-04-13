"""
Generate a professional Word document (.docx) for the MedAssist.ai Detailed Project Report.
Includes a Table of Contents with page numbers, headers, footers, and formatted tables.
"""

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os

# ─── Helpers ────────────────────────────────────────────────────────────


def set_cell_shading(cell, color_hex):
    """Set the background color of a table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_table_row(table, cells_data, bold=False, header=False):
    """Add a row to a table with formatted cells."""
    row = table.add_row()
    for i, text in enumerate(cells_data):
        cell = row.cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(str(text))
        run.font.size = Pt(9.5)
        run.font.name = "Calibri"
        if bold or header:
            run.bold = True
        if header:
            set_cell_shading(cell, "7C3AED")
            run.font.color.rgb = RGBColor(255, 255, 255)
    return row


def format_table(table):
    """Apply professional formatting to a table."""
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Set borders
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '  <w:top w:val="single" w:sz="4" w:space="0" w:color="D4D4D4"/>'
        '  <w:left w:val="single" w:sz="4" w:space="0" w:color="D4D4D4"/>'
        '  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="D4D4D4"/>'
        '  <w:right w:val="single" w:sz="4" w:space="0" w:color="D4D4D4"/>'
        '  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="D4D4D4"/>'
        '  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="D4D4D4"/>'
        '</w:tblBorders>'
    )
    tblPr.append(borders)
    # Alternate row shading
    for i, row in enumerate(table.rows):
        if i > 0 and i % 2 == 0:
            for cell in row.cells:
                set_cell_shading(cell, "F5F3FF")


def add_heading(doc, text, level=1):
    """Add a heading with custom style."""
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
        if level == 1:
            run.font.size = Pt(22)
        elif level == 2:
            run.font.size = Pt(16)
        elif level == 3:
            run.font.size = Pt(13)
    return h


def add_body(doc, text):
    """Add a body paragraph."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(11)
    run.font.name = "Calibri"
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = Pt(16)
    return p


def add_bullet(doc, text, bold_prefix=None):
    """Add a bulleted list item, optionally with a bold prefix."""
    p = doc.add_paragraph(style="List Bullet")
    if bold_prefix:
        run_b = p.add_run(bold_prefix)
        run_b.bold = True
        run_b.font.size = Pt(10.5)
        run_b.font.name = "Calibri"
        run = p.add_run(text)
    else:
        run = p.add_run(text)
    run.font.size = Pt(10.5)
    run.font.name = "Calibri"
    return p


def add_diagram(doc, image_path, caption, width=Inches(5.5)):
    """Add a diagram image with a centered caption."""
    if os.path.exists(image_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(image_path, width=width)
        # Caption
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(caption)
        run.font.size = Pt(9)
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
        cap.paragraph_format.space_after = Pt(12)
    else:
        add_body(doc, f"[Diagram not found: {image_path}]")


def add_page_break(doc):
    doc.add_page_break()


def add_toc(doc):
    """Insert a Table of Contents field that Word will auto-generate."""
    p = doc.add_paragraph()
    run = p.add_run()
    fldChar1 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    run._r.append(fldChar1)

    run2 = p.add_run()
    instrText = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText>')
    run2._r.append(instrText)

    run3 = p.add_run()
    fldChar2 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>')
    run3._r.append(fldChar2)

    run4 = p.add_run("Right-click here and select 'Update Field' to generate Table of Contents with page numbers.")
    run4.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
    run4.font.size = Pt(10)
    run4.italic = True

    run5 = p.add_run()
    fldChar3 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
    run5._r.append(fldChar3)


def add_page_numbers(doc):
    """Add page numbers to footer."""
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.clear()

        run = p.add_run()
        fldChar1 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
        run._r.append(fldChar1)

        run2 = p.add_run()
        instrText = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve"> PAGE </w:instrText>')
        run2._r.append(instrText)

        run3 = p.add_run()
        fldChar2 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>')
        run3._r.append(fldChar2)

        run4 = p.add_run("1")
        run4.font.size = Pt(9)
        run4.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

        run5 = p.add_run()
        fldChar3 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
        run5._r.append(fldChar3)


# ─── Main Document Generation ──────────────────────────────────────────

def generate_report():
    doc = Document()

    # ── Page Setup ──
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # ── Set Default Font ──
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)

    # === TITLE PAGE ===
    for _ in range(6):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("MedAssist.ai")
    run.font.size = Pt(42)
    run.font.color.rgb = RGBColor(0x7C, 0x3A, 0xED)
    run.bold = True

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Smart Clinical Decision Support System")
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

    doc.add_paragraph()

    tagline = doc.add_paragraph()
    tagline.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = tagline.add_run("Detailed Project Report")
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    for _ in range(4):
        doc.add_paragraph()

    meta_lines = [
        "Project Type: Full-Stack AI-Powered Healthcare Web Application",
        "License: MIT License — Copyright © 2026 Zaid",
        "Runtime: Python 3.11.9",
        "Total Codebase: ~6,100 lines across 8 core source files",
    ]
    for line in meta_lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line)
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    add_page_break(doc)

    # === TABLE OF CONTENTS ===
    toc_heading = doc.add_heading("Table of Contents", level=1)
    for run in toc_heading.runs:
        run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
    add_toc(doc)
    add_page_break(doc)

    # === 1. ABSTRACT ===
    add_heading(doc, "1. Abstract")
    add_body(doc,
        "MedAssist.ai is an intelligent, AI-powered Clinical Decision Support System (CDSS) designed to bridge "
        "the gap between symptom onset and medical consultation. The platform enables users to input their symptoms "
        "through an intuitive, mobile-first interface and receive probabilistic disease predictions powered by a "
        "calibrated Random Forest machine learning model trained on a dataset of 4,920 medical records spanning "
        "41 diseases and 131 clinical symptoms."
    )
    add_body(doc,
        "Beyond diagnosis, the system integrates a Groq-powered Large Language Model (LLM) chatbot for conversational "
        "health guidance, a Geoapify-based hospital locator with disease-specific specialty matching, and a complete "
        "appointment booking system with automated email reminders. The platform achieves 98% Top-1 accuracy and "
        "100% Top-3 accuracy on independent test data, ensuring that the correct diagnosis is consistently presented "
        "within the top three predictions."
    )
    add_body(doc,
        "The application is deployed as a production-ready web service on Render, backed by a Neon PostgreSQL cloud "
        "database, and serves both authenticated users with full history tracking and guest users with a limited demo experience."
    )

    # === 2. INTRODUCTION ===
    add_heading(doc, "2. Introduction")
    add_body(doc,
        "Clinical Decision Support Systems (CDSS) are computer-based programs that assist healthcare professionals "
        "and patients in making informed clinical decisions. With the rising global burden of disease and the increasing "
        "shortage of healthcare professionals, there is a critical need for accessible, intelligent tools that can provide "
        "preliminary health assessments."
    )
    add_body(doc, "MedAssist.ai addresses this need by providing:")
    add_bullet(doc, " Users select their symptoms and receive ranked diagnoses with calibrated confidence scores within seconds.", "Instant Disease Prediction:")
    add_bullet(doc, " A conversational chatbot provides health education, lifestyle advice, and safety guidance.", "AI Health Consultation:")
    add_bullet(doc, " Location-based hospital search with intelligent specialty matching based on the diagnosed condition.", "Healthcare Facility Discovery:")
    add_bullet(doc, " End-to-end appointment booking with automated confirmation and reminder emails.", "Appointment Management:")
    add_body(doc,
        "The system is designed with a mobile-first, premium UI philosophy and implements modern web design principles "
        "including glassmorphism, micro-animations, and responsive layouts to provide an engaging and trustworthy user experience."
    )

    # === 3. PROBLEM STATEMENT ===
    add_heading(doc, "3. Problem Statement")
    add_body(doc,
        "In many regions, access to timely medical consultation is limited by factors including geographical distance, "
        "cost, and doctor availability. Patients often face the following challenges:"
    )
    add_bullet(doc, " Difficulty in understanding the significance of symptoms and whether immediate medical attention is required.", "Symptom Uncertainty:")
    add_bullet(doc, " Unreliable internet health searches that either cause unnecessary panic or dangerous complacency.", "Information Overload:")
    add_bullet(doc, " Lack of awareness about nearby healthcare facilities, especially those with relevant specializations.", "Hospital Discovery:")
    add_bullet(doc, " Complex booking processes and missed appointments due to lack of reminders.", "Appointment Friction:")
    add_body(doc,
        "MedAssist.ai aims to solve these problems through an integrated, AI-driven platform that provides reliable "
        "preliminary diagnosis, trustworthy health information, location-aware hospital discovery, and seamless appointment management."
    )

    # === 4. LITERATURE REVIEW ===
    add_heading(doc, "4. Literature Review")
    add_heading(doc, "4.1 Clinical Decision Support Systems", level=2)
    add_body(doc,
        "Modern CDSS platforms leverage machine learning to analyze patient data and provide diagnostic suggestions. "
        "Studies have shown that ensemble methods, particularly Random Forests, perform exceptionally well on structured "
        "medical tabular data due to their inherent ability to handle high-dimensional binary feature spaces and provide "
        "feature importance rankings (Breiman, 2001)."
    )
    add_heading(doc, "4.2 Random Forest for Disease Classification", level=2)
    add_body(doc,
        "Random Forests aggregate predictions from hundreds of independently trained decision trees, reducing variance "
        "and overfitting. For multi-class medical diagnosis with binary symptom vectors, this approach has been validated "
        "in numerous studies achieving >95% accuracy across diverse disease datasets (Uddin et al., 2019)."
    )
    add_heading(doc, "4.3 Probability Calibration", level=2)
    add_body(doc,
        "Standard Random Forest models produce poorly calibrated probability estimates — they tend to cluster predictions "
        "near 0 and 1 rather than reflecting true statistical likelihood. Calibration techniques such as Platt Scaling "
        "(sigmoid method) and Isotonic Regression correct this, ensuring confidence scores are clinically meaningful "
        "(Niculescu-Mizil & Caruana, 2005)."
    )
    add_heading(doc, "4.4 Large Language Models in Healthcare", level=2)
    add_body(doc,
        "The integration of LLMs (such as LLaMA-based models) as conversational health assistants allows for contextual, "
        "empathetic health guidance. When paired with structured diagnostic output, LLMs can translate clinical predictions "
        "into patient-friendly language, improving health literacy and reducing diagnostic anxiety."
    )

    # === 5. OBJECTIVES ===
    add_heading(doc, "5. Objectives")
    obj_table = doc.add_table(rows=1, cols=3)
    format_table(obj_table)
    add_table_row(obj_table, ["#", "Objective", "Status"], header=True)
    # Remove the auto-generated first empty row
    obj_table._tbl.remove(obj_table.rows[0]._tr)
    objectives = [
        ("1", "Build an ML model that predicts diseases from symptoms with ≥95% accuracy", "Achieved (98%)"),
        ("2", "Provide Top-3 ranked predictions with calibrated confidence scores", "Achieved (100% Top-3)"),
        ("3", "Integrate an AI chatbot for conversational health guidance", "Implemented"),
        ("4", "Implement location-based hospital search with specialty matching", "Implemented"),
        ("5", "Build an appointment booking system with automated email reminders", "Implemented"),
        ("6", "Design a mobile-first, premium UI with modern design language", "Implemented"),
        ("7", "Deploy as a production-ready web application", "Deployed on Render"),
        ("8", "Implement secure user authentication with email verification", "Implemented"),
    ]
    for obj in objectives:
        add_table_row(obj_table, obj)

    # === 6. SYSTEM ARCHITECTURE ===
    add_heading(doc, "6. System Architecture")
    add_heading(doc, "6.1 High-Level Architecture", level=2)
    add_body(doc,
        "The application follows a three-tier architecture with a clear separation between the client-side frontend, "
        "the Flask backend server, and external service integrations."
    )
    add_body(doc, "The system consists of the following layers:")
    add_bullet(doc, " HTML5/Jinja2 templates, Vanilla CSS (3,562 lines), Vanilla JavaScript (1,164 lines), Web Speech API", "Client Layer:")
    add_bullet(doc, " Flask application (701 lines), ML Module (train_model.py + predict.py), Flask-APScheduler", "Server Layer:")
    add_bullet(doc, " Groq Cloud LLM (llama-3.1-8b-instant), Geoapify Places API, Brevo REST API", "External Services:")
    add_bullet(doc, " Neon PostgreSQL (Cloud), Pickle files (ML model + features), CSV datasets", "Data Layer:")

    # Insert system architecture diagram
    diagram_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrams")
    add_diagram(doc, os.path.join(diagram_dir, "system_architecture.png"), "Figure 1: MedAssist.ai System Architecture")

    add_heading(doc, "6.2 Data Flow", level=2)
    add_body(doc,
        "1. User selects symptoms, age, and gender on the frontend.\n"
        "2. Frontend sends POST /api/predict to Flask backend.\n"
        "3. Backend invokes ML engine: normalizes input → fuzzy matches → builds feature vector → runs calibrated model.\n"
        "4. Backend returns Top-3 predictions with probabilities.\n"
        "5. Frontend auto-triggers disease-info (Groq LLM) and hospital search (Geoapify) in parallel.\n"
        "6. User can book appointments, which triggers confirmation email (Brevo).\n"
        "7. Background scheduler sends 12h and 1h reminder emails automatically."
    )

    # === 7. TECHNOLOGY STACK ===
    add_heading(doc, "7. Technology Stack")

    add_heading(doc, "7.1 Backend Technologies", level=2)
    be_table = doc.add_table(rows=1, cols=4)
    format_table(be_table)
    add_table_row(be_table, ["Technology", "Version", "Role", "Justification"], header=True)
    be_table._tbl.remove(be_table.rows[0]._tr)
    be_data = [
        ("Python", "3.11.9", "Core language", "Mature ML and web ecosystem"),
        ("Flask", "3.0.0", "Web framework", "Lightweight, API-driven architecture"),
        ("Flask-SQLAlchemy", "3.1.1", "ORM", "Pythonic database access"),
        ("Flask-APScheduler", "1.13.1", "Task scheduler", "In-process job scheduling"),
        ("Gunicorn", "21.2.0", "WSGI server", "Production multi-worker server"),
        ("psycopg2-binary", "2.9.9", "DB adapter", "PostgreSQL connectivity"),
        ("python-dotenv", "1.0.0", "Config", "Environment variable management"),
        ("requests", "2.31.0", "HTTP client", "External API calls"),
        ("groq", "1.1.1", "LLM SDK", "Groq Cloud API client"),
    ]
    for row in be_data:
        add_table_row(be_table, row)

    add_heading(doc, "7.2 Frontend Technologies", level=2)
    fe_table = doc.add_table(rows=1, cols=3)
    format_table(fe_table)
    add_table_row(fe_table, ["Technology", "Role", "Details"], header=True)
    fe_table._tbl.remove(fe_table.rows[0]._tr)
    fe_data = [
        ("HTML5 / Jinja2", "Templates", "4 template files, server-side rendered"),
        ("Vanilla CSS", "Design system", "3,562 lines with glassmorphism and design tokens"),
        ("Vanilla JavaScript", "Client logic", "1,164 lines: tabs, forms, API calls, speech"),
        ("Google Fonts", "Typography", "Outfit (headings) and Inter (body)"),
        ("Marked.js", "Markdown", "CDN-loaded parser for chatbot responses"),
        ("Web Speech API", "Voice I/O", "SpeechRecognition + SpeechSynthesis"),
    ]
    for row in fe_data:
        add_table_row(fe_table, row)

    add_heading(doc, "7.3 Machine Learning Stack", level=2)
    ml_table = doc.add_table(rows=1, cols=3)
    format_table(ml_table)
    add_table_row(ml_table, ["Technology", "Version", "Role"], header=True)
    ml_table._tbl.remove(ml_table.rows[0]._tr)
    ml_data = [
        ("scikit-learn", "1.3.2", "RandomForestClassifier, GridSearchCV, CalibratedClassifierCV"),
        ("pandas", "2.1.3", "Data loading, cleaning, and feature engineering"),
        ("pickle", "stdlib", "Model serialization and deserialization"),
        ("difflib", "stdlib", "Fuzzy string matching for symptom tolerance"),
        ("re", "stdlib", "Regex-based column normalization"),
    ]
    for row in ml_data:
        add_table_row(ml_table, row)

    add_heading(doc, "7.4 Infrastructure", level=2)
    infra_table = doc.add_table(rows=1, cols=3)
    format_table(infra_table)
    add_table_row(infra_table, ["Service", "Provider", "Role"], header=True)
    infra_table._tbl.remove(infra_table.rows[0]._tr)
    infra_data = [
        ("Web Hosting", "Render", "Cloud platform for Flask deployment"),
        ("Database", "Neon (Azure East US 2)", "Serverless PostgreSQL"),
        ("Email", "Brevo (Sendinblue)", "Transactional email delivery"),
        ("LLM", "Groq Cloud", "Ultra-fast LLM inference"),
        ("Geolocation", "Geoapify", "Hospital/clinic place search"),
    ]
    for row in infra_data:
        add_table_row(infra_table, row)

    # === 8. DATASET DESCRIPTION ===
    add_heading(doc, "8. Dataset Description")

    add_heading(doc, "8.1 Training Dataset", level=2)
    ds_table = doc.add_table(rows=1, cols=2)
    format_table(ds_table)
    add_table_row(ds_table, ["Property", "Value"], header=True)
    ds_table._tbl.remove(ds_table.rows[0]._tr)
    ds_data = [
        ("File", "dataset/training_data.csv"),
        ("Total Records", "4,920"),
        ("Total Columns", "141 (raw), 138 (after cleaning)"),
        ("Unique Diseases", "41"),
        ("Samples per Disease", "120 (perfectly balanced)"),
        ("Feature Type", "Binary (0/1) symptom indicators"),
    ]
    for row in ds_data:
        add_table_row(ds_table, row)

    add_heading(doc, "8.2 Feature Breakdown", level=2)
    fb_table = doc.add_table(rows=1, cols=3)
    format_table(fb_table)
    add_table_row(fb_table, ["Category", "Count", "Examples"], header=True)
    fb_table._tbl.remove(fb_table.rows[0]._tr)
    add_table_row(fb_table, ("Symptom features", "131", "itching, skin_rash, high_fever, chest_pain, fatigue"))
    add_table_row(fb_table, ("Age features", "4", "age_child, age_teenager, age_adult, age_senior"))
    add_table_row(fb_table, ("Gender features", "3", "gender_male, gender_female, gender_other"))
    add_table_row(fb_table, ("Target variable", "1", "prognosis (41 unique disease labels)"))

    add_heading(doc, "8.3 Disease Classes (All 41)", level=2)
    diseases = [
        "Fungal infection", "Allergy", "GERD", "Chronic cholestasis", "Drug Reaction",
        "Peptic ulcer diseae", "AIDS", "Diabetes", "Gastroenteritis", "Bronchial Asthma",
        "Hypertension", "Migraine", "Cervical spondylosis", "Paralysis (brain hemorrhage)",
        "Jaundice", "Malaria", "Chicken pox", "Dengue", "Typhoid", "hepatitis A",
        "Hepatitis B", "Hepatitis C", "Hepatitis D", "Hepatitis E", "Alcoholic hepatitis",
        "Tuberculosis", "Common Cold", "Pneumonia", "Dimorphic hemmorhoids(piles)",
        "Heart attack", "Varicose veins", "Hypothyroidism", "Hyperthyroidism", "Hypoglycemia",
        "Osteoarthristis", "Arthritis", "(vertigo) Paroymsal Positional Vertigo",
        "Acne", "Urinary tract infection", "Psoriasis", "Impetigo"
    ]
    disease_text = ", ".join(diseases)
    add_body(doc, disease_text)

    add_heading(doc, "8.4 Test Dataset", level=2)
    add_body(doc, "File: dataset/test_data.csv — 42 records covering all 41 disease classes (1 sample per disease + 1 extra).")

    add_heading(doc, "8.5 Data Preprocessing Pipeline", level=2)
    add_bullet(doc, " Drop unnamed index columns and duplicate 'fluid_overload.1' column", "Column Removal:")
    add_bullet(doc, " Regex-based normalization ([\\s_]+ → _) to handle inconsistent whitespace in original CSV headers", "Normalization:")
    add_bullet(doc, " Remove duplicate columns (post-normalization) and duplicate rows", "Deduplication:")
    add_bullet(doc, " Assert 'prognosis' target column exists", "Validation:")

    # === 9. MACHINE LEARNING METHODOLOGY ===
    add_heading(doc, "9. Machine Learning Methodology")

    add_heading(doc, "9.1 Algorithm Selection", level=2)
    add_body(doc, "Chosen Algorithm: Random Forest Classifier (Ensemble Learning)")
    add_body(doc, "Justification:")
    add_bullet(doc, "The dataset consists of 138 binary features — a format where tree-based methods excel")
    add_bullet(doc, "Random Forests aggregate hundreds of decision trees, reducing overfitting risk")
    add_bullet(doc, "Built-in feature importance enables interpretability")
    add_bullet(doc, "Native multi-class classification support (41 diseases)")
    add_bullet(doc, "class_weight='balanced' handles any potential class imbalance")

    add_heading(doc, "9.2 Training Pipeline", level=2)
    add_body(doc,
        "The training pipeline consists of the following sequential steps:\n\n"
        "Step 1: Load training_data.csv (4,920 rows × 141 columns)\n"
        "Step 2: Preprocessing — Remove unnamed columns, remove fluid_overload.1, regex normalization, deduplication\n"
        "Step 3: Stratified Train/Test Split (80% train, 20% test)\n"
        "Step 4: Hyperparameter Tuning via GridSearchCV (3-fold CV, 36 parameter combinations)\n"
        "Step 5: Select Best Random Forest model\n"
        "Step 6: Apply Probability Calibration via CalibratedClassifierCV (sigmoid, 3-fold)\n"
        "Step 7: Save disease_model.pkl and symptoms.pkl"
    )

    # Insert ML pipeline diagram
    add_diagram(doc, os.path.join(diagram_dir, "ml_pipeline.png"), "Figure 2: Machine Learning Training Pipeline")

    add_heading(doc, "9.3 Hyperparameter Tuning", level=2)
    add_body(doc, "The system uses GridSearchCV with 3-fold cross-validation to exhaustively search across 36 parameter combinations:")
    hp_table = doc.add_table(rows=1, cols=2)
    format_table(hp_table)
    add_table_row(hp_table, ["Parameter", "Search Values"], header=True)
    hp_table._tbl.remove(hp_table.rows[0]._tr)
    add_table_row(hp_table, ("n_estimators", "100, 200, 300"))
    add_table_row(hp_table, ("max_depth", "20, 50, None"))
    add_table_row(hp_table, ("min_samples_split", "2, 5"))
    add_table_row(hp_table, ("class_weight", "balanced, balanced_subsample"))

    add_heading(doc, "9.4 Probability Calibration", level=2)
    add_body(doc,
        "Raw Random Forest probabilities are unreliable — they tend to be overconfident. The system applies Platt Scaling "
        "(sigmoid calibration) using CalibratedClassifierCV with 3-fold cross-validation."
    )
    add_body(doc,
        "Before calibration: A 90% confidence score might only correspond to a true 75% accuracy. "
        "After calibration: Confidence scores are statistically meaningful — 90% confidence truly means ~90% likelihood."
    )

    add_heading(doc, "9.5 Prediction Engine", level=2)
    add_body(doc, "The inference pipeline in predict.py implements:")
    add_bullet(doc, " Model and symptom list are loaded once and cached as module-level singletons", "Lazy Loading:")
    add_bullet(doc, " Regex-based ([\\s_]+ → _) matching the training pipeline", "Input Normalization:")
    add_bullet(doc, " difflib.get_close_matches(cutoff=0.7) maps imprecise inputs like 'shiver' → 'shivering'", "Fuzzy Matching:")
    add_bullet(doc, " One-hot encoding of age group and gender", "Demographic Features:")
    add_bullet(doc, " Enforced alignment with training feature order", "Column Ordering:")
    add_bullet(doc, " Top-3 ranked predictions with calibrated probability percentages", "Output:")

    add_heading(doc, "9.6 Feature Importance Analysis", level=2)
    fi_table = doc.add_table(rows=1, cols=3)
    format_table(fi_table)
    add_table_row(fi_table, ["Rank", "Feature", "Importance"], header=True)
    fi_table._tbl.remove(fi_table.rows[0]._tr)
    fi_data = [
        ("1", "muscle_pain", "0.0186"), ("2", "itching", "0.0158"), ("3", "chest_pain", "0.0147"),
        ("4", "high_fever", "0.0137"), ("5", "yellowing_of_eyes", "0.0136"), ("6", "mild_fever", "0.0135"),
        ("7", "nausea", "0.0134"), ("8", "fatigue", "0.0134"), ("9", "family_history", "0.0134"),
        ("10", "dark_urine", "0.0131"),
    ]
    for row in fi_data:
        add_table_row(fi_table, row)

    add_body(doc, "Note: Age and gender features have low individual importance (<0.001) due to the dataset structure. They are retained as contextual features for future dataset expansion.")

    # === 10. EXTERNAL API INTEGRATIONS ===
    add_heading(doc, "10. External API Integrations")

    add_heading(doc, "10.1 Groq Cloud LLM API", level=2)
    groq_table = doc.add_table(rows=1, cols=2)
    format_table(groq_table)
    add_table_row(groq_table, ["Property", "Value"], header=True)
    groq_table._tbl.remove(groq_table.rows[0]._tr)
    add_table_row(groq_table, ("Provider", "Groq Inc."))
    add_table_row(groq_table, ("Model", "llama-3.1-8b-instant"))
    add_table_row(groq_table, ("SDK", "groq Python package (v1.1.1)"))
    add_table_row(groq_table, ("Authentication", "API key via GROQ_API_KEY"))

    add_body(doc, "Integration Point A — AI Health Assistant Chatbot (POST /api/chat): Receives full conversation history, system prompt includes predicted diagnosis, max_tokens=655, temperature=0.7.")
    add_body(doc, "Integration Point B — Disease Intelligence Generator (GET /api/disease-info): Generates structured JSON with severity, description, precautions, and diet. Uses temperature=0.3 for factual accuracy.")

    add_heading(doc, "10.2 Geoapify Places API", level=2)
    geo_table = doc.add_table(rows=1, cols=2)
    format_table(geo_table)
    add_table_row(geo_table, ["Property", "Value"], header=True)
    geo_table._tbl.remove(geo_table.rows[0]._tr)
    add_table_row(geo_table, ("Endpoint", "https://api.geoapify.com/v2/places"))
    add_table_row(geo_table, ("Categories", "healthcare.hospital, healthcare.clinic_or_praxis"))
    add_table_row(geo_table, ("Search Radius", "5,000 meters (5 km)"))
    add_table_row(geo_table, ("Result Limit", "20 results (filtered to top 10)"))

    add_body(doc, "Smart Specialty Matching: The system maps predicted diseases to medical specialty keywords and prioritizes hospitals accordingly. For example, Heart attack maps to Cardiology; Diabetes maps to Endocrinology; Migraine maps to Neurology.")
    add_body(doc, "Sorting Logic: (is_specialized DESC, distance ASC) — Specialized hospitals appear first, then by proximity.")

    add_heading(doc, "10.3 Brevo (Sendinblue) REST API", level=2)
    brevo_table = doc.add_table(rows=1, cols=2)
    format_table(brevo_table)
    add_table_row(brevo_table, ["Property", "Value"], header=True)
    brevo_table._tbl.remove(brevo_table.rows[0]._tr)
    add_table_row(brevo_table, ("Endpoint", "https://api.brevo.com/v3/smtp/email"))
    add_table_row(brevo_table, ("Authentication", "API key via BREVO_API_KEY"))
    add_table_row(brevo_table, ("Sender", "Configurable via BREVO_SENDER_EMAIL"))

    add_body(doc, "Three email types are sent: (1) 6-digit OTP for registration verification, (2) Appointment confirmation upon booking, (3) Automated 12-hour and 1-hour appointment reminders. All emails use responsive inline-CSS HTML templates.")

    # === 11. BACKEND ARCHITECTURE ===
    add_heading(doc, "11. Backend Architecture")
    add_body(doc, "The monolithic Flask application (app.py — 701 lines) handles route definitions (15 endpoints), database model definitions (3 ORM models), external API integration logic, background job scheduling, and email sending utilities.")

    add_heading(doc, "11.1 Database Schema", level=2)
    # Insert ER diagram
    add_diagram(doc, os.path.join(diagram_dir, "er_diagram.png"), "Figure 3: Entity Relationship Diagram")
    add_body(doc,
        "The application uses three database models:\n\n"
        "User: id (PK), email (unique), password_hash, is_verified, verification_code, created_at\n"
        "PredictionRecord: id (PK), user_id (FK), symptoms (JSON), predicted_disease, top_predictions (JSON), created_at\n"
        "Appointment: id (PK), user_id (FK), hospital_name, doctor_name, appointment_date, appointment_time, patient_name, patient_phone, reminder_12h_sent, reminder_1h_sent, created_at"
    )

    add_heading(doc, "11.2 Database Connection Resilience", level=2)
    add_body(doc,
        "Neon serverless PostgreSQL aggressively closes idle connections. The application implements: "
        "pool_pre_ping=True (validate connections before use), pool_recycle=280 (reconnect every ~4.6 minutes), "
        "pool_timeout=30 (connection timeout)."
    )

    # === 12. FRONTEND ARCHITECTURE ===
    add_heading(doc, "12. Frontend Architecture")

    add_heading(doc, "12.1 Design System", level=2)
    add_body(doc, "The CSS design system (styles.css — 3,562 lines) implements a premium visual language:")
    add_bullet(doc, " Primary: #7C3AED (violet), Background: #FAFBFF, Surface: #FFFFFF", "Color Palette:")
    add_bullet(doc, " backdrop-filter: blur(16px) with translucent backgrounds", "Glassmorphism:")
    add_bullet(doc, " Multi-layered box shadows for depth perception", "Shadows:")
    add_bullet(doc, " Heartbeat logo, scroll-reveal, floating badges, hover effects", "Animations:")
    add_bullet(doc, " Breakpoints at 992px, 768px, and 640px", "Responsive:")

    add_heading(doc, "12.2 Page Templates", level=2)
    tmpl_table = doc.add_table(rows=1, cols=3)
    format_table(tmpl_table)
    add_table_row(tmpl_table, ["Template", "Lines", "Description"], header=True)
    tmpl_table._tbl.remove(tmpl_table.rows[0]._tr)
    add_table_row(tmpl_table, ("index.html", "818", "Main dashboard: landing, symptoms, diagnosis, hospitals, chatbot, auth"))
    add_table_row(tmpl_table, ("appointment.html", "378", "Booking form with doctor selection and time slots"))
    add_table_row(tmpl_table, ("history.html", "~100", "Full prediction history page"))
    add_table_row(tmpl_table, ("appointments_history.html", "~110", "Full appointments history page"))

    add_heading(doc, "12.3 Client-Side JavaScript Modules", level=2)
    js_table = doc.add_table(rows=1, cols=3)
    format_table(js_table)
    add_table_row(js_table, ["Module", "Lines", "Functionality"], header=True)
    js_table._tbl.remove(js_table.rows[0]._tr)
    js_data = [
        ("Symptom Management", "~100", "Fetch, render, search, filter, track selections"),
        ("Prediction Submission", "~100", "Form handling, API call, result rendering"),
        ("Hospital Locator", "~90", "Geolocation, API call, card rendering"),
        ("Disease Intelligence", "~135", "AI details, severity badges, text-to-speech"),
        ("AI Chatbot", "~135", "Chat history, typing indicators, voice search"),
        ("Authentication", "~150", "Login, register, verify, session management"),
        ("User Sidebar", "~100", "History loading, accordion toggles, drawer"),
        ("Landing Page", "~90", "Scroll reveal, showcase carousel, demo mode"),
    ]
    for row in js_data:
        add_table_row(js_table, row)

    # === 13. AUTOMATION ===
    add_heading(doc, "13. Automation & Background Jobs")
    add_heading(doc, "13.1 Appointment Reminder System", level=2)
    add_body(doc,
        "The Flask-APScheduler runs a background job (check_reminders) every 10 minutes that:\n\n"
        "1. Queries all appointments where reminder flags are False\n"
        "2. Parses appointment datetime (date + time → datetime object)\n"
        "3. Calculates time_to_appointment = appointment_time - current_time_IST\n"
        "4. If 0h < time ≤ 12h and 12h reminder not sent → sends 12h reminder via Brevo\n"
        "5. If 0h < time ≤ 1h and 1h reminder not sent → sends 1h reminder via Brevo\n"
        "6. Sets corresponding flag to True and commits to database"
    )
    # Insert automation flow diagram
    add_diagram(doc, os.path.join(diagram_dir, "automation_flow.png"), "Figure 4: Appointment Reminder Automation Flow")

    add_body(doc, "Key Design Decisions:")
    add_bullet(doc, " Server runs in UTC; appointments stored in IST. Scheduler applies +05:30 offset.", "IST Offset:")
    add_bullet(doc, " Boolean flags (reminder_12h_sent, reminder_1h_sent) prevent duplicate sends.", "Idempotency:")
    add_bullet(doc, " misfire_grace_time=900 (15 min) allows delayed execution on cold starts.", "Graceful Failure:")

    # === 14. AUTHENTICATION ===
    add_heading(doc, "14. Authentication & Security")
    add_heading(doc, "14.1 Authentication Flow", level=2)
    add_body(doc,
        "1. User submits POST /api/register with email and password\n"
        "2. Backend hashes password with Werkzeug (PBKDF2 + salt), generates 6-digit OTP\n"
        "3. Creates unverified User record in DB, sends OTP via Brevo email\n"
        "4. User submits POST /api/verify with email and OTP code\n"
        "5. Backend validates OTP, sets is_verified = True\n"
        "6. User submits POST /api/login with credentials\n"
        "7. Backend validates, creates Flask server-side session"
    )

    add_heading(doc, "14.2 Security Measures", level=2)
    sec_table = doc.add_table(rows=1, cols=2)
    format_table(sec_table)
    add_table_row(sec_table, ["Measure", "Implementation"], header=True)
    sec_table._tbl.remove(sec_table.rows[0]._tr)
    add_table_row(sec_table, ("Password Hashing", "Werkzeug PBKDF2 + salt"))
    add_table_row(sec_table, ("Session Management", "Flask server-side sessions with SECRET_KEY"))
    add_table_row(sec_table, ("Email Verification", "6-digit OTP required before login"))
    add_table_row(sec_table, ("Environment Variables", "All secrets in .env, never hardcoded"))
    add_table_row(sec_table, ("Input Validation", "Required field checks on all POST endpoints"))

    add_heading(doc, "14.3 Guest/Demo Mode", level=2)
    add_body(doc, "Unauthenticated users access /?demo=1 with: symptom prediction (allowed), AI chatbot (allowed), hospital locator (blocked), appointment booking (blocked), history (blocked).")

    # === 15. API REFERENCE ===
    add_heading(doc, "15. API Reference")
    add_heading(doc, "15.1 Public Endpoints", level=2)
    api_table = doc.add_table(rows=1, cols=4)
    format_table(api_table)
    add_table_row(api_table, ["Method", "Endpoint", "Request", "Response"], header=True)
    api_table._tbl.remove(api_table.rows[0]._tr)
    api_data = [
        ("GET", "/", "—", "Landing/Dashboard HTML"),
        ("POST", "/api/register", "{email, password}", "{message} or {error}"),
        ("POST", "/api/verify", "{email, code}", "{message} or {error}"),
        ("POST", "/api/login", "{email, password}", "{message, user_id}"),
        ("GET", "/api/symptoms", "—", "{symptoms: [...]} (131 items)"),
        ("POST", "/api/predict", "{symptoms, age?, gender?}", "{prediction, top_predictions}"),
        ("GET", "/api/disease-info", "?disease=X", "{severity, description, precautions, diet}"),
        ("GET", "/api/hospitals", "?lat=X&lon=Y&disease=Z", "{hospitals: [...]}"),
        ("POST", "/api/chat", "{messages: [...]}", "{response}"),
    ]
    for row in api_data:
        add_table_row(api_table, row)

    add_heading(doc, "15.2 Protected Endpoints (Auth Required)", level=2)
    api2_table = doc.add_table(rows=1, cols=4)
    format_table(api2_table)
    add_table_row(api2_table, ["Method", "Endpoint", "Request", "Response"], header=True)
    api2_table._tbl.remove(api2_table.rows[0]._tr)
    api2_data = [
        ("POST", "/api/logout", "—", "{message}"),
        ("POST", "/api/book_appointment", "{hospital, doctor, date, time, name, phone}", "{message, appointment}"),
        ("GET", "/api/user/data", "—", "{predictions, appointments}"),
        ("GET", "/history", "—", "Prediction history page"),
        ("GET", "/appointments-history", "—", "Appointments history page"),
        ("GET", "/appointment", "?hospital=X", "Booking form page"),
    ]
    for row in api2_data:
        add_table_row(api2_table, row)

    # === 16. DEPLOYMENT ===
    add_heading(doc, "16. Deployment & DevOps")
    dep_table = doc.add_table(rows=1, cols=3)
    format_table(dep_table)
    add_table_row(dep_table, ["File", "Content", "Purpose"], header=True)
    dep_table._tbl.remove(dep_table.rows[0]._tr)
    add_table_row(dep_table, ("Procfile", "gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120", "Render process"))
    add_table_row(dep_table, ("runtime.txt", "python-3.11.9", "Python version"))
    add_table_row(dep_table, ("requirements.txt", "11 dependencies", "Pip install"))
    add_table_row(dep_table, (".env", "5 environment variables", "API keys and DB URL"))

    add_body(doc, "Production Considerations: Gunicorn timeout set to 120s for LLM responses; pool_pre_ping=True prevents stale DB connections; postgres:// auto-corrected to postgresql:// for SQLAlchemy; APScheduler misfire_grace_time=900s for cold starts.")

    # === 17. TESTING ===
    add_heading(doc, "17. Testing & Evaluation Results")

    add_heading(doc, "17.1 Machine Learning Evaluation", level=2)
    eval_table = doc.add_table(rows=1, cols=3)
    format_table(eval_table)
    add_table_row(eval_table, ["Metric", "Score", "Dataset"], header=True)
    eval_table._tbl.remove(eval_table.rows[0]._tr)
    add_table_row(eval_table, ("Training Accuracy", "100.00%", "Internal 80/20 stratified split"))
    add_table_row(eval_table, ("Test Accuracy (Top-1)", "98.00%", "Independent test_data.csv"))
    add_table_row(eval_table, ("Test Accuracy (Top-3)", "100.00%", "Correct diagnosis always in top 3"))
    add_table_row(eval_table, ("Cross-Validation", "100.00% ± 0.00%", "5-fold CV on full dataset"))
    add_table_row(eval_table, ("Macro Avg Precision", "0.99", "Across all 41 classes"))
    add_table_row(eval_table, ("Macro Avg Recall", "0.99", "Across all 41 classes"))
    add_table_row(eval_table, ("Macro Avg F1-Score", "0.98", "Across all 41 classes"))

    add_heading(doc, "17.2 Fuzzy Matching Validation", level=2)
    fz_table = doc.add_table(rows=1, cols=3)
    format_table(fz_table)
    add_table_row(fz_table, ["Input", "Matched To", "Status"], header=True)
    fz_table._tbl.remove(fz_table.rows[0]._tr)
    add_table_row(fz_table, ('"shiver"', '"shivering"', "Correct match"))
    add_table_row(fz_table, ('"high fevr"', '"high_fever"', "Correct match"))
    add_table_row(fz_table, ('"skin rash"', '"skin_rash"', "Exact match (after normalization)"))
    add_table_row(fz_table, ('"xyz_invalid"', "—", "Correctly rejected"))

    # === 18. PROJECT STRUCTURE ===
    add_heading(doc, "18. Project Directory Structure")
    dir_lines = [
        "Smart-CDSS/",
        "│",
        "├── app.py                          # Flask application (701 lines)",
        "│                                   # Routes, models, API integrations",
        "│",
        "├── ml/",
        "│   ├── train_model.py              # ML training pipeline (120 lines)",
        "│   │                               # GridSearchCV + CalibratedClassifierCV",
        "│   └── predict.py                  # Inference engine (143 lines)",
        "│                                   # Fuzzy matching + Top-3 predictions",
        "│",
        "├── model/",
        "│   ├── disease_model.pkl           # Serialized calibrated RF model (~22 MB)",
        "│   └── symptoms.pkl                # Serialized feature name list (~2 KB)",
        "│",
        "├── dataset/",
        "│   ├── training_data.csv           # Training dataset (~1.4 MB)",
        "│   ├── test_data.csv               # Test dataset (~14 KB)",
        "│   ├── evaluate_dataset.py         # Dataset analysis utilities",
        "│   └── update_dataset.py           # Dataset modification scripts",
        "│",
        "├── evaluate_model.py               # Model evaluation script (92 lines)",
        "│",
        "├── templates/",
        "│   ├── index.html                  # Main application template (818 lines)",
        "│   ├── appointment.html            # Booking form template (378 lines)",
        "│   ├── history.html                # Prediction history page",
        "│   └── appointments_history.html   # Appointments history page",
        "│",
        "├── static/",
        "│   ├── css/",
        "│   │   └── styles.css              # Complete design system (3,562 lines)",
        "│   ├── js/",
        "│   │   └── app.js                  # Client-side JavaScript (1,164 lines)",
        "│   └── img/",
        "│       ├── symptoms-profiling.png  # Landing page showcase",
        "│       ├── deep-insights.png       # Landing page showcase",
        "│       ├── facility-locator.png    # Landing page showcase",
        "│       ├── Appointment-booking.png # Landing page showcase",
        "│       └── 247-consultation.png    # Landing page showcase",
        "│",
        "├── requirements.txt                # Python dependencies (11 packages)",
        "├── Procfile                        # Gunicorn deployment config",
        "├── runtime.txt                     # Python 3.11.9",
        "├── .env                            # Environment variables",
        "├── .gitignore                      # Git ignore rules",
        "├── LICENSE                         # MIT License",
        "│",
        "└── Utility Scripts/",
        "    ├── create_test_user.py         # Test user creation",
        "    ├── debug_queries.py            # Database debugging",
        "    ├── fix_db_reminders.py         # Reminder flag repair",
        "    ├── update_db.py                # Database migrations",
        "    ├── test_auth.py                # Authentication testing",
        "    ├── test_brevo.py               # Email API testing",
        "    └── test_endpoint.py            # Endpoint testing",
    ]
    for line in dir_lines:
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.name = "Courier New"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = Pt(14)

    # === 19. SCREENSHOTS & UI ===
    add_heading(doc, "19. Screenshots & User Interface")
    add_body(doc, "The application implements a premium, mobile-first design with the following key screens:")
    # Insert user workflow diagram
    add_diagram(doc, os.path.join(diagram_dir, "user_workflow.png"), "Figure 5: End-to-End User Workflow")
    ui_table = doc.add_table(rows=1, cols=2)
    format_table(ui_table)
    add_table_row(ui_table, ["Screen", "Description"], header=True)
    ui_table._tbl.remove(ui_table.rows[0]._tr)
    add_table_row(ui_table, ("Landing Page", "Hero section with animated backgrounds, CTA buttons, feature carousel, contact form"))
    add_table_row(ui_table, ("Symptom Selection", "Age/gender dropdowns, searchable symptom grid with checkboxes, counter"))
    add_table_row(ui_table, ("Diagnosis Results", "Master-detail layout: condition cards with confidence bars + AI details"))
    add_table_row(ui_table, ("Hospital Locator", "Location-based cards with specialty badges, map links, booking buttons"))
    add_table_row(ui_table, ("Appointment Booking", "Form with doctor selection, date picker, time slots, confirmation"))
    add_table_row(ui_table, ("AI Chat Assistant", "Chat with markdown rendering, voice input, contextual health guidance"))
    add_table_row(ui_table, ("User Sidebar", "Drawer with diagnosis history, appointments, account management"))

    # === 20. FUTURE SCOPE ===
    add_heading(doc, "20. Future Scope")
    fs_table = doc.add_table(rows=1, cols=3)
    format_table(fs_table)
    add_table_row(fs_table, ["Enhancement", "Description", "Priority"], header=True)
    fs_table._tbl.remove(fs_table.rows[0]._tr)
    fs_data = [
        ("Expanded Dataset", "Add more diseases, regional symptoms, and real-world clinical data", "High"),
        ("Multi-language Support", "Hindi, Urdu, Arabic interfaces and chatbot responses", "High"),
        ("HIPAA Compliance", "Implement healthcare data privacy standards", "High"),
        ("Medical Image Analysis", "Image-based diagnosis (skin conditions, X-rays)", "Medium"),
        ("Wearable Integration", "Connect with smartwatch health data (heart rate, SpO2)", "Medium"),
        ("Doctor Portal", "Dashboard for doctors to view patient referrals and history", "Medium"),
        ("Push Notifications", "Browser/mobile push for appointment reminders", "Low"),
        ("A/B Testing", "Compare model versions in production", "Low"),
    ]
    for row in fs_data:
        add_table_row(fs_table, row)

    # === 21. CONCLUSION ===
    add_heading(doc, "21. Conclusion")
    add_body(doc,
        "MedAssist.ai demonstrates the successful integration of machine learning, large language models, and modern "
        "web technologies to create a comprehensive healthcare decision support platform."
    )
    add_body(doc,
        "Accurate Diagnosis: The calibrated Random Forest model achieves 98% Top-1 accuracy and 100% Top-3 accuracy, "
        "ensuring reliable preliminary disease identification from 131 symptom inputs across 41 disease classes."
    )
    add_body(doc,
        "Intelligent Assistance: The Groq-powered LLM chatbot provides contextual, empathetic health guidance with "
        "structured safety guidelines, bridging the gap between automated diagnosis and human understanding."
    )
    add_body(doc,
        "Actionable Outcomes: The Geoapify hospital locator with disease-specific specialty matching and the integrated "
        "appointment booking system with automated Brevo email reminders transform prediction results into concrete healthcare actions."
    )
    add_body(doc,
        "Premium User Experience: The mobile-first design with glassmorphism, micro-animations, and responsive layouts "
        "provides an engaging, trustworthy interface that encourages healthy engagement with the platform."
    )
    add_body(doc,
        "The modular architecture ensures that each component — ML model, LLM integration, hospital search, email "
        "automation — can be independently upgraded as better models, APIs, or datasets become available."
    )

    # === 22. REFERENCES ===
    add_heading(doc, "22. References")
    refs = [
        "Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5–32.",
        "Niculescu-Mizil, A., & Caruana, R. (2005). Predicting Good Probabilities with Supervised Learning. ICML 2005.",
        "Uddin, S., Khan, A., Hossain, M. E., & Moni, M. A. (2019). Comparing different supervised machine learning algorithms for disease prediction. BMC Medical Informatics, 19(1), 281.",
        "scikit-learn Documentation — CalibratedClassifierCV. https://scikit-learn.org/stable/modules/calibration.html",
        "Groq Cloud API Documentation. https://console.groq.com/docs",
        "Geoapify Places API Documentation. https://apidocs.geoapify.com/docs/places/",
        "Brevo (Sendinblue) Transactional Email API. https://developers.brevo.com/",
    ]
    for i, ref in enumerate(refs, 1):
        p = doc.add_paragraph()
        run = p.add_run(f"[{i}] {ref}")
        run.font.size = Pt(10)
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

    doc.add_paragraph()
    disclaimer = doc.add_paragraph()
    disclaimer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = disclaimer.add_run("This document was generated for internal project review and academic documentation purposes.\nMedAssist.ai is a decision support tool and does not replace professional medical consultation.")
    run.font.size = Pt(9)
    run.font.italic = True
    run.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    # ── Add Page Numbers ──
    add_page_numbers(doc)

    # ── Save ──
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MedAssist_DPR_v2.docx")
    doc.save(output_path)
    print(f"Report saved to: {output_path}")
    print(f"\nIMPORTANT: Open the file in Microsoft Word, then:")
    print(f"  1. Right-click the Table of Contents")
    print(f"  2. Select 'Update Field' -> 'Update entire table'")
    print(f"  3. This will populate page numbers automatically")
    print(f"  4. To save as PDF: File -> Save As -> PDF")

    return output_path


if __name__ == "__main__":
    generate_report()
