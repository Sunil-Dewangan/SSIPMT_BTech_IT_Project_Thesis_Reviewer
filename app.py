
import streamlit as st
import google.generativeai as genai
import base64
import json
import io
import os
import time
import tempfile
import mammoth
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from pdf_generator import generate_full_report, generate_report_card, generate_comparison_table

load_dotenv()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SSIPMT Report Reviewer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #f0f4ff; }
.stMetric label { font-size: 11px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GUIDELINES & SYSTEM PROMPT
# ─────────────────────────────────────────────
GUIDELINES = """
SSIPMT B.Tech Project Report Guidelines — Dept. of IT, Session 2025-2026

PAGE SETUP: A4, all margins 1 inch, Times New Roman 12pt, 1.5 line spacing, 0pt paragraph spacing before/after, box page border on every page.

MANDATORY STRUCTURE (exact order):
1. Cover/Title Page — no page number
2. Declaration by Candidate — Roman numeral i
3. Certificate by Supervisor — Roman numeral ii
4. Certificate by Examiners — Roman numeral iii
5. Acknowledgement — Roman numeral iv
6. List of Abbreviations — Roman numeral v (alphabetical, two-column table)
7. List of Figures — Roman numeral vi (4 columns: Sr.No., Fig No., Description, Page No.)
8. Table of Contents — Roman numeral vii (automatic TOC with page numbers)
9. Abstract — Roman numeral viii (300–500 words, no citations, ends with Keywords line of 5–8 keywords)
10. Chapter Separator Pages — no page number
11. Chapters 1–14 — Arabic numerals starting at 1
12. References — continues Arabic numerals

HEADING STYLES:
- Chapter separator page: 22pt Bold CAPS Centred
- Chapter title on content page: 16pt Bold CAPS Centred
- Section (1.1, 2.1...): 12pt Bold Left-aligned
- Subsection (1.1.1): 12pt Bold Left-aligned
- Body text: 12pt Regular Justified
- Figure caption BELOW figure: 11pt Regular Centred — format "Fig. X.Y: Description"
- Table caption ABOVE table: 11pt Bold Centred — format "Table X.Y: Description"
- Institute header: 9pt Bold Centred on every page except cover and separators

14 MANDATORY CHAPTERS WITH REQUIRED CONTENT:
Ch1 Introduction: must have exactly 5 sections — 1.1 Project Overview, 1.2 Problem Statement, 1.3 Objectives, 1.4 Scope, 1.5 Organisation of Report
Ch2 Previous Work: literature review with in-text citations, minimum 7 sections, must end with summary/comparison table
Ch3 System Analysis: 3.1 Identification of Need, 3.2 Preliminary Investigation
Ch4 Feasibility Study: must cover all 5 types — Technical, Operational, Economic, Legal, Social — plus a Summary section
Ch5 Analysis: must include DFD Level 0 (1 central process + 4 external entities), DFD Level 1 (5–7 sub-processes + data stores D1/D2...), DFD Level 2 (expand 2 Level-1 processes), ER Diagram (entities+attributes+relationships), Database Table Structures (Field Name, Data Type, Size, Constraints) for every table
Ch6 S/W Technology Paradigm: Waterfall model with labelled diagram + application to current project
Ch7 Methodology: System Architecture + step-by-step development + Algorithms in bordered box (Courier New 11pt, heading "Algorithm N: Name", starts with Input: and Output:, numbered steps)
Ch8 S/W and H/W Requirements: Developer requirements + User requirements + Technology stack summary table
Ch9 System Design: Modular architecture + details of each module + inter-module communication
Ch10 Screenshots: ACTUAL running application screenshots (not wireframes), colour figures must be colour-printed
Ch11 Implementation and Maintenance: step-by-step implementation details + maintenance plan
Ch12 Testing: must cover all 8 testing types with test case tables (Unit, Integration, System, Acceptance, Performance, Security, Regression, UAT)
Ch13 System Security Measures: security design and implementation details
Ch14 Conclusion and Future Scope: chapter conclusions + future enhancements table with version, priority, effort columns

REFERENCES:
- Heading: REFERENCES (not Bibliography)
- Minimum 15 references required
- At least 10 must be peer-reviewed (journal or conference papers)
- IEEE numbered format [1], [2], [3] in text and in list
- Journal: [N] A. Author, "Title," Journal Name, vol. X, no. Y, pp. Z–Z, Year. DOI
- Conference: [N] A. Author, "Title," in Proc. Conference Name, City, Year, pp. Z–Z.
- Book: [N] A. Author, Book Title, Xth ed. Publisher, Year.
- Every reference must be cited at least once in text; every factual claim must have a citation
- No Wikipedia, no informal blogs allowed

FIGURES: Caption BELOW, "Fig. ChapterNo.FigNo.: Description", 11pt Regular Centred, must be referenced in text before appearance, minimum 150 DPI
TABLES: Caption ABOVE, "Table ChapterNo.TableNo.: Description", 11pt Bold Centred, header row bold with 20% gray shading, visible borders, referenced before appearance

GENERAL RULES:
- Absolutely no first-person language (no "I", "we", "our", "my") — use passive voice and third person
- No placeholder text remaining ([Name], [Date], [Company], etc.)
- No decorative fonts, WordArt, clipart, coloured body text
- Minimum 2 full pages per chapter (separator page not counted)
- Total report: 40–80 pages (excluding cover page and front matter)
- Spell-check and grammar-check must be completed before submission
"""

SYSTEM_PROMPT = f"""You are an expert, strict, and fair B.Tech project report reviewer for Shri Shankaracharya Institute of Professional Management & Technology (SSIPMT), Raipur, Department of Information Technology, Session 2025-2026.

Review the submitted student project report thoroughly against these official SSIPMT guidelines:

{GUIDELINES}

Be specific — cite actual content from the report when identifying issues. Be thorough but fair.

Return ONLY a valid JSON object. No markdown formatting, no backticks, no explanation text outside the JSON.

Required JSON structure:
{{
  "project_title": "string",
  "report_type": "string",
  "student_names": ["array of strings"],
  "guide_name": "string",
  "overall_score": number between 0-100,
  "overall_recommendation": "APPROVED or MINOR_REVISION or MAJOR_REVISION or REJECTED",
  "executive_summary": "3-4 sentence overview of report quality",
  "format_compliance": {{
    "score": number,
    "checks": [{{"item": "string", "status": "PASS or FAIL or WARNING or CANNOT_VERIFY", "detail": "string"}}]
  }},
  "front_matter": {{
    "score": number,
    "sections": [{{"name": "string", "present": true or false, "issues": "string or null"}}]
  }},
  "chapters": [
    {{
      "number": number,
      "title": "string",
      "present": true or false,
      "estimated_pages": number,
      "meets_2page_minimum": true or false,
      "score": number,
      "issues": ["array of specific issue strings"],
      "strengths": ["array of strength strings"],
      "feedback": "detailed specific feedback string"
    }}
  ],
  "technical_elements": {{
    "score": number,
    "dfd_level0": {{"present": true or false, "issues": "string or null"}},
    "dfd_level1": {{"present": true or false, "issues": "string or null"}},
    "dfd_level2": {{"present": true or false, "issues": "string or null"}},
    "er_diagram": {{"present": true or false, "issues": "string or null"}},
    "table_structures": {{"present": true or false, "count": number, "issues": "string or null"}},
    "algorithms": {{"present": true or false, "count": number, "properly_formatted": true or false, "issues": "string or null"}},
    "waterfall_diagram": {{"present": true or false, "issues": "string or null"}},
    "testing_types": {{"count": number, "types_found": ["array"], "issues": "string or null"}}
  }},
  "abstract": {{
    "score": number,
    "estimated_word_count": number,
    "within_300_500": true or false,
    "has_keywords": true or false,
    "keyword_count": number,
    "covers_problem": true or false,
    "covers_solution": true or false,
    "covers_technologies": true or false,
    "covers_results": true or false,
    "has_citations": true or false,
    "issues": ["array"],
    "feedback": "string"
  }},
  "references": {{
    "score": number,
    "total_count": number,
    "meets_minimum_15": true or false,
    "peer_reviewed_count": number,
    "meets_10_peer_reviewed": true or false,
    "ieee_format": "FULL or PARTIAL or POOR",
    "issues": ["array of specific issues"],
    "feedback": "string"
  }},
  "language_quality": {{
    "score": number,
    "first_person_violations": ["exact quotes found or empty array"],
    "grammar_quality": "POOR or FAIR or GOOD or EXCELLENT",
    "technical_accuracy": "POOR or FAIR or GOOD or EXCELLENT",
    "academic_tone": "POOR or FAIR or GOOD or EXCELLENT",
    "placeholder_text_found": true or false,
    "feedback": "string"
  }},
  "critical_issues": ["array of critical issues that prevent submission"],
  "major_issues": ["array of significant issues requiring correction"],
  "minor_issues": ["array of smaller improvements needed"],
  "strengths": ["array of things the report does well"],
  "priority_action_list": [
    {{"priority": number, "action": "string", "location": "string", "severity": "CRITICAL or MAJOR or MINOR"}}
  ]
}}"""

# ─────────────────────────────────────────────
# DEFAULTS
# ─────────────────────────────────────────────
DEFAULT_WEIGHTS = {
    "format": 15, "front_matter": 10, "chapters": 25,
    "technical": 20, "abstract": 5, "references": 15, "language": 10
}
WEIGHT_INFO = {
    "format":       "Format Compliance",
    "front_matter": "Front Matter (8 sections)",
    "chapters":     "Chapter Content (14 chapters)",
    "technical":    "Technical Elements",
    "abstract":     "Abstract Quality",
    "references":   "References",
    "language":     "Language & Writing",
}

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in {"weights": dict(DEFAULT_WEIGHTS), "single_review": None, "batch_results": []}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
#def get_api_key():
#    return (os.getenv("GEMINI_API_KEY", "")
#            or st.session_state.get("gemini_key", ""))
def get_api_key():
    # 1. Try to get the key from the environment or session state
    raw_key = os.getenv("GEMINI_API_KEY", "") or st.session_state.get("gemini_key", "")
    
    # 2. Fallback to Streamlit Secrets (useful if you deploy to Streamlit Cloud)
    if not raw_key:
        try:
            raw_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
            
    # 3. CRITICAL FIX: Strip all invisible whitespace and accidental quotation marks
    if raw_key:
        return raw_key.strip().strip("\"'")
        
    return ""

def score_emoji(s):
    return "🟢" if s >= 80 else ("🟡" if s >= 60 else "🔴")

def rec_icon(rec):
    return {"APPROVED": "✅ APPROVED", "MINOR_REVISION": "⚠️ MINOR REVISION",
            "MAJOR_REVISION": "🟠 MAJOR REVISION", "REJECTED": "❌ REJECTED"}.get(rec, rec)

def compute_weighted_score(review):
    wt = st.session_state.weights
    total = sum(wt.values()) or 1
    chs = review.get("chapters", [])
    ch_avg = (sum(c.get("score", 0) for c in chs) / len(chs)) if chs else 0
    dim = {
        "format":       review.get("format_compliance", {}).get("score", 0),
        "front_matter": review.get("front_matter", {}).get("score", 0),
        "chapters":     ch_avg,
        "technical":    review.get("technical_elements", {}).get("score", 0),
        "abstract":     review.get("abstract", {}).get("score", 0),
        "references":   review.get("references", {}).get("score", 0),
        "language":     review.get("language_quality", {}).get("score", 0),
    }
    return round(sum(dim[k] * (wt[k] / total) for k in wt))

def extract_file(uploaded_file):
    """Extract content from PDF or DOCX for Gemini."""
    name = uploaded_file.name.lower()
    raw  = uploaded_file.read()
    if name.endswith(".pdf"):
        return {"type": "pdf", "bytes": raw, "name": uploaded_file.name}
    elif name.endswith(".docx"):
        result = mammoth.extract_raw_text({"file": io.BytesIO(raw)})
        if not result.value.strip():
            raise ValueError("Could not extract text from DOCX. Convert to PDF and retry.")
        return {"type": "text", "data": result.value, "name": uploaded_file.name}
    raise ValueError("Unsupported file type. Upload PDF or DOCX only.")

def call_gemini(file_data):
    """Send file to Gemini and get JSON review."""
    api_key = get_api_key()
    if not api_key:
        st.error("⚠️ No Gemini API key found. Add it in the sidebar.")
        st.stop()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            max_output_tokens=4096,
            temperature=0.1,     # low = consistent structured output
        )
    )

    if file_data["type"] == "pdf":
        # Write PDF to a temp file, upload to Gemini Files API
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_data["bytes"])
            tmp_path = tmp.name
        try:
            uploaded = genai.upload_file(tmp_path, mime_type="application/pdf",
                                         display_name=file_data["name"])
            # Wait until Gemini has processed the file
            for _ in range(20):
                f = genai.get_file(uploaded.name)
                if f.state.name == "ACTIVE":
                    break
                if f.state.name == "FAILED":
                    raise ValueError("Gemini failed to process the PDF. Try a smaller file or convert to DOCX.")
                time.sleep(3)
            response = model.generate_content([
                uploaded,
                "Review this B.Tech project report against SSIPMT guidelines. Return only the JSON."
            ])
            try:
                genai.delete_file(uploaded.name)
            except Exception:
                pass
        finally:
            os.unlink(tmp_path)
    else:
        # DOCX extracted text
        response = model.generate_content(
            f"B.Tech Project Report (extracted from DOCX file: {file_data['name']}):\n\n"
            f"{file_data['data'][:40000]}\n\n"
            f"Review this report against SSIPMT guidelines. Return only the JSON review object."
        )

    raw   = response.text
    clean = raw.replace("```json", "").replace("```", "").strip()
    # Remove leading/trailing text that is not JSON
    start = clean.find("{")
    end   = clean.rfind("}") + 1
    if start >= 0 and end > start:
        clean = clean[start:end]
    return json.loads(clean)

# ─────────────────────────────────────────────
# DISPLAY REVIEW
# ─────────────────────────────────────────────
def show_review(rv):
    """Render the full review result."""
    ws  = compute_weighted_score(rv)
    rec = rv.get("overall_recommendation", "")

    # ── Overview ──
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.subheader(rv.get("project_title", "Untitled Report"))
        st.caption(
            f"**Student(s):** {', '.join(rv.get('student_names', ['—']))}  ·  "
            f"**Guide:** {rv.get('guide_name', '—')}"
        )
        st.write(rv.get("executive_summary", ""))
    with col2:
        st.metric("Weighted Score", f"{ws} / 100")
        st.caption(f"AI raw: {rv.get('overall_score', 0)}")
    with col3:
        st.metric("Decision", "")
        st.markdown(f"**{rec_icon(rec)}**")

    st.divider()

    # ── Dimension Scores ──
    cols = st.columns(6)
    for col, (name, key) in zip(cols, [
        ("Format",       "format_compliance"),
        ("Front Matter", "front_matter"),
        ("Technical",    "technical_elements"),
        ("Abstract",     "abstract"),
        ("References",   "references"),
        ("Language",     "language_quality"),
    ]):
        s = rv.get(key, {}).get("score", 0)
        col.metric(name, f"{score_emoji(s)} {s}")

    st.divider()

    # ── Issues ──
    ci = rv.get("critical_issues", [])
    mi = rv.get("major_issues",   [])
    ni = rv.get("minor_issues",   [])
    if ci:
        with st.expander(f"🚨 Critical Issues ({len(ci)}) — Report cannot be submitted as-is", expanded=True):
            for i in ci: st.markdown(f"- {i}")
    if mi:
        with st.expander(f"⚠️ Major Issues ({len(mi)}) — Significant corrections required", expanded=True):
            for i in mi: st.markdown(f"- {i}")
    if ni:
        with st.expander(f"📝 Minor Issues ({len(ni)})"):
            for i in ni: st.markdown(f"- {i}")

    # ── Priority Actions ──
    if rv.get("priority_action_list"):
        with st.expander("📋 Priority Action List — What to fix, in order", expanded=True):
            df = pd.DataFrame(rv["priority_action_list"])
            st.dataframe(df, hide_index=True, use_container_width=True)

    # ── Format Compliance ──
    fc = rv.get("format_compliance", {})
    if fc.get("checks"):
        with st.expander(f"📐 Format Compliance — Score: {fc.get('score', 0)}"):
            for c in fc["checks"]:
                icon = {"PASS":"✅","FAIL":"❌","WARNING":"⚠️","CANNOT_VERIFY":"❔"}.get(c["status"],"❔")
                st.markdown(f"{icon} **{c['item']}** — {c['detail']}")

    # ── Front Matter ──
    fm = rv.get("front_matter", {})
    if fm.get("sections"):
        with st.expander(f"📄 Front Matter — Score: {fm.get('score', 0)}"):
            cols2 = st.columns(3)
            for idx, s in enumerate(fm["sections"]):
                with cols2[idx % 3]:
                    st.markdown(f"{'✅' if s['present'] else '❌'} **{s['name']}**")
                    if s.get("issues"):
                        st.caption(f"⚠ {s['issues']}")

    # ── Chapters ──
    if rv.get("chapters"):
        with st.expander("📚 Chapter-by-Chapter Review"):
            for ch in rv["chapters"]:
                ok   = ch.get("present", False)
                warn = "" if ch.get("meets_2page_minimum", True) else "  ⚠️ Under 2-page minimum"
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{'✅' if ok else '❌'} Ch.{ch['number']}: {ch['title']}**{warn}")
                    st.caption(f"~{ch.get('estimated_pages',0)} pages")
                    if ch.get("feedback"):
                        st.write(ch["feedback"])
                    for iss in ch.get("issues", []):
                        st.markdown(f"  - ❌ {iss}")
                    for stt in ch.get("strengths", []):
                        st.markdown(f"  - ✓ {stt}")
                with c2:
                    if ok:
                        st.metric("", f"{score_emoji(ch.get('score',0))} {ch.get('score',0)}")
                st.divider()

    # ── Technical ──
    te = rv.get("technical_elements", {})
    if te:
        with st.expander(f"⚙️ Technical Elements — Score: {te.get('score',0)}"):
            for name, key in [
                ("DFD Level 0",            "dfd_level0"),
                ("DFD Level 1",            "dfd_level1"),
                ("DFD Level 2",            "dfd_level2"),
                ("ER Diagram",             "er_diagram"),
                ("Database Table Structures","table_structures"),
                ("Algorithms",             "algorithms"),
                ("Waterfall Model Diagram","waterfall_diagram"),
            ]:
                el = te.get(key)
                if not el: continue
                icon = "✅" if el.get("present") else "❌"
                cnt  = f" ({el['count']})" if "count" in el else ""
                st.markdown(f"{icon} **{name}**{cnt}")
                if el.get("issues"):
                    st.caption(f"  ↳ {el['issues']}")
            tst = te.get("testing_types", {})
            st.markdown(f"**Testing:** {tst.get('count',0)}/8 types — "
                        f"{', '.join(tst.get('types_found',[]) or ['None identified'])}")

    # ── Abstract ──
    ab = rv.get("abstract", {})
    if ab:
        with st.expander(f"📝 Abstract — Score: {ab.get('score',0)}"):
            c1, c2 = st.columns(2)
            with c1:
                wc = ab.get("estimated_word_count", 0)
                st.markdown(f"- Word count: ~{wc} {'✅' if ab.get('within_300_500') else '❌'} (300–500 required)")
                st.markdown(f"- Keywords: {'✅ ' + str(ab.get('keyword_count',0)) if ab.get('has_keywords') else '❌ Missing'}")
                st.markdown(f"- Covers problem: {'✅' if ab.get('covers_problem') else '❌'}")
                st.markdown(f"- Covers solution: {'✅' if ab.get('covers_solution') else '❌'}")
            with c2:
                st.markdown(f"- Covers technologies: {'✅' if ab.get('covers_technologies') else '❌'}")
                st.markdown(f"- Covers results: {'✅' if ab.get('covers_results') else '❌'}")
                st.markdown(f"- No citations: {'✅ Correct' if not ab.get('has_citations') else '❌ Remove citations'}")
            for iss in ab.get("issues", []):
                st.markdown(f"- ❌ {iss}")
            if ab.get("feedback"):
                st.info(ab["feedback"])

    # ── References ──
    ref = rv.get("references", {})
    if ref:
        with st.expander(f"📖 References — Score: {ref.get('score',0)}"):
            c1, c2, c3 = st.columns(3)
            tc = ref.get('total_count', 0)
            pc = ref.get('peer_reviewed_count', 0)
            c1.metric("Total References",  f"{tc}", delta=None if ref.get('meets_minimum_15') else "Need ≥ 15")
            c2.metric("Peer-reviewed",     f"{pc}", delta=None if ref.get('meets_10_peer_reviewed') else "Need ≥ 10")
            c3.metric("IEEE Format",       ref.get("ieee_format", "?"))
            for iss in ref.get("issues", []):
                st.markdown(f"- ❌ {iss}")
            if ref.get("feedback"):
                st.info(ref["feedback"])

    # ── Language ──
    lq = rv.get("language_quality", {})
    if lq:
        with st.expander(f"✍️ Language & Writing — Score: {lq.get('score',0)}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Grammar",            lq.get("grammar_quality", "—"))
            c2.metric("Technical Accuracy", lq.get("technical_accuracy", "—"))
            c3.metric("Academic Tone",      lq.get("academic_tone", "—"))
            if lq.get("placeholder_text_found"):
                st.error("⚠️ Placeholder text [Name]/[Date]/[Company] still present — must be replaced")
            if lq.get("first_person_violations"):
                st.warning("First-person violations found (not allowed in academic writing):")
                for v in lq["first_person_violations"]:
                    st.markdown(f'  - *"{v}"*')
            if lq.get("feedback"):
                st.info(lq["feedback"])

    # ── Strengths ──
    if rv.get("strengths"):
        with st.expander("💪 Strengths of this Report"):
            for s in rv["strengths"]:
                st.markdown(f"✓ {s}")

    # ── Downloads ──
    st.divider()
    st.subheader("📥 Download Reports")
    ws  = compute_weighted_score(rv)
    d1, d2 = st.columns(2)
    with d1:
        try:
            pdf = generate_full_report(rv, st.session_state.weights, ws)
            fname = f"Review_{rv.get('project_title','report')[:30].replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button("📄 Full Review Report (PDF)", pdf, fname, "application/pdf",
                               use_container_width=True, type="primary")
        except Exception as e:
            st.error(f"PDF error: {e}")
    with d2:
        try:
            card = generate_report_card(rv, st.session_state.weights, ws)
            fname2 = f"Card_{rv.get('project_title','report')[:30].replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button("🪪 Student Report Card (PDF)", card, fname2, "application/pdf",
                               use_container_width=True)
        except Exception as e:
            st.error(f"Card error: {e}")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🎓 SSIPMT\nReport Reviewer")
    st.caption("Dept. of IT · Session 2025–2026\n**100% Free — Powered by Google Gemini**")
    st.divider()

    # ── API Key ──
    #st.subheader("🔑 Gemini API Key")
    #env_key = os.getenv("GEMINI_API_KEY", "")
    #if env_key:
    #    st.success("✓ Key loaded from .env file")
    #else:
    #    st.session_state["gemini_key"] = st.text_input(
    #        "Paste your free Gemini API key",
    #        type="password",
    #        help="Get your free key in 2 minutes at aistudio.google.com/apikey"
    #    )
    #    st.caption("🔗 [Get free key → aistudio.google.com/apikey](https://aistudio.google.com/apikey)")

    # ── API Key ──
    st.subheader("🔑 Gemini API Key")
    
    # Check env AND secrets
    env_key = os.getenv("GEMINI_API_KEY", "")
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret_key = ""
        
    if env_key or secret_key:
        st.success("✓ Key loaded securely")
    else:
        st.session_state["gemini_key"] = st.text_input(
            "Paste your free Gemini API key",
            type="password",
            help="Get your free key in 2 minutes at aistudio.google.com/apikey"
        )
        st.caption("🔗 [Get free key → aistudio.google.com/apikey](https://aistudio.google.com/apikey)")

    st.divider()

    # ── Weights ──
    st.subheader("⚖️ Scoring Weights")
    st.caption("Adjust dimension importance.")
    new_wt = {}
    for k, label in WEIGHT_INFO.items():
        new_wt[k] = st.slider(label, 5, 60, st.session_state.weights[k], key=f"w_{k}")
    st.session_state.weights = new_wt
    tot = sum(new_wt.values())
    st.success(f"Total: {tot}% ✓") if abs(tot - 100) < 1 else st.warning(f"Total: {tot}% (target: 100%)")
    if st.button("↩ Reset Defaults"):
        st.session_state.weights = dict(DEFAULT_WEIGHTS)
        st.rerun()

    st.divider()
    st.caption("Free tier: **1,500 reviews/day**\nNo credit card required.")

# ─────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["📋  Single Review", "📦  Batch Review"])

# ══════════════════════════════════════════════
# TAB 1 — SINGLE REVIEW
# ══════════════════════════════════════════════
with tab1:
    st.header("Single Report Review")

    uploaded = st.file_uploader(
        "Upload student PDF or DOCX report",
        type=["pdf", "docx"],
        key="single_upload",
        help="PDF recommended — Gemini reads it directly. DOCX also supported."
    )

    if uploaded:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            ftype = "PDF" if uploaded.name.lower().endswith(".pdf") else "DOCX"
            st.info(f"📁 **{uploaded.name}** — {uploaded.size/1024/1024:.2f} MB  |  {ftype}")
        with col_b:
            start = st.button("🔍 Start Review", type="primary", use_container_width=True)

        if start:
            with st.spinner("Extracting document..."):
                try:
                    fd = extract_file(uploaded)
                except Exception as e:
                    st.error(str(e))
                    st.stop()

            bar  = st.progress(0, "Uploading to Gemini...")
            msgs = ["Analysing structure...", "Reading chapters...",
                    "Checking technical elements...", "Evaluating references...",
                    "Reviewing language...", "Computing scores...", "Almost done..."]
            result = [None]
            err    = [None]
            done   = [False]

            import threading
            def run():
                try:
                    result[0] = call_gemini(fd)
                except Exception as e:
                    err[0] = str(e)
                finally:
                    done[0] = True

            t = threading.Thread(target=run)
            t.start()

            step = 0
            while not done[0]:
                pct = min(10 + step * 12, 90)
                bar.progress(pct, msgs[min(step, len(msgs)-1)])
                time.sleep(5)
                step += 1
            t.join()
            bar.progress(100, "Done!")
            time.sleep(0.3)
            bar.empty()

            if err[0]:
                st.error(f"Review failed: {err[0]}")
            else:
                st.session_state.single_review = result[0]
                st.success("✅ Review complete!")

    if st.session_state.single_review:
        st.divider()
        show_review(st.session_state.single_review)

# ══════════════════════════════════════════════
# TAB 2 — BATCH REVIEW
# ══════════════════════════════════════════════
with tab2:
    st.header("Batch Review")
    st.caption("Upload all student reports at once. Reviewed one-by-one automatically.")
    st.info("ℹ️ Free tier allows **15 reviews per minute** — the tool adds a small pause between files automatically.")

    batch_files = st.file_uploader(
        "Upload multiple PDF/DOCX reports",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key="batch_upload"
    )

    if batch_files:
        st.success(f"📦 {len(batch_files)} file(s) ready")
        for f in batch_files:
            st.caption(f"  • {f.name}  ({f.size/1024/1024:.1f} MB)")

        if st.button("🚀 Start Batch Review", type="primary"):
            results   = []
            prog      = st.progress(0)
            status_ph = st.empty()

            for idx, uf in enumerate(batch_files):
                status_ph.info(f"🔍 Reviewing {idx+1}/{len(batch_files)}: **{uf.name}**")
                try:
                    fd = extract_file(uf)
                    rv = call_gemini(fd)
                    ws = compute_weighted_score(rv)
                    results.append({"file": uf.name, "review": rv, "score": ws, "error": None})
                except Exception as e:
                    results.append({"file": uf.name, "review": None, "score": 0, "error": str(e)})

                prog.progress((idx + 1) / len(batch_files))

                # Respect free-tier rate limit: 15 RPM → wait 5s between requests
                if idx < len(batch_files) - 1:
                    time.sleep(5)

            st.session_state.batch_results = results
            done_n = len([r for r in results if not r["error"]])
            status_ph.success(f"✅ Batch complete — {done_n}/{len(batch_files)} reviewed successfully")

    if st.session_state.batch_results:
        st.divider()
        st.subheader("📊 Comparison Table")

        rows = []
        for r in st.session_state.batch_results:
            if r["error"]:
                rows.append({"File": r["file"], "Students": "—", "Title": "ERROR",
                             "Score": 0, "Format": 0, "Front Matter": 0, "Technical": 0,
                             "Abstract": 0, "References": 0, "Language": 0, "Recommendation": "ERROR"})
            else:
                rv = r["review"]
                rows.append({
                    "File":           r["file"],
                    "Students":       ", ".join(rv.get("student_names", ["—"])),
                    "Title":          rv.get("project_title", "—")[:35],
                    "Score":          r["score"],
                    "Format":         rv.get("format_compliance", {}).get("score", 0),
                    "Front Matter":   rv.get("front_matter", {}).get("score", 0),
                    "Technical":      rv.get("technical_elements", {}).get("score", 0),
                    "Abstract":       rv.get("abstract", {}).get("score", 0),
                    "References":     rv.get("references", {}).get("score", 0),
                    "Language":       rv.get("language_quality", {}).get("score", 0),
                    "Recommendation": rv.get("overall_recommendation", "—").replace("_", " "),
                })

        df = pd.DataFrame(rows).sort_values("Score", ascending=False)
        st.dataframe(df, hide_index=True, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            csv = df.to_csv(index=False).encode()
            st.download_button("📊 Download Comparison (CSV / Excel)", csv,
                               f"Batch_{datetime.now().strftime('%Y%m%d')}.csv",
                               "text/csv", use_container_width=True)
        with c2:
            try:
                cmp_pdf = generate_comparison_table(
                    st.session_state.batch_results, st.session_state.weights
                )
                st.download_button("📄 Download Comparison (PDF)", cmp_pdf,
                                   f"Batch_{datetime.now().strftime('%Y%m%d')}.pdf",
                                   "application/pdf", use_container_width=True, type="primary")
            except Exception as e:
                st.error(str(e))

        # Individual full review
        st.divider()
        st.subheader("View Individual Review")
        done_r = [r for r in st.session_state.batch_results if not r["error"]]
        if done_r:
            sel_name = st.selectbox("Select student report:", [r["file"] for r in done_r])
            sel = next(r for r in done_r if r["file"] == sel_name)
            show_review(sel["review"])
