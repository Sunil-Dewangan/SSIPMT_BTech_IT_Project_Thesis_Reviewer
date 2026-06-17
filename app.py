"""
SSIPMT B.Tech Project Thesis Report Reviewer
Department of Information Technology, SSIPMT Raipur
Developed by Sunil Kumar Dewangan
Powered by Groq API — 100% FREE
Get free API key at: https://console.groq.com
"""

import streamlit as st
from groq import Groq
import json
import io
import os
import time
import mammoth
import pandas as pd
import fitz  # PyMuPDF
from dotenv import load_dotenv
from datetime import datetime
from pdf_generator import generate_full_report, generate_report_card, generate_comparison_table

load_dotenv()

MAX_PAGES = 80  # SSIPMT guidelines: 40-80 pages

# ─────────────────────────────────────────────
# PAGE CONFIG — No Sidebar
# ─────────────────────────────────────────────
st.set_page_config(page_title="SSIPMT Thesis Reviewer", page_icon="🎓",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.stMetric label { font-size: 11px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding:18px 0 10px 0;'>
  <span style='font-size:36px;'>🎓</span>
  <h2 style='margin:4px 0 2px 0; color:#1e3a8a; font-size:26px;'>
    SSIPMT Project Thesis Report Reviewer
  </h2>
  <p style='margin:0; color:#6b7280; font-size:13px;'>
    Department of Information Technology &nbsp;|&nbsp;
    Developed by <strong>Sunil Kumar Dewangan</strong>
  </p>
</div>
<hr style='border:none; border-top:2px solid #e5e7eb; margin-bottom:18px;'/>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GUIDELINES
# ─────────────────────────────────────────────
GUIDELINES = """
SSIPMT B.Tech Project Report Guidelines — Dept. of IT

PAGE SETUP: A4, all margins 1 inch, Times New Roman 12pt, 1.5 line spacing, 0pt paragraph spacing, box page border on every page.

MANDATORY STRUCTURE: 1.Cover(no#) 2.Declaration(i) 3.Supervisor Certificate(ii) 4.Examiner Certificate(iii) 5.Acknowledgement(iv) 6.List of Abbreviations(v) 7.List of Figures(vi) 8.Table of Contents(vii) 9.Abstract(viii,300-500 words,Keywords 5-8) 10.Chapter Separators(no#) 11.Chapters 1-14(Arabic) 12.References

HEADING STYLES: Chapter separator:22pt Bold CAPS Centred. Chapter content:16pt Bold CAPS Centred. Section(1.1):12pt Bold Left. Body:12pt Regular Justified. Fig caption(BELOW):11pt Regular Centred "Fig.X.Y:Desc". Table caption(ABOVE):11pt Bold Centred "Table X.Y:Desc". Institute header:9pt Bold Centred on all pages except cover/separators.

14 MANDATORY CHAPTERS:
Ch1 Introduction: 1.1 Project Overview, 1.2 Problem Statement, 1.3 Objectives, 1.4 Scope, 1.5 Organisation
Ch2 Previous Work: literature review with citations, min 7 sections, summary table
Ch3 System Analysis: 3.1 Identification of Need, 3.2 Preliminary Investigation
Ch4 Feasibility Study: Technical, Operational, Economic, Legal, Social + Summary
Ch5 Analysis: DFD Level 0, Level 1, Level 2, ER Diagram, Database Table Structures
Ch6 S/W Technology Paradigm: Waterfall model with diagram
Ch7 Methodology: Architecture + steps + Algorithms (bordered box, Courier New 11pt, Input/Output)
Ch8 S/W and H/W Requirements: Developer + User + Technology stack
Ch9 System Design: Modules + inter-module communication
Ch10 Screenshots: ACTUAL running app screenshots, colour
Ch11 Implementation and Maintenance: step-by-step + maintenance plan
Ch12 Testing: 8 types with test case tables (Unit, Integration, System, Acceptance, Performance, Security, Regression, UAT)
Ch13 System Security Measures
Ch14 Conclusion and Future Scope: future enhancements table with version/priority/effort

REFERENCES: min 15, min 10 peer-reviewed, IEEE numbered [1][2], no Wikipedia.
GENERAL: No first-person (no I/we/our/my), no placeholder text, min 2 pages per chapter, total 40-80 pages.
"""

def build_system_prompt(session, sub_name, sub_code, semester, fulfillment):
    return f"""You are a strict, thorough, and fair B.Tech project report reviewer for SSIPMT Raipur, Dept. of IT.

Review context:
- Session: {session}
- Subject: {sub_name} (Code: {sub_code})
- Semester: {semester}
- Degree: {fulfillment}

Official SSIPMT Guidelines:
{GUIDELINES}

Be specific — cite actual content when identifying issues. Be thorough but fair.

Return ONLY valid JSON, no markdown, no backticks, no text outside JSON:
{{"project_title":"string","report_type":"string","student_names":["array"],"guide_name":"string","overall_score":number,"overall_recommendation":"APPROVED or MINOR_REVISION or MAJOR_REVISION or REJECTED","executive_summary":"3-4 sentences","format_compliance":{{"score":number,"checks":[{{"item":"string","status":"PASS or FAIL or WARNING or CANNOT_VERIFY","detail":"string"}}]}},"front_matter":{{"score":number,"sections":[{{"name":"string","present":true,"issues":"string or null"}}]}},"chapters":[{{"number":number,"title":"string","present":true,"estimated_pages":number,"meets_2page_minimum":true,"score":number,"issues":["array"],"strengths":["array"],"feedback":"string"}}],"technical_elements":{{"score":number,"dfd_level0":{{"present":true,"issues":"null"}},"dfd_level1":{{"present":true,"issues":"null"}},"dfd_level2":{{"present":true,"issues":"null"}},"er_diagram":{{"present":true,"issues":"null"}},"table_structures":{{"present":true,"count":number,"issues":"null"}},"algorithms":{{"present":true,"count":number,"properly_formatted":true,"issues":"null"}},"waterfall_diagram":{{"present":true,"issues":"null"}},"testing_types":{{"count":number,"types_found":["array"],"issues":"null"}}}},"abstract":{{"score":number,"estimated_word_count":number,"within_300_500":true,"has_keywords":true,"keyword_count":number,"covers_problem":true,"covers_solution":true,"covers_technologies":true,"covers_results":true,"has_citations":false,"issues":["array"],"feedback":"string"}},"references":{{"score":number,"total_count":number,"meets_minimum_15":true,"peer_reviewed_count":number,"meets_10_peer_reviewed":true,"ieee_format":"FULL or PARTIAL or POOR","issues":["array"],"feedback":"string"}},"language_quality":{{"score":number,"first_person_violations":["array"],"grammar_quality":"POOR or FAIR or GOOD or EXCELLENT","technical_accuracy":"POOR or FAIR or GOOD or EXCELLENT","academic_tone":"POOR or FAIR or GOOD or EXCELLENT","placeholder_text_found":false,"feedback":"string"}},"critical_issues":["array"],"major_issues":["array"],"minor_issues":["array"],"strengths":["array"],"priority_action_list":[{{"priority":number,"action":"string","location":"string","severity":"CRITICAL or MAJOR or MINOR"}}]}}"""

# ─────────────────────────────────────────────
# DEFAULTS
# ─────────────────────────────────────────────
DEFAULT_WEIGHTS = {"format":15,"front_matter":10,"chapters":25,"technical":20,"abstract":5,"references":15,"language":10}
WEIGHT_INFO = {"format":"Format","front_matter":"Front Matter","chapters":"Chapters",
               "technical":"Technical","abstract":"Abstract","references":"References","language":"Language"}
SESSIONS = ["2025-26","2024-25","2026-27","2027-28","2023-24"]

for k,v in {"weights":dict(DEFAULT_WEIGHTS),"single_review":None,"batch_results":[]}.items():
    if k not in st.session_state: st.session_state[k]=v

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_api_key():
    raw = os.getenv("GROQ_API_KEY","")
    if not raw:
        try: raw = st.secrets.get("GROQ_API_KEY","")
        except: pass
    if not raw: raw = st.session_state.get("groq_key","")
    return raw.strip().strip("\"'") if raw else ""

def score_emoji(s): return "🟢" if s>=80 else ("🟡" if s>=60 else "🔴")

def rec_icon(rec):
    return {"APPROVED":"✅ APPROVED","MINOR_REVISION":"⚠️ MINOR REVISION",
            "MAJOR_REVISION":"🟠 MAJOR REVISION","REJECTED":"❌ REJECTED"}.get(rec,rec)

def fulfillment_text(sem):
    if sem==8: return "In Fulfillment of the Requirements for the Award of B.Tech in Information Technology"
    return "In Partial Fulfillment of the Requirements for the Award of B.Tech in Information Technology"

def compute_weighted_score(review):
    wt=st.session_state.weights; total=sum(wt.values()) or 1
    chs=review.get("chapters",[])
    ch_avg=(sum(c.get("score",0) for c in chs)/len(chs)) if chs else 0
    dim={"format":review.get("format_compliance",{}).get("score",0),
         "front_matter":review.get("front_matter",{}).get("score",0),"chapters":ch_avg,
         "technical":review.get("technical_elements",{}).get("score",0),
         "abstract":review.get("abstract",{}).get("score",0),
         "references":review.get("references",{}).get("score",0),
         "language":review.get("language_quality",{}).get("score",0)}
    return round(sum(dim[k]*(wt[k]/total) for k in wt))

def override_recommendation(weighted_score):
    """Override AI recommendation based on weighted score thresholds."""
    if weighted_score >= 85:
        return "APPROVED"
    elif weighted_score >= 75:
        return "MINOR_REVISION"
    elif weighted_score >= 40:
        return "MAJOR_REVISION"
    else:
        return "REJECTED"

def count_pdf_pages(pdf_bytes):
    doc=fitz.open(stream=pdf_bytes,filetype="pdf"); n=len(doc); doc.close(); return n

def extract_text_from_pdf(pdf_bytes, max_chars=25000):
    """Extract text — front-heavy (75% front, 25% back) to capture structure + references."""
    doc=fitz.open(stream=pdf_bytes,filetype="pdf"); total=len(doc)
    front_end=int(total*0.75)
    front_text="".join(doc[i].get_text() for i in range(front_end))
    back_text="".join(doc[i].get_text() for i in range(front_end,total))
    doc.close()
    front_limit=int(max_chars*0.75); back_limit=max_chars-front_limit
    result=front_text[:front_limit]
    if back_text.strip():
        result+=f"\n\n[--- Pages {front_end+1}-{total} ---]\n\n"+back_text[:back_limit]
    return result.strip()

def extract_file(uploaded_file):
    """Extract text from PDF or DOCX. Checks page limit."""
    name=uploaded_file.name.lower(); raw=uploaded_file.read()
    if name.endswith(".pdf"):
        pages=count_pdf_pages(raw)
        if pages>MAX_PAGES:
            raise ValueError(f"This report has **{pages} pages**. Maximum allowed is **{MAX_PAGES} pages** (SSIPMT guideline: 40–80 pages). Please reduce the report size and re-upload.")
        text=extract_text_from_pdf(raw)
        if not text.strip():
            raise ValueError("Could not extract text. PDF may be scanned/image-based. Convert to DOCX and try again.")
        return {"text":text,"name":uploaded_file.name,"pages":pages}
    elif name.endswith(".docx"):
        # FIX: pass BytesIO directly (not as dict) to avoid 'seek' error
        result=mammoth.extract_raw_text(io.BytesIO(raw))
        text=result.value
        if not text.strip(): raise ValueError("Could not extract text from DOCX.")
        est_pages=len(text.split())//300
        if est_pages>MAX_PAGES:
            raise ValueError(f"Document estimated at ~{est_pages} pages. Maximum is {MAX_PAGES} pages.")
        return {"text":text[:25000],"name":uploaded_file.name,"pages":est_pages}
    raise ValueError("Upload PDF or DOCX only.")

def robust_json_parse(raw):
    """Robustly extract JSON even if response is truncated."""
    clean = raw.replace("```json","").replace("```","").strip()
    start = clean.find("{")
    if start < 0:
        raise ValueError("No JSON found in response")
    # Walk to find matching closing brace
    depth=0; end_pos=-1; in_str=False; esc=False
    for i,ch in enumerate(clean[start:],start):
        if esc: esc=False; continue
        if ch=="\\" and in_str: esc=True; continue
        if ch=='"' and not esc: in_str=not in_str; continue
        if in_str: continue
        if ch=="{": depth+=1
        elif ch=="}":
            depth-=1
            if depth==0: end_pos=i+1; break
    if end_pos>start:
        try: return json.loads(clean[start:end_pos])
        except: pass
    # Fallback: try rfind
    end_pos=clean.rfind("}")+1
    if start>=0 and end_pos>start:
        try: return json.loads(clean[start:end_pos])
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse JSON: {e}")
    raise ValueError("No valid JSON in response")

def call_groq(file_data, system_prompt):
    """Send extracted text to Groq and get JSON review."""
    api_key=get_api_key()
    if not api_key: st.error("⚠️ No Groq API key found."); st.stop()

    client=Groq(api_key=api_key)
    prompt=(f"B.Tech Project Report ({file_data['name']}, ~{file_data.get('pages','?')} pages):\n\n"
            f"{file_data['text']}\n\nReview against SSIPMT guidelines. Return only the JSON.")

    response=client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":system_prompt},
                  {"role":"user","content":prompt}],
        temperature=0.1, max_tokens=4096,
    )
    raw=response.choices[0].message.content
    return robust_json_parse(raw)

# ─────────────────────────────────────────────
# DISPLAY REVIEW
# ─────────────────────────────────────────────
def show_review(rv):
    ws=compute_weighted_score(rv)
    rec=override_recommendation(ws)
    c1,c2,c3=st.columns([4,1,1])
    with c1:
        st.subheader(rv.get("project_title","Untitled"))
        st.caption(f"**Student(s):** {', '.join(rv.get('student_names',['—']))}  ·  **Guide:** {rv.get('guide_name','—')}")
        st.write(rv.get("executive_summary",""))
    with c2: st.metric("Weighted Score",f"{ws}/100"); st.caption(f"AI raw: {rv.get('overall_score',0)}")
    with c3: st.metric("Decision",""); st.markdown(f"**{rec_icon(rec)}**")
    st.caption("Score thresholds:  >=85 = APPROVED  |  75-84 = MINOR REVISION  |  40-74 = MAJOR REVISION  |  <40 = REJECTED")
    st.divider()

    cols=st.columns(6)
    for col,(name,key) in zip(cols,[("Format","format_compliance"),("Front Matter","front_matter"),
        ("Technical","technical_elements"),("Abstract","abstract"),("References","references"),("Language","language_quality")]):
        col.metric(name,f"{score_emoji(rv.get(key,{}).get('score',0))} {rv.get(key,{}).get('score',0)}")
    st.divider()

    for issues,label,exp in [(rv.get("critical_issues",[]),"🚨 Critical Issues — Must fix before submission",True),
        (rv.get("major_issues",[]),"⚠️ Major Issues",True),(rv.get("minor_issues",[]),"📝 Minor Issues",False)]:
        if issues:
            with st.expander(f"{label} ({len(issues)})",expanded=exp):
                for i in issues: st.markdown(f"- {i}")

    if rv.get("priority_action_list"):
        with st.expander("📋 Priority Action List",expanded=True):
            st.dataframe(pd.DataFrame(rv["priority_action_list"]),hide_index=True,use_container_width=True)

    fc=rv.get("format_compliance",{})
    if fc.get("checks"):
        with st.expander(f"📐 Format Compliance — Score: {fc.get('score',0)}"):
            for c in fc["checks"]:
                icon={"PASS":"✅","FAIL":"❌","WARNING":"⚠️","CANNOT_VERIFY":"❔"}.get(c["status"],"❔")
                st.markdown(f"{icon} **{c['item']}** — {c['detail']}")

    fm=rv.get("front_matter",{})
    if fm.get("sections"):
        with st.expander(f"📄 Front Matter — Score: {fm.get('score',0)}"):
            cols2=st.columns(3)
            for idx,s in enumerate(fm["sections"]):
                with cols2[idx%3]:
                    st.markdown(f"{'✅' if s['present'] else '❌'} **{s['name']}**")
                    if s.get("issues"): st.caption(f"⚠ {s['issues']}")

    if rv.get("chapters"):
        with st.expander("📚 Chapter-by-Chapter Review"):
            for ch in rv["chapters"]:
                ok=ch.get("present",False); warn="" if ch.get("meets_2page_minimum",True) else "  ⚠️ Under 2-page min"
                c1,c2=st.columns([5,1])
                with c1:
                    st.markdown(f"**{'✅' if ok else '❌'} Ch.{ch['number']}: {ch['title']}**{warn}")
                    st.caption(f"~{ch.get('estimated_pages',0)} pages")
                    if ch.get("feedback"): st.write(ch["feedback"])
                    for iss in ch.get("issues",[]): st.markdown(f"  - ❌ {iss}")
                    for stt in ch.get("strengths",[]): st.markdown(f"  - ✓ {stt}")
                with c2:
                    if ok: st.metric("",f"{score_emoji(ch.get('score',0))} {ch.get('score',0)}")
                st.divider()

    te=rv.get("technical_elements",{})
    if te:
        with st.expander(f"⚙️ Technical Elements — Score: {te.get('score',0)}"):
            for nm,k in [("DFD Level 0","dfd_level0"),("DFD Level 1","dfd_level1"),("DFD Level 2","dfd_level2"),
                ("ER Diagram","er_diagram"),("Database Tables","table_structures"),
                ("Algorithms","algorithms"),("Waterfall Diagram","waterfall_diagram")]:
                el=te.get(k)
                if not el: continue
                cnt=f" ({el['count']})" if "count" in el else ""
                st.markdown(f"{'✅' if el.get('present') else '❌'} **{nm}**{cnt}")
                if el.get("issues"): st.caption(f"  ↳ {el['issues']}")
            tst=te.get("testing_types",{})
            st.markdown(f"**Testing:** {tst.get('count',0)}/8 — {', '.join(tst.get('types_found',[]) or ['None'])}")

    ab=rv.get("abstract",{})
    if ab:
        with st.expander(f"📝 Abstract — Score: {ab.get('score',0)}"):
            c1,c2=st.columns(2)
            with c1:
                st.markdown(f"- Words: ~{ab.get('estimated_word_count',0)} {'✅' if ab.get('within_300_500') else '❌'}")
                st.markdown(f"- Keywords: {'✅ '+str(ab.get('keyword_count',0)) if ab.get('has_keywords') else '❌ Missing'}")
                st.markdown(f"- Covers problem: {'✅' if ab.get('covers_problem') else '❌'}")
                st.markdown(f"- Covers solution: {'✅' if ab.get('covers_solution') else '❌'}")
            with c2:
                st.markdown(f"- Covers technologies: {'✅' if ab.get('covers_technologies') else '❌'}")
                st.markdown(f"- Covers results: {'✅' if ab.get('covers_results') else '❌'}")
                st.markdown(f"- No citations: {'✅' if not ab.get('has_citations') else '❌ Remove'}")
            if ab.get("feedback"): st.info(ab["feedback"])

    ref=rv.get("references",{})
    if ref:
        with st.expander(f"📖 References — Score: {ref.get('score',0)}"):
            c1,c2,c3=st.columns(3)
            c1.metric("Total",ref.get("total_count",0),delta=None if ref.get("meets_minimum_15") else "Need ≥15")
            c2.metric("Peer-reviewed",ref.get("peer_reviewed_count",0),delta=None if ref.get("meets_10_peer_reviewed") else "Need ≥10")
            c3.metric("IEEE Format",ref.get("ieee_format","?"))
            for iss in ref.get("issues",[]): st.markdown(f"- ❌ {iss}")
            if ref.get("feedback"): st.info(ref["feedback"])

    lq=rv.get("language_quality",{})
    if lq:
        with st.expander(f"✍️ Language & Writing — Score: {lq.get('score',0)}"):
            c1,c2,c3=st.columns(3)
            c1.metric("Grammar",lq.get("grammar_quality","—"))
            c2.metric("Technical Accuracy",lq.get("technical_accuracy","—"))
            c3.metric("Academic Tone",lq.get("academic_tone","—"))
            if lq.get("placeholder_text_found"): st.error("⚠️ Placeholder text found — replace before submission")
            if lq.get("first_person_violations"):
                st.warning("First-person violations:")
                for v in lq["first_person_violations"]: st.markdown(f'  - *"{v}"*')
            if lq.get("feedback"): st.info(lq["feedback"])

    if rv.get("strengths"):
        with st.expander("💪 Strengths"):
            for s in rv["strengths"]: st.markdown(f"✓ {s}")

    st.divider(); st.subheader("📥 Download Reports")
    ws=compute_weighted_score(rv); d1,d2=st.columns(2)
    with d1:
        try:
            pdf=generate_full_report(rv,st.session_state.weights,ws)
            fn=f"Review_{rv.get('project_title','report')[:30].replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button("📄 Full Review Report (PDF)",pdf,fn,"application/pdf",use_container_width=True,type="primary")
        except Exception as e: st.error(f"PDF error: {e}")
    with d2:
        try:
            card=generate_report_card(rv,st.session_state.weights,ws)
            fn2=f"Card_{rv.get('project_title','report')[:30].replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button("🪪 Student Report Card (PDF)",card,fn2,"application/pdf",use_container_width=True)
        except Exception as e: st.error(f"Card error: {e}")

# ─────────────────────────────────────────────
# API KEY
# ─────────────────────────────────────────────
if not get_api_key():
    with st.expander("🔑 Groq API Key Required", expanded=True):
        st.session_state["groq_key"]=st.text_input(
            "Paste your free Groq API key (stored only for this session)",
            type="password", help="Get free key at console.groq.com")
        st.caption("🔗 [Get free key → console.groq.com](https://console.groq.com)")
else:
    st.caption("✅ Groq API key loaded")

# ─────────────────────────────────────────────
# REPORT INFORMATION FORM
# ─────────────────────────────────────────────
st.subheader("📋 Report Information")
c1,c2,c3,c4=st.columns(4)
with c1: session=st.selectbox("Academic Session",SESSIONS,index=0)
with c2: sub_name=st.text_input("Subject Name",placeholder="e.g. Major Project")
with c3: sub_code=st.text_input("Subject Code",placeholder="e.g. CS801")
with c4: semester=st.selectbox("Semester",[1,2,3,4,5,6,7,8],index=7)

ff=fulfillment_text(semester)
if semester==8: st.success(f"📜 **8th Semester →** {ff}")
else: st.info(f"📜 **{semester}th Semester →** {ff}")

# ─────────────────────────────────────────────
# SCORING WEIGHTS (collapsed)
# ─────────────────────────────────────────────
with st.expander("⚖️ Scoring Weights (click to adjust)", expanded=False):
    st.caption("Adjust how much each dimension counts toward the final score. Total should be 100%.")
    new_wt={}; wcols=st.columns(7)
    for col,(k,label) in zip(wcols,WEIGHT_INFO.items()):
        with col: new_wt[k]=st.number_input(label,5,60,st.session_state.weights[k],5,key=f"w_{k}")
    st.session_state.weights=new_wt; tot=sum(new_wt.values())
    if abs(tot-100)<1: st.success(f"Total: {tot}% ✓")
    else: st.warning(f"Total: {tot}% — should be 100%")
    if st.button("↩ Reset Defaults"): st.session_state.weights=dict(DEFAULT_WEIGHTS); st.rerun()

st.divider()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, = st.tabs(["📋  Single Review"])

with tab1:
    st.info(f"📌 Maximum **{MAX_PAGES} pages** per report (SSIPMT guideline: 40–80 pages). Files exceeding this limit will not be processed.")
    uploaded=st.file_uploader("Drag and drop PDF or DOCX file here",type=["pdf","docx"],
                               key="single_upload",help=f"PDF or DOCX · Max {MAX_PAGES} pages · Text-based PDFs only")
    if uploaded:
        ca,cb=st.columns([3,1])
        with ca: st.info(f"📁 **{uploaded.name}** — {uploaded.size/1024/1024:.2f} MB")
        with cb: start=st.button("🔍 Start Review",type="primary",use_container_width=True)

        if start:
            if not sub_name.strip(): st.warning("⚠️ Please enter the Subject Name above first."); st.stop()
            if not sub_code.strip(): st.warning("⚠️ Please enter the Subject Code above first."); st.stop()

            with st.spinner("Checking document..."):
                try:
                    fd=extract_file(uploaded)
                    st.caption(f"✅ {fd['pages']} pages · {len(fd['text']):,} chars sent for review")
                except Exception as e: st.error(str(e)); st.stop()

            sys_prompt=build_system_prompt(session,sub_name,sub_code,semester,ff)
            with st.spinner("🤖 AI reviewing... (30–60 seconds)"):
                try:
                    rv=call_groq(fd,sys_prompt)
                    st.session_state.single_review=rv; st.success("✅ Review complete!")
                except Exception as e:
                    if "413" in str(e) or "rate_limit" in str(e).lower():
                        st.error("⚠️ Request too large for Groq free tier. The report text has been automatically trimmed — please try again.")
                    else: st.error(f"Review failed: {e}")

    if st.session_state.single_review:
        if st.button("🔄 Review Another Report", type="secondary"):
            st.session_state.single_review = None
            st.rerun()
        st.divider()
        show_review(st.session_state.single_review)
