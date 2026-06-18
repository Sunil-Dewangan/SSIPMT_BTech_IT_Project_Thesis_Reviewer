"""
PDF Report Generator — SSIPMT B.Tech Project Report Reviewer
Uses fpdf2
"""

from fpdf import FPDF
from datetime import datetime
import io

SSIPMT = "Shri Shankaracharya Institute of Professional Management & Technology, Raipur"
DEPT   = "Department of Information Technology  |  Session 2025-2026"

WEIGHT_NAMES = {
    "format":"Format Compliance","front_matter":"Front Matter","chapters":"Chapter Content",
    "technical":"Technical Elements","abstract":"Abstract Quality",
    "references":"References","language":"Language & Writing",
}

_R = {
    '\u2014':'-','\u2013':'-','\u2012':'-','\u2011':'-','\u2010':'-',
    '\u2026':'...','\u201c':'"','\u201d':'"','\u2018':"'",'\u2019':"'",
    '\u2022':'*','\u2023':'*','\u25cf':'*','\u2192':'->','\u2190':'<-',
    '\u2265':'>=','\u2264':'<=','\u00d7':'x','\u00f7':'/',
    '\u2713':'Yes','\u2717':'No','\u00b0':'deg','\u00ae':'(R)',
    '\u00a9':'(C)','\u00b1':'+/-','\u2248':'~=','\u2260':'!=',
    '\u221e':'inf','\u00a0':' ','\u200b':'','\u200e':'','\u200f':'','\ufeff':'',
    '\u2033':'"','\u2032':"'",'\u00e9':'e','\u00e8':'e','\u00ea':'e',
    '\u00e0':'a','\u00e2':'a','\u00e4':'a','\u00f6':'o','\u00fc':'u','\u00df':'ss',
}

def safe(text):
    if text is None: return ""
    text = str(text)
    for ch, rep in _R.items():
        text = text.replace(ch, rep)
    return text.encode('latin-1', 'replace').decode('latin-1')

def sc(s):
    if s >= 95: return (22,163,74)
    if s >= 75: return (37,99,235)
    if s >= 40: return (194,65,12)
    return (220,38,38)

def rec_color(rec):
    return {"APPROVED":(22,163,74),"MINOR_REVISION":(37,99,235),
            "MAJOR_REVISION":(194,65,12),"REJECTED":(220,38,38)}.get(rec,(100,100,100))

def rec_bg(rec):
    return {"APPROVED":(220,252,231),"MINOR_REVISION":(219,234,254),
            "MAJOR_REVISION":(254,215,170),"REJECTED":(254,226,226)}.get(rec,(243,244,246))

W = 170  # usable page width: 210mm - 20mm left - 20mm right

class BasePDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P",unit="mm",format="A4")
        self.set_auto_page_break(auto=True,margin=15)
        self.set_margins(20,20,20)

    def header(self):
        self.set_fill_color(30,58,138)
        self.rect(0,0,210,14,"F")
        self.set_font("Helvetica","B",7)
        self.set_text_color(255,255,255)
        self.set_y(4)
        self.cell(W,6,safe(SSIPMT+"  |  "+DEPT),align="C")
        self.set_text_color(0,0,0)
        self.set_y(18)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica","I",7)
        self.set_text_color(150,150,150)
        self.cell(W,6,safe(f"Page {self.page_no()}  |  Generated {datetime.now().strftime('%d %B %Y')}  |  AI-generated review - SSIPMT Dept. of IT"),align="C")
        self.set_text_color(0,0,0)

    def sec(self,text):
        self.ln(3)
        self.set_fill_color(30,58,138)
        self.set_text_color(255,255,255)
        self.set_font("Helvetica","B",9)
        self.cell(W,6,safe("  "+text),fill=True,ln=True)
        self.set_text_color(0,0,0)
        self.ln(1)

    def kv(self, label, value, lw=55, fill=False):
        """Key-value row with explicit widths — no cell(0,...) overflow."""
        vw = W - lw
        if fill: self.set_fill_color(249,250,251)
        else:    self.set_fill_color(255,255,255)
        self.set_font("Helvetica","B",8)
        self.cell(lw,5,safe(label),border="B",fill=fill)
        self.set_font("Helvetica","",8)
        self.cell(vw,5,safe(str(value))[:110],border="B",fill=fill,ln=True)

    def kv_wrap(self, label, value, lw=55, fill=False):
        """Key-value row where value may wrap onto multiple lines."""
        vw = W - lw
        if fill: self.set_fill_color(249,250,251)
        else:    self.set_fill_color(255,255,255)
        self.set_font("Helvetica","B",8)
        self.cell(lw,5,safe(label),border="B",fill=fill)
        self.set_font("Helvetica","",8)
        self.set_x(self.l_margin + lw)
        self.multi_cell(vw,5,safe(str(value)),border="B",fill=fill)

    def sc_cell(self,score,w=18,h=6):
        r,g,b=sc(score)
        self.set_text_color(r,g,b)
        self.set_font("Helvetica","B",9)
        self.cell(w,h,safe(str(score)),align="C",border=1)
        self.set_text_color(0,0,0)

    def bul(self,text,color=(80,30,20),indent=4):
        self.set_x(self.l_margin+indent)
        self.set_font("Helvetica","",8)
        self.set_text_color(*color)
        self.multi_cell(W-indent,4,safe("- "+str(text)))
        self.set_text_color(0,0,0)


def generate_full_report(review:dict, weights:dict, weighted_score:int, recommendation:str=None) -> bytes:
    pdf = BasePDF()
    pdf.add_page()
    rec = recommendation or review.get("overall_recommendation","")
    date_str = datetime.now().strftime("%d %B %Y")

    # ── Title ──
    pdf.ln(2)
    pdf.set_font("Helvetica","B",15)
    pdf.set_text_color(30,58,138)
    pdf.cell(W,9,"B.Tech Project Report - AI Review",align="C",ln=True)
    pdf.set_font("Helvetica","",8)
    pdf.set_text_color(100,100,100)
    pdf.cell(W,5,safe(date_str),align="C",ln=True)
    pdf.set_text_color(0,0,0)
    pdf.ln(2)

    # ── Report Info ──
    #pdf.sec("Report Information")
    #pdf.kv("Project Title", review.get("project_title","-"),          fill=True)
    #pdf.kv_wrap("Student(s)",  ", ".join(review.get("student_names",["-"])), fill=False)
    #pdf.kv("Guide",         review.get("guide_name","-"),             fill=True)
    #pdf.kv("Report Type",   review.get("report_type","B.Tech Project Report"), fill=False)
    pdf.sec("Report Information")
    for i,(k,v) in enumerate([
        ("Project Title", review.get("project_title","-")),
        ("Student(s)",    ", ".join(review.get("student_names",["-"]))),
        ("Guide",         review.get("guide_name","-")),
        ("Report Type",   review.get("report_type","B.Tech Project Report")),
    ]):
        pdf.kv(k, str(v)[:95], fill=(i%2==0))

    # ── Score Summary ──
    pdf.ln(4)
    pdf.sec("Score Summary")
    rb=rec_bg(rec); rc=rec_color(rec)
    pdf.set_fill_color(30,58,138); pdf.set_text_color(255,255,255)
    pdf.set_font("Helvetica","B",30)
    pdf.cell(36,22,safe(str(weighted_score)),border=1,fill=True,align="C")
    pdf.set_fill_color(*rb); pdf.set_text_color(*rc)
    pdf.set_font("Helvetica","B",10)
    pdf.cell(65,22,safe(rec.replace("_"," ")),border=1,fill=True,align="C")
    pdf.set_fill_color(248,250,252); pdf.set_text_color(60,60,60)
    pdf.set_font("Helvetica","",8)
    pdf.cell(69,22,safe(f"  AI raw: {review.get('overall_score',0)}/100  Weighted: {weighted_score}/100"),border=1,fill=True,ln=True)
    pdf.set_text_color(0,0,0); pdf.ln(2)
    pdf.set_font("Helvetica","I",7); pdf.set_text_color(100,100,100)
    pdf.cell(W,4,"Thresholds:  >=95=APPROVED  |  75-94=MINOR REVISION  |  40-74=MAJOR REVISION  |  <40=REJECTED",ln=True)
    pdf.set_text_color(0,0,0); pdf.ln(2)
    pdf.set_fill_color(239,246,255); pdf.set_font("Helvetica","I",8)
    pdf.multi_cell(W,4,safe(review.get("executive_summary","")),border=1,fill=True)
    pdf.ln(3)

    # ── Dimension Scores ──
    pdf.sec("Dimension Score Breakdown")
    pdf.set_font("Helvetica","B",8)
    pdf.set_fill_color(30,58,138); pdf.set_text_color(255,255,255)
    for hdr,w2 in [("Dimension",72),("Score",18),("Weight",16),("Assessment",64)]:
        pdf.cell(w2,6,safe(hdr),border=1,fill=True)
    pdf.ln(); pdf.set_text_color(0,0,0)
    dim_data=[
        ("Format Compliance",  review.get("format_compliance",{}).get("score",0),  weights.get("format",15)),
        ("Front Matter",       review.get("front_matter",{}).get("score",0),        weights.get("front_matter",10)),
        ("Technical Elements", review.get("technical_elements",{}).get("score",0), weights.get("technical",20)),
        ("Abstract Quality",   review.get("abstract",{}).get("score",0),            weights.get("abstract",5)),
        ("References",         review.get("references",{}).get("score",0),          weights.get("references",15)),
        ("Language & Writing", review.get("language_quality",{}).get("score",0),   weights.get("language",10)),
    ]
    for i,(name,score,wt) in enumerate(dim_data):
        pdf.set_fill_color(255,255,255) if i%2==0 else pdf.set_fill_color(249,250,251)
        pdf.set_font("Helvetica","",8); pdf.cell(72,5,safe(name),border=1,fill=True)
        pdf.sc_cell(score,18,5)
        pdf.cell(16,5,safe(f"{wt}%"),border=1,align="C",fill=True)
        assess="Good" if score>=80 else ("Needs improvement" if score>=60 else "Significant work required")
        pdf.set_font("Helvetica","",7); pdf.cell(64,5,safe(assess),border=1,fill=True,ln=True)
    pdf.ln(3)

    # ── Issues ──
    ci=review.get("critical_issues",[]); mi=review.get("major_issues",[]); ni=review.get("minor_issues",[])
    if ci:
        pdf.sec(f"Critical Issues ({len(ci)}) - Must Fix Before Submission")
        for iss in ci: pdf.bul(str(iss)[:120],color=(127,29,29))
    if mi:
        pdf.sec(f"Major Issues ({len(mi)}) - Significant Corrections Required")
        for iss in mi: pdf.bul(str(iss)[:120],color=(124,45,18))
    if ni:
        pdf.sec(f"Minor Issues ({len(ni)}) - Recommended Improvements")
        for iss in ni: pdf.bul(str(iss)[:120],color=(113,63,18))

    # ── Priority Action List ──
    pal=review.get("priority_action_list",[])
    if pal:
        pdf.add_page()
        pdf.sec("Priority Action List")
        pdf.set_font("Helvetica","B",8)
        pdf.set_fill_color(30,58,138); pdf.set_text_color(255,255,255)
        for hdr,w2 in [("#",8),("Action Required",110),("Location",44),("Severity",18)]:
            pdf.cell(w2,6,safe(hdr),border=1,fill=True)
        pdf.ln(); pdf.set_text_color(0,0,0)
        for i,a in enumerate(pal):
            pdf.set_fill_color(255,255,255) if i%2==0 else pdf.set_fill_color(249,250,251)
            pdf.set_font("Helvetica","B",8)
            pdf.cell(8,5,safe(str(a.get("priority",""))),border=1,fill=True,align="C")
            pdf.set_font("Helvetica","",8)
            pdf.cell(110,5,safe(str(a.get("action",""))[:70]),border=1,fill=True)
            pdf.cell(44,5,safe(str(a.get("location",""))[:28]),border=1,fill=True)
            sev=a.get("severity","")
            sev_col={"CRITICAL":(220,38,38),"MAJOR":(234,88,12),"MINOR":(37,99,235)}.get(sev,(0,0,0))
            pdf.set_text_color(*sev_col); pdf.set_font("Helvetica","B",7)
            pdf.cell(18,5,safe(sev),border=1,align="C",fill=True,ln=True)
            pdf.set_text_color(0,0,0)

    # ── Chapter Review ──
    pdf.add_page()
    pdf.sec("Chapter-by-Chapter Review")
    pdf.set_font("Helvetica","B",7)
    pdf.set_fill_color(30,58,138); pdf.set_text_color(255,255,255)
    for hdr,w2 in [("#",7),("Chapter Title",68),("Present",18),("~Pages",13),("Score",14),("Key Issues",50)]:
        pdf.cell(w2,6,safe(hdr),border=1,fill=True,align="C" if w2<20 else "L")
    pdf.ln(); pdf.set_text_color(0,0,0)
    for i,ch in enumerate(review.get("chapters",[])):
        pdf.set_fill_color(255,255,255) if i%2==0 else pdf.set_fill_color(249,250,251)
        pdf.set_font("Helvetica","B",7)
        pdf.cell(7,5,safe(str(ch.get("number",""))),border=1,fill=True,align="C")
        pdf.set_font("Helvetica","",7)
        pdf.cell(68,5,safe(str(ch.get("title",""))[:42]),border=1,fill=True)
        pdf.cell(18,5,safe("Yes" if ch.get("present") else "MISSING"),border=1,align="C",fill=True)
        pdf.cell(13,5,safe(f"~{ch.get('estimated_pages',0)}"),border=1,align="C",fill=True)
        pdf.sc_cell(ch.get("score",0),14,5)
        iss_txt=safe(("; ".join(ch.get("issues",[])[:1])[:46]) if ch.get("issues") else (ch.get("feedback","")[:46] if ch.get("feedback") else "-"))
        pdf.set_font("Helvetica","",6); pdf.cell(50,5,iss_txt,border=1,fill=True,ln=True)

    # ── Technical Elements ──
    te=review.get("technical_elements",{})
    if te:
        pdf.ln(3); pdf.sec("Technical Elements")
        for nm,k in [("DFD Level 0","dfd_level0"),("DFD Level 1","dfd_level1"),("DFD Level 2","dfd_level2"),
            ("ER Diagram","er_diagram"),("Database Table Structures","table_structures"),
            ("Algorithms","algorithms"),("Waterfall Model Diagram","waterfall_diagram")]:
            el=te.get(k)
            if not el: continue
            present=el.get("present",False)
            pdf.set_font("Helvetica","",8); pdf.cell(85,5,safe(nm))
            pdf.set_text_color(22,163,74) if present else pdf.set_text_color(220,38,38)
            pdf.set_font("Helvetica","B",8)
            cnt=f" ({el['count']})" if "count" in el else ""
            pdf.cell(30,5,safe(("PRESENT"+cnt) if present else "MISSING"))
            pdf.set_text_color(0,0,0); pdf.set_font("Helvetica","",7)
            pdf.cell(55,5,safe(str(el.get("issues","") or "")[:55]),ln=True)
        tst=te.get("testing_types",{})
        pdf.set_font("Helvetica","B",8)
        pdf.cell(W,5,safe(f"Testing: {tst.get('count',0)}/8 types - {', '.join(tst.get('types_found',[]) or ['None identified'])}"),ln=True)

    # ── Strengths ──
    if review.get("strengths"):
        pdf.ln(2); pdf.sec("Strengths")
        for s in review["strengths"]: pdf.bul(str(s)[:120],color=(22,101,52))

    # ── Sign-off ──
    pdf.add_page(); pdf.sec("Reviewer Sign-off"); pdf.ln(8)
    pdf.set_font("Helvetica","",9)
    pdf.cell(80,5,"Guide:",ln=False)
    pdf.cell(70,5,"Project In-Charge:",ln=False)
    pdf.cell(30,5,safe(f"Date: {date_str}"),ln=True)
    pdf.ln(14)
    pdf.cell(80,0,"_"*34,ln=False); pdf.cell(70,0,"_"*28,ln=False); pdf.cell(30,0,"_"*13,ln=True)
    pdf.ln(3); pdf.set_font("Helvetica","I",7); pdf.set_text_color(100,100,100)
    pdf.cell(80,4,"Name & Signature",ln=False); pdf.cell(70,4,"Signature",ln=False); pdf.cell(30,4,"HoD Signature",ln=True)
    pdf.set_text_color(0,0,0); pdf.ln(8)
    pdf.set_font("Helvetica","I",7); pdf.set_text_color(150,150,150)
    pdf.multi_cell(W,4,"This report was generated by an AI system. It is a review aid for supervising faculty. Final decisions remain with the Department of IT, SSIPMT Raipur.")

    buf=io.BytesIO(); pdf.output(buf); return buf.getvalue()


def generate_report_card(review:dict, weights:dict, weighted_score:int, recommendation:str=None) -> bytes:
    pdf=BasePDF(); pdf.add_page()
    rec = recommendation or review.get("overall_recommendation","")
    rc=rec_color(rec); rb=rec_bg(rec)
    date_str=datetime.now().strftime("%d %B %Y")

    # ── Title ──
    pdf.ln(2)
    pdf.set_font("Helvetica","B",14); pdf.set_text_color(30,58,138)
    pdf.cell(W,9,"STUDENT REVIEW REPORT CARD",align="C",ln=True)
    pdf.set_font("Helvetica","",8); pdf.set_text_color(100,100,100)
    pdf.cell(W,5,safe(f"B.Tech Project Report  |  {date_str}"),align="C",ln=True)
    pdf.set_text_color(0,0,0); pdf.ln(3)

    # ── Project Info — same KV table as Full Review, no overflow ──
    lw=55; vw=W-lw
    #pdf.kv("Project Title", review.get("project_title","-"),               fill=True)
   # pdf.kv_wrap("Student(s)",  ", ".join(review.get("student_names",["-"])),  fill=False)
    #pdf.kv("Guide",         review.get("guide_name","-"),                  fill=True)
    #pdf.kv("Report Type",   review.get("report_type","B.Tech Project Report"), fill=False)
    pdf.sec("Report Information")
    for i,(k,v) in enumerate([
        ("Project Title", review.get("project_title","-")),
        ("Student(s)",    ", ".join(review.get("student_names",["-"]))),
        ("Guide",         review.get("guide_name","-")),
        ("Report Type",   review.get("report_type","B.Tech Project Report")),
    ]):
        pdf.kv(k, str(v)[:95], fill=(i%2==0))
    pdf.ln(3)

    # ── Score + Recommendation ──
    score_w=38; rec_w=W-score_w
    pdf.set_fill_color(30,58,138); pdf.set_text_color(255,255,255)
    pdf.set_font("Helvetica","B",30)
    pdf.cell(score_w,22,safe(str(weighted_score)),border=1,fill=True,align="C")
    pdf.set_fill_color(*rb); pdf.set_text_color(*rc)
    pdf.set_font("Helvetica","B",12)
    pdf.cell(rec_w,22,safe(rec.replace("_"," ")),border=1,fill=True,align="C",ln=True)
    pdf.set_text_color(0,0,0)
    pdf.set_font("Helvetica","I",7); pdf.set_text_color(100,100,100)
    pdf.cell(W,4,safe(f"Score:{weighted_score}/100  AI raw:{review.get('overall_score',0)}/100  |  >=95=Approved  75-94=Minor  40-74=Major  <40=Rejected"),ln=True)
    pdf.set_text_color(0,0,0); pdf.ln(3)

    # ── Dimension Table ──
    dim_w=72; sc_w=18; wt_w=18; st_w=W-dim_w-sc_w-wt_w
    pdf.set_font("Helvetica","B",8)
    pdf.set_fill_color(30,58,138); pdf.set_text_color(255,255,255)
    pdf.cell(dim_w,6,"Dimension",border=1,fill=True)
    pdf.cell(sc_w,6,"Score",border=1,fill=True,align="C")
    pdf.cell(wt_w,6,"Weight",border=1,fill=True,align="C")
    pdf.cell(st_w,6,"Status",border=1,fill=True,ln=True)
    pdf.set_text_color(0,0,0)
    dims=[
        ("Format Compliance",  review.get("format_compliance",{}).get("score",0),  weights.get("format",15)),
        ("Front Matter",       review.get("front_matter",{}).get("score",0),        weights.get("front_matter",10)),
        ("Technical Elements", review.get("technical_elements",{}).get("score",0), weights.get("technical",20)),
        ("Abstract Quality",   review.get("abstract",{}).get("score",0),            weights.get("abstract",5)),
        ("References",         review.get("references",{}).get("score",0),          weights.get("references",15)),
        ("Language & Writing", review.get("language_quality",{}).get("score",0),   weights.get("language",10)),
    ]
    for i,(name,score,wt) in enumerate(dims):
        pdf.set_fill_color(255,255,255) if i%2==0 else pdf.set_fill_color(249,250,251)
        pdf.set_font("Helvetica","",8); pdf.cell(dim_w,5,safe(name),border=1,fill=True)
        pdf.sc_cell(score,sc_w,5)
        pdf.cell(wt_w,5,safe(f"{wt}%"),border=1,align="C",fill=True)
        st2="Good" if score>=80 else ("Needs improvement" if score>=60 else "Significant revision needed")
        pdf.set_font("Helvetica","",7); pdf.cell(st_w,5,safe(st2),border=1,fill=True,ln=True)
    pdf.ln(3)

    # ── Priority Actions ──
    pal=review.get("priority_action_list",[])[:5]
    if pal:
        lbl_w=28; act_w=W-lbl_w
        pdf.set_font("Helvetica","B",9); pdf.set_text_color(30,58,138)
        pdf.cell(W,6,"Priority Actions for Student:",ln=True); pdf.set_text_color(0,0,0)
        for a in pal:
            sev=a.get("severity","")
            sc2={"CRITICAL":(220,38,38),"MAJOR":(234,88,12),"MINOR":(37,99,235)}.get(sev,(0,0,0))
            bg2={"CRITICAL":(254,242,242),"MAJOR":(255,247,237),"MINOR":(239,246,255)}.get(sev,(249,250,251))
            pdf.set_fill_color(*bg2); pdf.set_font("Helvetica","B",8); pdf.set_text_color(*sc2)
            pdf.cell(lbl_w,5,safe(f"{a.get('priority','')}. [{sev}]"),border="L",fill=True)
            pdf.set_text_color(0,0,0); pdf.set_font("Helvetica","",8)
            pdf.cell(act_w,5,safe(str(a.get("action",""))[:80]+" - "+str(a.get("location",""))),border="B",fill=True,ln=True)
    pdf.ln(5)

    # ── Signature ──
    pdf.set_draw_color(180,180,180)
    pdf.line(pdf.l_margin,pdf.get_y(),210-pdf.r_margin,pdf.get_y()); pdf.ln(3)
    sig1=80; sig2=60; sig3=W-sig1-sig2
    pdf.set_font("Helvetica","",9)
    pdf.cell(sig1,5,"Guide:",ln=False); pdf.cell(sig2,5,"Project In-Charge",ln=False)
    pdf.cell(sig3,5,safe(f"Date: {date_str}"),ln=True); pdf.ln(10)
    pdf.cell(sig1,0,"_"*32,ln=False); pdf.cell(sig2,0,"_"*26,ln=False); pdf.cell(sig3,0,"_"*14,ln=True); pdf.ln(3)
    pdf.set_font("Helvetica","I",7); pdf.set_text_color(150,150,150)
    pdf.cell(sig1,4,"Name & Signature",ln=False); pdf.cell(sig2,4,"Signature",ln=False); pdf.cell(sig3,4,"HoD Signature",ln=True)

    buf=io.BytesIO(); pdf.output(buf); return buf.getvalue()


def _ws(review, weights):
    wt=weights or {}; total=sum(wt.values()) or 1
    chs=review.get("chapters",[]); ch_avg=(sum(c.get("score",0) for c in chs)/len(chs)) if chs else 0
    dim={"format":review.get("format_compliance",{}).get("score",0),
         "front_matter":review.get("front_matter",{}).get("score",0),"chapters":ch_avg,
         "technical":review.get("technical_elements",{}).get("score",0),
         "abstract":review.get("abstract",{}).get("score",0),
         "references":review.get("references",{}).get("score",0),
         "language":review.get("language_quality",{}).get("score",0)}
    return round(sum(dim.get(k,0)*(wt.get(k,0)/total) for k in wt))

def generate_comparison_table(batch_results:list, weights:dict) -> bytes:
    pdf=BasePDF(); pdf.add_page()
    date_str=datetime.now().strftime("%d %B %Y")
    pdf.ln(2); pdf.set_font("Helvetica","B",13); pdf.set_text_color(30,58,138)
    pdf.cell(W,9,"BATCH REVIEW COMPARISON TABLE",align="C",ln=True)
    pdf.set_font("Helvetica","",8); pdf.set_text_color(100,100,100)
    done=[r for r in batch_results if not r.get("error")]
    pdf.cell(W,5,safe(f"Generated {date_str}  |  {len(done)} report(s) reviewed"),align="C",ln=True)
    pdf.set_text_color(0,0,0); pdf.ln(4)
    wt_note="Weights: "+" | ".join(f"{WEIGHT_NAMES[k]}={v}%" for k,v in weights.items() if k in WEIGHT_NAMES)
    pdf.set_font("Helvetica","I",7); pdf.set_fill_color(239,246,255)
    pdf.multi_cell(W,4,safe(wt_note),border=1,fill=True); pdf.ln(3)
    pdf.set_font("Helvetica","B",7); pdf.set_fill_color(30,58,138); pdf.set_text_color(255,255,255)
    for hdr,w2 in [("#",6),("File",38),("Student(s)",36),("Title",36),("Score",12),("Fmt",9),("FM",8),("Tech",9),("Abs",8),("Ref",8),("Lang",8)]:
        pdf.cell(w2,6,safe(hdr),border=1,fill=True,align="C" if w2<15 else "L")
    pdf.ln(); pdf.set_text_color(0,0,0)
    for i,r in enumerate(batch_results):
        if r.get("error"):
            pdf.set_fill_color(254,226,226); pdf.set_font("Helvetica","I",7)
            pdf.cell(6,5,safe(str(i+1)),border=1,fill=True,align="C")
            pdf.cell(38,5,safe(r["file"][:22]),border=1,fill=True)
            pdf.cell(76,5,safe("ERROR: "+str(r.get("error",""))[:55]),border=1,fill=True,ln=True)
            continue
        rv=r["review"]; ws=_ws(rv,weights)
        pdf.set_fill_color(255,255,255) if i%2==0 else pdf.set_fill_color(249,250,251)
        pdf.set_font("Helvetica","B",7); pdf.cell(6,5,safe(str(i+1)),border=1,fill=True,align="C")
        pdf.set_font("Helvetica","",7)
        pdf.cell(38,5,safe(r["file"][:22]),border=1,fill=True)
        pdf.cell(36,5,safe(", ".join(rv.get("student_names",["-"]))[:22]),border=1,fill=True)
        pdf.cell(36,5,safe(str(rv.get("project_title",""))[:22]),border=1,fill=True)
        pdf.sc_cell(ws,12,5)
        for k in ["format_compliance","front_matter","technical_elements","abstract","references","language_quality"]:
            s2=rv.get(k,{}).get("score",0)
            w2=[9,8,9,8,8,8][["format_compliance","front_matter","technical_elements","abstract","references","language_quality"].index(k)]
            pdf.sc_cell(s2,w2,5)
        pdf.ln()
    buf=io.BytesIO(); pdf.output(buf); return buf.getvalue()
