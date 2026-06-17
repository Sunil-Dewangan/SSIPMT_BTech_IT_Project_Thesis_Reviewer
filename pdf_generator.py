"""
PDF Report Generator for SSIPMT B.Tech Project Report Reviewer
Uses fpdf2 — pip install fpdf2
"""

from fpdf import FPDF
from datetime import datetime
import io


SSIPMT = "Shri Shankaracharya Institute of Professional Management & Technology, Raipur"
DEPT   = "Department of Information Technology  |  Session 2025-2026"

WEIGHT_NAMES = {
    "format":       "Format Compliance",
    "front_matter": "Front Matter",
    "chapters":     "Chapter Content",
    "technical":    "Technical Elements",
    "abstract":     "Abstract Quality",
    "references":   "References",
    "language":     "Language & Writing",
}


def sc(s):
    """Score colour tuple (R,G,B)."""
    if s >= 80: return (22, 163, 74)
    if s >= 60: return (217, 119, 6)
    return (220, 38, 38)

def rec_color(rec):
    return {
        "APPROVED":      (22, 163, 74),
        "MINOR_REVISION":(161, 98, 7),
        "MAJOR_REVISION":(194, 65, 12),
        "REJECTED":      (220, 38, 38),
    }.get(rec, (100, 100, 100))


# ─────────────────────────────────────────────
class BasePDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        
        
        
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(20, 20, 20)

    def header(self):
        self.set_fill_color(30, 58, 138)
        self.rect(0, 0, 210, 16, "F")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(255, 255, 255)
        self.set_y(5)
        self.cell(0, 6, SSIPMT + "  |  " + DEPT, align="C")
        self.set_text_color(0, 0, 0)
        self.set_y(20)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, f"Page {self.page_no()}  |  Generated {datetime.now().strftime('%d %B %Y')}  |  AI-generated review", align="C")
        self.set_text_color(0, 0, 0)

    def section_title(self, text):
        self.ln(4)
        self.set_fill_color(30, 58, 138)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, "  " + text, fill=True, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def row_pair(self, label, value, label_w=60, fill=False):
        if fill:
            self.set_fill_color(249, 250, 251)
        self.set_font("Helvetica", "B", 9)
        self.cell(label_w, 6, label, border="B", fill=fill)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, str(value), border="B", fill=fill, ln=True)

    def score_cell(self, score, w=20, h=8):
        r, g, b = sc(score)
        self.set_text_color(r, g, b)
        self.set_font("Helvetica", "B", 10)
        self.cell(w, h, str(score), align="C", border=1)
        self.set_text_color(0, 0, 0)

    def bullet(self, text, color=(0, 0, 0), indent=5):
        self.set_x(self.l_margin + indent)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*color)
        # Wrap long lines
        self.multi_cell(0, 5, u"\u2022  " + str(text))
        self.set_text_color(0, 0, 0)

    def safe_text(self, text):
        return str(text or "").encode("latin-1", "replace").decode("latin-1")


# ─────────────────────────────────────────────
def generate_full_report(review: dict, weights: dict, weighted_score: int) -> bytes:
    """Generate a full multi-page review report PDF."""
    pdf = BasePDF()
    pdf.add_page()

    rec = review.get("overall_recommendation", "")
    date_str = datetime.now().strftime("%d %B %Y")

    # ── Title Block ──
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, "B.Tech Project Report — AI Review", align="C", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, date_str, align="C", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # ── Info Table ──
    pdf.section_title("Report Information")
    info_rows = [
        ("Project Title",  review.get("project_title", "—")),
        ("Student(s)",     ", ".join(review.get("student_names", ["—"]))),
        ("Guide",          review.get("guide_name", "—")),
        ("Report Type",    review.get("report_type", "B.Tech Project Report")),
    ]
    for i, (k, v) in enumerate(info_rows):
        pdf.row_pair(k, str(v)[:90], fill=(i % 2 == 0))

    # ── Score Summary ──
    pdf.ln(4)
    pdf.section_title("Score Summary")
    # Big score box
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(40, 20, str(weighted_score), border=1, fill=True, align="C")
    # Recommendation
    rco = rec_color(rec)
    pdf.set_fill_color(*rco)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(60, 20, rec.replace("_", " "), border=1, fill=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(249, 250, 251)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 20, "  AI raw score: " + str(review.get("overall_score", 0)) + "/100\n  Weighted score uses custom dimension weights.", border=1, fill=True, ln=True)
    pdf.ln(2)

    # Executive summary
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_fill_color(239, 246, 255)
    pdf.multi_cell(0, 5, review.get("executive_summary", ""), border=1, fill=True)
    pdf.ln(3)

    # ── Dimension Scores ──
    pdf.section_title("Dimension Score Breakdown")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(243, 244, 246)
    pdf.cell(70, 7, "Dimension", border=1, fill=True)
    pdf.cell(20, 7, "Score", border=1, fill=True, align="C")
    pdf.cell(15, 7, "Weight", border=1, fill=True, align="C")
    pdf.cell(0, 7, "Assessment", border=1, fill=True, ln=True)

    dims = [
        ("Format Compliance",  review.get("format_compliance", {}).get("score", 0),  weights.get("format", 15)),
        ("Front Matter",       review.get("front_matter", {}).get("score", 0),        weights.get("front_matter", 10)),
        ("Technical Elements", review.get("technical_elements", {}).get("score", 0), weights.get("technical", 20)),
        ("Abstract",           review.get("abstract", {}).get("score", 0),            weights.get("abstract", 5)),
        ("References",         review.get("references", {}).get("score", 0),          weights.get("references", 15)),
        ("Language & Writing", review.get("language_quality", {}).get("score", 0),   weights.get("language", 10)),
    ]
    for i, (name, score, wt) in enumerate(dims):
        if i % 2 == 0: pdf.set_fill_color(255, 255, 255)
        else: pdf.set_fill_color(249, 250, 251)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(70, 6, name, border=1, fill=True)
        pdf.score_cell(score, 20, 6)
        pdf.cell(15, 6, f"{wt}%", border=1, align="C")
        assess = "Good" if score >= 80 else ("Needs improvement" if score >= 60 else "Significant work required")
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 6, assess, border=1, ln=True)
    pdf.ln(3)

    # ── Issues ──
    ci = review.get("critical_issues", [])
    mi = review.get("major_issues", [])
    ni = review.get("minor_issues", [])

    if ci:
        pdf.section_title(f"Critical Issues ({len(ci)}) — Must Fix Before Submission")
        for iss in ci:
            pdf.bullet(str(iss)[:110], color=(127, 29, 29))

    if mi:
        pdf.section_title(f"Major Issues ({len(mi)}) — Significant Corrections Required")
        for iss in mi:
            pdf.bullet(str(iss)[:110], color=(124, 45, 18))

    if ni:
        pdf.section_title(f"Minor Issues ({len(ni)}) — Recommended Improvements")
        for iss in ni:
            pdf.bullet(str(iss)[:110], color=(113, 63, 18))

    # ── Chapter Review ──
    pdf.add_page()
    pdf.section_title("Chapter-by-Chapter Review")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(243, 244, 246)
    for hdr, w in [("#",8),("Chapter Title",70),("Present",18),("Pages",14),("Score",16),("Key Issues",54)]:
        pdf.cell(w, 7, hdr, border=1, fill=True, align="C" if w < 20 else "L")
    pdf.ln()

    for i, ch in enumerate(review.get("chapters", [])):
        fill = i % 2 == 0
        pdf.set_fill_color(255, 255, 255) if fill else pdf.set_fill_color(249, 250, 251)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(8, 6, str(ch.get("number", "")), border=1, fill=True, align="C")
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(70, 6, str(ch.get("title", ""))[:38], border=1, fill=True)
        pdf.cell(18, 6, "Yes" if ch.get("present") else "MISSING", border=1, align="C", fill=True)
        pdf.cell(14, 6, f"~{ch.get('estimated_pages', 0)}", border=1, align="C", fill=True)
        pdf.score_cell(ch.get("score", 0), 16, 6)
        issues_txt = "; ".join(ch.get("issues", [])[:2])[:50] if ch.get("issues") else "—"
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(54, 6, issues_txt, border=1, fill=True, ln=True)

    # ── Priority Action List ──
    pal = review.get("priority_action_list", [])
    if pal:
        pdf.ln(3)
        pdf.section_title("Priority Action List")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(243, 244, 246)
        for hdr, w in [("#",8),("Action Required",110),("Location",42),("Severity",20)]:
            pdf.cell(w, 7, hdr, border=1, fill=True)
        pdf.ln()
        for i, a in enumerate(pal):
            pdf.set_fill_color(255, 255, 255) if i % 2 == 0 else pdf.set_fill_color(249, 250, 251)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(8, 6, str(a.get("priority", "")), border=1, fill=True, align="C")
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(110, 6, str(a.get("action", ""))[:68], border=1, fill=True)
            pdf.cell(42, 6, str(a.get("location", ""))[:25], border=1, fill=True)
            sev = a.get("severity", "")
            sev_col = {"CRITICAL": (220, 38, 38), "MAJOR": (234, 88, 12), "MINOR": (202, 138, 4)}.get(sev, (0,0,0))
            pdf.set_text_color(*sev_col)
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(20, 6, sev, border=1, align="C", fill=True, ln=True)
            pdf.set_text_color(0, 0, 0)

    # ── Technical Elements ──
    te = review.get("technical_elements", {})
    if te:
        pdf.ln(3)
        pdf.section_title("Technical Elements")
        items = [
            ("DFD Level 0",            te.get("dfd_level0")),
            ("DFD Level 1",            te.get("dfd_level1")),
            ("DFD Level 2",            te.get("dfd_level2")),
            ("ER Diagram",             te.get("er_diagram")),
            ("Database Table Structures", te.get("table_structures")),
            ("Algorithms",             te.get("algorithms")),
            ("Waterfall Model Diagram",te.get("waterfall_diagram")),
        ]
        for name, el in items:
            if not el: continue
            status = "PRESENT" if el.get("present") else "MISSING"
            color  = (22, 163, 74) if el.get("present") else (220, 38, 38)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(80, 5, name)
            pdf.set_text_color(*color)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(25, 5, status)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 8)
            issue_txt = str(el.get("issues", "") or "")[:70]
            pdf.cell(0, 5, issue_txt, ln=True)

        tst = te.get("testing_types", {})
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, f"Testing: {tst.get('count', 0)}/8 types — {', '.join(tst.get('types_found', []) or ['None identified'])}", ln=True)

    # ── Signature Block ──
    pdf.add_page()
    pdf.section_title("Reviewer Sign-off")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 10)
    cols_w = [80, 70, 30]
    pdf.cell(cols_w[0], 6, "Reviewed by:", ln=False)
    pdf.cell(cols_w[1], 6, "Designation:", ln=False)
    pdf.cell(cols_w[2], 6, f"Date: {date_str}", ln=True)
    pdf.ln(15)
    pdf.cell(cols_w[0], 0, "_" * 35, ln=False)
    pdf.cell(cols_w[1], 0, "_" * 30, ln=False)
    pdf.cell(cols_w[2], 0, "_" * 12, ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(cols_w[0], 5, "Name & Designation", ln=False)
    pdf.cell(cols_w[1], 5, "Department / SSIPMT Raipur", ln=False)
    pdf.cell(cols_w[2], 5, "Signature", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 5, "This report was generated by an AI system (Claude, Anthropic). "
                         "It is intended as a review aid for the supervising faculty. "
                         "Final decisions remain with the Department of IT, SSIPMT Raipur.")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ─────────────────────────────────────────────
def generate_report_card(review: dict, weights: dict, weighted_score: int) -> bytes:
    """Generate a single-page student report card PDF."""
    pdf = BasePDF()
    pdf.add_page()

    rec = review.get("overall_recommendation", "")
    rco = rec_color(rec)
    date_str = datetime.now().strftime("%d %B %Y")

    # Title
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 9, "STUDENT REVIEW REPORT CARD", align="C", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"B.Tech Project Report  |  {date_str}", align="C", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # Top info row
    pdf.set_fill_color(239, 246, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(0, 6, f"Project: {review.get('project_title', '—')}", border=1, fill=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Student(s): {', '.join(review.get('student_names', ['—']))}   |   Guide: {review.get('guide_name', '—')}", border="B", ln=True)
    pdf.ln(3)

    # Score + Recommendation
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 32)
    pdf.cell(40, 22, str(weighted_score), border=1, fill=True, align="C")
    pdf.set_fill_color(*rco)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(80, 22, rec.replace("_", " "), border=1, fill=True, align="C")
    pdf.set_fill_color(249, 250, 251)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 22, f"  Score: {weighted_score}/100\n  AI raw: {review.get('overall_score', 0)}/100\n  Custom weights applied", border=1, fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # Dimension table
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    for hdr, w in [("Dimension", 70), ("Score", 18), ("Weight", 18), ("Status", 74)]:
        pdf.cell(w, 7, hdr, border=1, fill=True, align="C" if w < 30 else "L")
    pdf.ln()
    pdf.set_text_color(0, 0, 0)

    dims = [
        ("Format Compliance",   review.get("format_compliance", {}).get("score", 0),   weights.get("format", 15)),
        ("Front Matter",        review.get("front_matter", {}).get("score", 0),         weights.get("front_matter", 10)),
        ("Technical Elements",  review.get("technical_elements", {}).get("score", 0),  weights.get("technical", 20)),
        ("Abstract Quality",    review.get("abstract", {}).get("score", 0),             weights.get("abstract", 5)),
        ("References",          review.get("references", {}).get("score", 0),           weights.get("references", 15)),
        ("Language & Writing",  review.get("language_quality", {}).get("score", 0),    weights.get("language", 10)),
    ]
    for i, (name, score, wt) in enumerate(dims):
        pdf.set_fill_color(255, 255, 255) if i % 2 == 0 else pdf.set_fill_color(249, 250, 251)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(70, 6, name, border=1, fill=True)
        pdf.score_cell(score, 18, 6)
        pdf.cell(18, 6, f"{wt}%", border=1, align="C", fill=True)
        status = "Good — meets standard" if score >= 80 else ("Needs improvement" if score >= 60 else "Significant revision required")
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(74, 6, status, border=1, fill=True, ln=True)
    pdf.ln(3)

    # Top 5 priority actions
    pal = review.get("priority_action_list", [])[:5]
    if pal:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 6, "Priority Actions for Student:", ln=True)
        pdf.set_text_color(0, 0, 0)
        for a in pal:
            sev = a.get("severity", "")
            sev_col = {"CRITICAL": (220, 38, 38), "MAJOR": (234, 88, 12), "MINOR": (202, 138, 4)}.get(sev, (0,0,0))
            pdf.set_fill_color(254, 242, 242) if sev == "CRITICAL" else (pdf.set_fill_color(255, 247, 237) if sev == "MAJOR" else pdf.set_fill_color(254, 252, 232))
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*sev_col)
            pdf.cell(20, 5, f"{a['priority']}. [{sev}]", border="L", fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 5, str(a.get("action", ""))[:85] + f"  —  {a.get('location', '')}", border="B", fill=True, ln=True)
    pdf.ln(5)

    # Signature
    pdf.set_draw_color(180, 180, 180)
    pdf.line(pdf.l_margin, pdf.get_y(), 210 - pdf.r_margin, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(80, 5, "Reviewer:", ln=False)
    pdf.cell(70, 5, "Dept. of IT, SSIPMT Raipur", ln=False)
    pdf.cell(0, 5, f"Date: {date_str}", ln=True)
    pdf.ln(10)
    pdf.cell(80, 0, "_" * 32, ln=False)
    pdf.cell(70, 0, "_" * 28, ln=False)
    pdf.cell(0, 0, "_" * 15, ln=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(80, 4, "Name & Signature", ln=False)
    pdf.cell(70, 4, "Department Stamp", ln=False)
    pdf.cell(0, 4, "Signature", ln=True)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ─────────────────────────────────────────────
def _weighted_score(review, weights):
    """Compute weighted score inline (no circular import)."""
    wt = weights or {}
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
    return round(sum(dim.get(k, 0) * (wt.get(k, 0) / total) for k in wt))


def generate_comparison_table(batch_results: list, weights: dict) -> bytes:
    """Generate a batch comparison table PDF."""
    pdf = BasePDF()
    pdf.add_page()
    date_str = datetime.now().strftime("%d %B %Y")

    # Title
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 9, "BATCH REVIEW COMPARISON TABLE", align="C", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    done = [r for r in batch_results if not r.get("error")]
    pdf.cell(0, 5, f"Generated {date_str}  |  {len(done)} report(s) reviewed", align="C", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Weight note
    wt_note = "  Weights: " + " | ".join(f"{WEIGHT_NAMES[k]}={v}%" for k, v in weights.items())
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_fill_color(239, 246, 255)
    pdf.multi_cell(0, 5, wt_note, border=1, fill=True)
    pdf.ln(3)

    # Table header
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    cols = [("#",6),("File",40),("Student(s)",38),("Title",38),("Score",12),
            ("Fmt",10),("FM",9),("Tech",10),("Abs",9),("Ref",9),("Lang",9)]
    for hdr, w in cols:
        pdf.cell(w, 7, hdr, border=1, fill=True, align="C" if w < 20 else "L")
    pdf.ln()
    pdf.set_text_color(0, 0, 0)

    for i, r in enumerate(batch_results):
        if r.get("error"):
            pdf.set_fill_color(254, 226, 226)
            pdf.set_font("Helvetica", "I", 7)
            pdf.cell(6, 5, str(i+1), border=1, fill=True, align="C")
            pdf.cell(40, 5, r["file"][:22], border=1, fill=True)
            pdf.cell(0, 5, "ERROR: " + r["error"][:60], border=1, fill=True, ln=True)
            continue

        rv = r["review"]
        ws = _weighted_score(rv, weights)
        fill_c = (255, 255, 255) if i % 2 == 0 else (249, 250, 251)
        pdf.set_fill_color(*fill_c)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(6, 5, str(i+1), border=1, fill=True, align="C")
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(40, 5, r["file"][:22], border=1, fill=True)
        pdf.cell(38, 5, ", ".join(rv.get("student_names", ["—"]))[:22], border=1, fill=True)
        pdf.cell(38, 5, str(rv.get("project_title", ""))[:22], border=1, fill=True)
        pdf.score_cell(ws, 12, 5)
        for k in ["format_compliance", "front_matter", "technical_elements", "abstract", "references", "language_quality"]:
            s = rv.get(k, {}).get("score", 0)
            w_col = [10,9,10,9,9,9][[
                "format_compliance","front_matter","technical_elements",
                "abstract","references","language_quality"].index(k)]
            pdf.score_cell(s, w_col, 5)
        pdf.ln()

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
