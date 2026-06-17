"""
SSIPMT B.Tech Project Report Reviewer
Powered by Groq API — 100% FREE
Get free API key at: https://console.groq.com
"""

import streamlit as st
from groq import Groq
import base64
import json
import io
import os
import time
import mammoth
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from pdf_generator import generate_full_report, generate_report_card, generate_comparison_table
import fitz  # PyMuPDF — extract text from PDF

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
- Body text: 12pt Regular Justified
- Figure caption BELOW figure: 11pt Regular Centred — format "Fig. X.Y: Description"
- Table caption ABOVE table: 11pt Bold Centred — format "Table X.Y: Description"
- Institute header: 9pt Bold Centred on every page except cover and separators

14 MANDATORY CHAPTERS:
Ch1 Introduction: 1.1 Project Overview, 1.2 Problem Statement, 1.3 Objectives, 1.4 Scope, 1.5 Organisation
Ch2 Previous Work: literature review with citations, min 7 sections, summary table
Ch3 System Analysis: 3.1 Identification of Need, 3.2 Preliminary Investigation
Ch4 Feasibility Study: Technical, Operational, Economic, Legal, Social + Summary
Ch5 Analysis: DFD Level 0, Level 1, Level 2, ER Diagram, Database Table Structures
Ch6 S/W Technology Paradigm: Waterfall model with diagram
Ch7 Methodology: Architecture + steps + Algorithms in bordered box (Courier New 11pt, Input/Output)
Ch8 S/W and H/W Requirements: Developer + User + Technology stack
Ch9 System Design: Modules + inter-module communication
Ch10 Screenshots: ACTUAL running app screenshots, colour
Ch11 Implementation and Maintenance: step-by-step + maintenance plan
Ch12 Testing: 8 types with test case tables (Unit, Integration, System, Acceptance, Performance, Security, Regression, UAT)
Ch13 System Security Measures
Ch14 Conclusion and Future Scope: future enhancements table with version/priority/effort

REFERENCES: Heading=REFERENCES, min 15, min 10 peer-reviewed, IEEE numbered [1][2], no Wikipedia.

GENERAL: No first-person (no I/we/our/my), no placeholder text, min 2 pages per chapter, total 40-80 pages.
"""

SYSTEM_PROMPT = f"""You are an expert, strict, and fair B.Tech project report reviewer for SSIPMT Raipur, Dept. of IT, Session 2025-2026.

Review the submitted student project report text against these official SSIPMT guidelines:
{GUIDELINES}

Be specific — cite actual content when identifying issues. Be thorough but fair.

Return ONLY a valid JSON object. No markdown, no backticks, no text outside JSON.

Required JSON structure:
{{"project_title":"string","report_type":"string","student_names":["array"],"guide_name":"string","overall_score":number,"overall_recommendation":"APPROVED or MINOR_REVISION or MAJOR_REVISION or REJECTED","executive_summary":"3-4 sentences","format_compliance":{{"score":number,"checks":[{{"item":"string","status":"PASS or FAIL or WARNING or CANNOT_VERIFY","detail":"string"}}]}},"front_matter":{{"score":number,"sections":[{{"name":"string","present":true,"issues":"string or null"}}]}},"chapters":[{{"number":number,"title":"string","present":true,"estimated_pages":number,"meets_2page_minimum":true,"score":number,"issues":["array"],"strengths":["array"],"feedback":"string"}}],"technical_elements":{{"score":number,"dfd_level0":{{"present":true,"issues":"null"}},"dfd_level1":{{"present":true,"issues":"null"}},"dfd_level2":{{"present":true,"issues":"null"}},"er_diagram":{{"present":true,"issues":"null"}},"table_structures":{{"present":true,"count":number,"issues":"null"}},"algorithms":{{"present":true,"count":number,"properly_formatted":true,"issues":"null"}},"waterfall_diagram":{{"present":true,"issues":"null"}},"testing_types":{{"count":number,"types_found":["array"],"issues":"null"}}}},"abstract":{{"score":number,"estimated_word_count":number,"within_300_500":true,"has_keywords":true,"keyword_count":number,"covers_problem":true,"covers_solution":true,"covers_technologies":true,"covers_results":true,"has_citations":false,"issues":["array"],"feedback":"string"}},"references":{{"score":number,"total_count":number,"meets_minimum_15":true,"peer_reviewed_count":number,"meets_10_peer_reviewed":true,"ieee_format":"FULL or PARTIAL or POOR","issues":["array"],"feedback":"string"}},"language_quality":{{"score":number,"first_person_violations":["array"],"grammar_quality":"POOR or FAIR or GOOD or EXCELLENT","technical_accuracy":"POOR or FAIR or GOOD or EXCELLENT","academic_tone":"POOR or FAIR or GOOD or EXCELLENT","placeholder_text_found":false,"feedback":"string"}},"critical_issues":["array"],"major_issues":["array"],"minor_issues":["array"],"strengths":["array"],"priority_action_list":[{{"priority":number,"action":"string","location":"string","severity":"CRITICAL or MAJOR or MINOR"}}]}}"""

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
def get_api_key():
    return (os.getenv("GROQ_API_KEY", "")
            or st.session_state.get("groq_key", ""))

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

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()

def extract_file(uploaded_file):
    """Extract text from PDF or DOCX."""
    name = uploaded_file.name.lower()
    raw  = uploaded_file.read()
    if name.endswith(".pdf"):
        text = extract_text_from_pdf(raw)
        if not text:
            raise ValueError("Could not extract text from this PDF. It may be scanned. Try DOCX.")
        return {"text": text, "name": uploaded_file.name}
    elif name.endswith(".docx"):
        result = mammoth.extract_raw_text({"file": io.BytesIO(raw)})
        if not result.value.strip():
            raise ValueError("Could not extract text from DOCX.")
        return {"text": result.value, "name": uploaded_file.name}
    raise ValueError("Unsupported file type. Upload PDF or DOCX only.")

def call_groq(file_data):
    """Send extracted text to Groq and get JSON review."""
    api_key = get_api_key()
    if not api_key:
        st.error("⚠️ No Groq API key found. Add it in the sidebar.")
        st.stop()

    client = Groq(api_key=api_key)

    # Groq context window is 128k tokens — truncate text to be safe
    text = file_data["text"][:35000]

    prompt = (
        f"B.Tech Project Report (file: {file_data['name']}):\n\n"
        f"{text}\n\n"
        f"Review this report against SSIPMT guidelines. Return only the JSON."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.1,
        max_tokens=4096,
    )

    raw   = response.choices[0].message.content
    clean = raw.replace("```json", "").replace("```", "").strip()
    start = clean.find("{")
    end   = clean.rfind("}") + 1
    if start >= 0 and end > start:
        clean = clean[start:end]
    return json.loads(clean)

# ─────────────────────────────────────────────
# DISPLAY REVIEW
# ─────────────────────────────────────────────
def show_review(rv):
    ws  = compute_weighted_score(rv)
    rec = rv.get("overall_recommendation", "")

    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.subheader(rv.get("project_title", "Untitled Report"))
        st.caption(f"**Student(s):** {', '.join(rv.get('student_names', ['—']))}  ·  **Guide:** {rv.get('guide_name', '—')}")
        st.write(rv.get("executive_summary", ""))
    with col2:
        st.metric("Weighted Score", f"{ws} / 100")
        st.caption(f"AI raw: {rv.get('overall_score', 0)}")
    with col3:
        st.metric("Decision", "")
        st.markdown(f"**{rec_icon(rec)}**")

    st.divider()

    cols = st.columns(6)
    for col, (name, key) in zip(cols, [
        ("Format","format_compliance"), ("Front Matter","front_matter"),
        ("Technical","technical_elements"), ("Abstract","abstract"),
        ("References","references"), ("Language","language_quality"),
    ]):
        s = rv.get(key, {}).get("score", 0)
        col.metric(name, f"{score_emoji(s)} {s}")

    st.divider()

    ci = rv.get("critical_issues", [])
    mi = rv.get("major_issues",   [])
    ni = rv.get("minor_issues",   [])
    if ci:
        with st.expander(f"🚨 Critical Issues ({len(ci)}) — Must fix before submission", expanded=True):
            for i in ci: st.markdown(f"- {i}")
    if mi:
        with st.expander(f"⚠️ Major Issues ({len(mi)})", expanded=True):
            for i in mi: st.markdown(f"- {i}")
    if ni:
        with st.expander(f"📝 Minor Issues ({len(ni)})"):
            for i in ni: st.markdown(f"- {i}")

    if rv.get("priority_action_list"):
        with st.expander("📋 Priority Action List", expanded=True):
            st.dataframe(pd.DataFrame(rv["priority_action_list"]), hide_index=True, use_container_width=True)

    fc = rv.get("format_compliance", {})
    if fc.get("checks"):
        with st.expander(f"📐 Format Compliance — Score: {fc.get('score', 0)}"):
            for c in fc["checks"]:
                icon = {"PASS":"✅","FAIL":"❌","WARNING":"⚠️","CANNOT_VERIFY":"❔"}.get(c["status"],"❔")
                st.markdown(f"{icon} **{c['item']}** — {c['detail']}")

    fm = rv.get("front_matter", {})
    if fm.get("sections"):
        with st.expander(f"📄 Front Matter — Score: {fm.get('score', 0)}"):
            cols2 = st.columns(3)
            for idx, s in enumerate(fm["sections"]):
                with cols2[idx % 3]:
                    st.markdown(f"{'✅' if s['present'] else '❌'} **{s['name']}**")
                    if s.get("issues"): st.caption(f"⚠ {s['issues']}")

    if rv.get("chapters"):
        with st.expander("📚 Chapter-by-Chapter Review"):
            for ch in rv["chapters"]:
                ok   = ch.get("present", False)
                warn = "" if ch.get("meets_2page_minimum", True) else "  ⚠️ Under 2-page minimum"
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{'✅' if ok else '❌'} Ch.{ch['number']}: {ch['title']}**{warn}")
                    st.caption(f"~{ch.get('estimated_pages',0)} pages")
                    if ch.get("feedback"): st.write(ch["feedback"])
                    for iss in ch.get("issues", []): st.markdown(f"  - ❌ {iss}")
                    for stt in ch.get("strengths", []): st.markdown(f"  - ✓ {stt}")
                with c2:
                    if ok: st.metric("", f"{score_emoji(ch.get('score',0))} {ch.get('score',0)}")
                st.divider()

    te = rv.get("technical_elements", {})
    if te:
        with st.expander(f"⚙️ Technical Elements — Score: {te.get('score',0)}"):
            for name, key in [
                ("DFD Level 0","dfd_level0"),("DFD Level 1","dfd_level1"),("DFD Level 2","dfd_level2"),
                ("ER Diagram","er_diagram"),("Database Table Structures","table_structures"),
                ("Algorithms","algorithms"),("Waterfall Model Diagram","waterfall_diagram"),
            ]:
                el = te.get(key)
                if not el: continue
                icon = "✅" if el.get("present") else "❌"
                cnt  = f" ({el['count']})" if "count" in el else ""
                st.markdown(f"{icon} **{name}**{cnt}")
                if el.get("issues"): st.caption(f"  ↳ {el['issues']}")
            tst = te.get("testing_types", {})
            st.markdown(f"**Testing:** {tst.get('count',0)}/8 types — {', '.join(tst.get('types_found',[]) or ['None'])}")

    ab = rv.get("abstract", {})
    if ab:
        with st.expander(f"📝 Abstract — Score: {ab.get('score',0)}"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"- Word count: ~{ab.get('estimated_word_count',0)} {'✅' if ab.get('within_300_500') else '❌'}")
                st.markdown(f"- Keywords: {'✅ '+str(ab.get('keyword_count',0)) if ab.get('has_keywords') else '❌ Missing'}")
                st.markdown(f"- Covers problem: {'✅' if ab.get('covers_problem') else '❌'}")
                st.markdown(f"- Covers solution: {'✅' if ab.get('covers_solution') else '❌'}")
            with c2:
                st.markdown(f"- Covers technologies: {'✅' if ab.get('covers_technologies') else '❌'}")
                st.markdown(f"- Covers results: {'✅' if ab.get('covers_results') else '❌'}")
                st.markdown(f"- No citations: {'✅' if not ab.get('has_citations') else '❌ Remove'}")
            if ab.get("feedback"): st.info(ab["feedback"])

    ref = rv.get("references", {})
    if ref:
        with st.expander(f"📖 References — Score: {ref.get('score',0)}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Total", f"{ref.get('total_count',0)}", delta=None if ref.get('meets_minimum_15') else "Need ≥15")
            c2.metric("Peer-reviewed", f"{ref.get('peer_reviewed_count',0)}", delta=None if ref.get('meets_10_peer_reviewed') else "Need ≥10")
            c3.metric("IEEE Format", ref.get("ieee_format","?"))
            for iss in ref.get("issues",[]): st.markdown(f"- ❌ {iss}")
            if ref.get("feedback"): st.info(ref["feedback"])

    lq = rv.get("language_quality", {})
    if lq:
        with st.expander(f"✍️ Language & Writing — Score: {lq.get('score',0)}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Grammar", lq.get("grammar_quality","—"))
            c2.metric("Technical Accuracy", lq.get("technical_accuracy","—"))
            c3.metric("Academic Tone", lq.get("academic_tone","—"))
            if lq.get("placeholder_text_found"):
                st.error("⚠️ Placeholder text found — replace before submission")
            if lq.get("first_person_violations"):
                st.warning("First-person violations:")
                for v in lq["first_person_violations"]: st.markdown(f'  - *"{v}"*')
            if lq.get("feedback"): st.info(lq["feedback"])

    if rv.get("strengths"):
        with st.expander("💪 Strengths"):
            for s in rv["strengths"]: st.markdown(f"✓ {s}")

    st.divider()
    st.subheader("📥 Download Reports")
    ws = compute_weighted_score(rv)
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
    st.caption("Dept. of IT · Session 2025–2026\n**100% Free — Powered by Groq**")
    st.divider()

    st.subheader("🔑 Groq API Key")
    env_key = os.getenv("GROQ_API_KEY", "")
    if env_key:
        st.success("✓ Key loaded")
    else:
        st.session_state["groq_key"] = st.text_input(
            "Paste your free Groq API key",
            type="password",
            help="Get free key at console.groq.com"
        )
        st.caption("🔗 [Get free key → console.groq.com](https://console.groq.com)")

    st.divider()

    st.subheader("⚖️ Scoring Weights")
    st.caption("Adjust dimension importance.")
    new_wt = {}
    for k, label in WEIGHT_INFO.items():
        new_wt[k] = st.slider(label, 5, 60, st.session_state.weights[k], key=f"w_{k}")
    st.session_state.weights = new_wt
    tot = sum(new_wt.values())
    if abs(tot - 100) < 1:
        st.success(f"Total: {tot}% ✓")
    else:
        st.warning(f"Total: {tot}% (target: 100%)")
    if st.button("↩ Reset Defaults"):
        st.session_state.weights = dict(DEFAULT_WEIGHTS)
        st.rerun()

    st.divider()
    st.caption("Free tier: **14,400 requests/day**\nNo credit card required.")

# ─────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["📋  Single Review", "📦  Batch Review"])

# ── SINGLE ──
with tab1:
    st.header("Single Report Review")
    uploaded = st.file_uploader("Upload student PDF or DOCX report",
                                type=["pdf","docx"], key="single_upload")
    if uploaded:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            ftype = "PDF" if uploaded.name.lower().endswith(".pdf") else "DOCX"
            st.info(f"📁 **{uploaded.name}** — {uploaded.size/1024/1024:.2f} MB  |  {ftype}")
        with col_b:
            start = st.button("🔍 Start Review", type="primary", use_container_width=True)

        if start:
            with st.spinner("Extracting text from document..."):
                try:
                    fd = extract_file(uploaded)
                except Exception as e:
                    st.error(str(e))
                    st.stop()

            with st.spinner("🤖 AI is reviewing the report... (30–60 seconds)"):
                try:
                    rv = call_groq(fd)
                    st.session_state.single_review = rv
                    st.success("✅ Review complete!")
                except Exception as e:
                    st.error(f"Review failed: {e}")

    if st.session_state.single_review:
        st.divider()
        show_review(st.session_state.single_review)

# ── BATCH ──
with tab2:
    st.header("Batch Review")
    st.caption("Upload all student reports at once. Reviewed one-by-one.")

    batch_files = st.file_uploader("Upload multiple PDF/DOCX reports",
                                   type=["pdf","docx"],
                                   accept_multiple_files=True,
                                   key="batch_upload")
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
                    rv = call_groq(fd)
                    ws = compute_weighted_score(rv)
                    results.append({"file": uf.name, "review": rv, "score": ws, "error": None})
                except Exception as e:
                    results.append({"file": uf.name, "review": None, "score": 0, "error": str(e)})
                prog.progress((idx + 1) / len(batch_files))
                if idx < len(batch_files) - 1:
                    time.sleep(2)

            st.session_state.batch_results = results
            done_n = len([r for r in results if not r["error"]])
            status_ph.success(f"✅ Done — {done_n}/{len(batch_files)} reviewed")

    if st.session_state.batch_results:
        st.divider()
        st.subheader("📊 Comparison Table")
        rows = []
        for r in st.session_state.batch_results:
            if r["error"]:
                rows.append({"File":r["file"],"Students":"—","Title":"ERROR","Score":0,
                             "Format":0,"Front Matter":0,"Technical":0,"Abstract":0,
                             "References":0,"Language":0,"Recommendation":"ERROR"})
            else:
                rv = r["review"]
                rows.append({
                    "File":          r["file"],
                    "Students":      ", ".join(rv.get("student_names",["—"])),
                    "Title":         rv.get("project_title","—")[:35],
                    "Score":         r["score"],
                    "Format":        rv.get("format_compliance",{}).get("score",0),
                    "Front Matter":  rv.get("front_matter",{}).get("score",0),
                    "Technical":     rv.get("technical_elements",{}).get("score",0),
                    "Abstract":      rv.get("abstract",{}).get("score",0),
                    "References":    rv.get("references",{}).get("score",0),
                    "Language":      rv.get("language_quality",{}).get("score",0),
                    "Recommendation":rv.get("overall_recommendation","—").replace("_"," "),
                })
        df = pd.DataFrame(rows).sort_values("Score", ascending=False)
        st.dataframe(df, hide_index=True, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📊 Download CSV", df.to_csv(index=False).encode(),
                               f"Batch_{datetime.now().strftime('%Y%m%d')}.csv",
                               "text/csv", use_container_width=True)
        with c2:
            try:
                cmp_pdf = generate_comparison_table(st.session_state.batch_results, st.session_state.weights)
                st.download_button("📄 Download PDF", cmp_pdf,
                                   f"Batch_{datetime.now().strftime('%Y%m%d')}.pdf",
                                   "application/pdf", use_container_width=True, type="primary")
            except Exception as e:
                st.error(str(e))

        st.divider()
        st.subheader("View Individual Review")
        done_r = [r for r in st.session_state.batch_results if not r["error"]]
        if done_r:
            sel_name = st.selectbox("Select report:", [r["file"] for r in done_r])
            sel = next(r for r in done_r if r["file"] == sel_name)
            show_review(sel["review"])
