"""
MaintSignal - PDF Report Generator
Generates a branded, professional assessment report for client delivery.

Usage:
    from report_generator import ReportGenerator
    
    generator = ReportGenerator(
        company_name="Acme Manufacturing",
        plant_name="Houston Plant",
        assessment_date="2025-06-15"
    )
    generator.generate(quality_results, downtime_results, failure_results, financial_results)
    generator.save("acme_assessment_report.pdf")

Dependencies:
    pip install fpdf2
"""

from fpdf import FPDF
from datetime import datetime
import os


class MaintSignalPDF(FPDF):
    """Custom PDF class with MaintSignal branding."""

    # Brand colors (RGB)
    DARK_BG = (10, 12, 16)
    CARD_BG = (18, 21, 28)
    ACCENT = (34, 214, 138)
    TEXT = (226, 228, 234)
    TEXT_MUTED = (122, 129, 153)
    DANGER = (240, 88, 88)
    WARNING = (240, 168, 48)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    def __init__(self, company_name="", plant_name="", assessment_date=""):
        super().__init__()
        self.company_name = company_name
        self.plant_name = plant_name
        self.assessment_date = assessment_date or datetime.now().strftime("%B %d, %Y")

        # Use built-in fonts - Helvetica for clean professional look
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if self.page_no() == 1:
            return  # Skip header on cover page

        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 8, "MAINTSIGNAL - MAINTENANCE INTELLIGENCE ASSESSMENT", align="L")
        self.cell(0, 8, f"{self.company_name} | {self.assessment_date}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 35, 48)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 8, "CONFIDENTIAL - Prepared by MaintSignal", align="L")
        self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", align="R")

    def add_cover_page(self):
        """Generate the cover page."""
        self.add_page()
        self.set_fill_color(*self.DARK_BG)
        self.rect(0, 0, 210, 297, "F")

        # Logo area
        self.ln(50)
        self.set_font("Helvetica", "B", 32)
        self.set_text_color(*self.ACCENT)
        self.cell(0, 15, "MaintSignal", align="C", new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "", 12)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 8, "Maintenance Intelligence Assessment", align="C", new_x="LMARGIN", new_y="NEXT")

        # Divider
        self.ln(20)
        self.set_draw_color(*self.ACCENT)
        self.set_line_width(0.5)
        self.line(70, self.get_y(), 140, self.get_y())
        self.ln(20)

        # Client info
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*self.WHITE)
        self.cell(0, 12, self.company_name, align="C", new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "", 14)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 10, self.plant_name, align="C", new_x="LMARGIN", new_y="NEXT")

        self.ln(30)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*self.TEXT)
        self.cell(0, 8, f"Assessment Date: {self.assessment_date}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 8, f"Report Generated: {datetime.now().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")

        # Confidentiality notice
        self.ln(40)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 6, "CONFIDENTIAL - This report contains proprietary analysis of maintenance data.", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 6, "Distribution is restricted to authorized personnel only.", align="C", new_x="LMARGIN", new_y="NEXT")

    def section_header(self, title, subtitle=""):
        """Add a section header."""
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*self.ACCENT)
        self.cell(0, 6, title.upper(), new_x="LMARGIN", new_y="NEXT")

        if subtitle:
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(*self.BLACK)
            self.cell(0, 10, subtitle, new_x="LMARGIN", new_y="NEXT")

        self.ln(3)

    def metric_row(self, label, value, color=None):
        """Add a metric row with label and value."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(120, 8, label)

        self.set_font("Helvetica", "B", 11)
        if color:
            self.set_text_color(*color)
        else:
            self.set_text_color(*self.BLACK)
        self.cell(0, 8, str(value), align="R", new_x="LMARGIN", new_y="NEXT")

    def progress_bar(self, label, value, max_val=100, bar_color=None):
        """Draw a progress bar with label."""
        if bar_color is None:
            if value >= 75:
                bar_color = self.ACCENT
            elif value >= 55:
                bar_color = self.WARNING
            else:
                bar_color = self.DANGER

        # Label
        self.set_font("Helvetica", "", 9)
        self.set_text_color(80, 80, 80)
        self.cell(130, 6, label)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*bar_color)
        self.cell(0, 6, f"{value}%", align="R", new_x="LMARGIN", new_y="NEXT")

        # Bar background
        y = self.get_y()
        self.set_fill_color(230, 230, 230)
        self.rect(10, y, 190, 3, "F")

        # Bar fill
        fill_width = (value / max_val) * 190
        self.set_fill_color(*bar_color)
        self.rect(10, y, fill_width, 3, "F")

        self.ln(6)

    def insight_box(self, text, severity="info"):
        """Add a colored insight box."""
        if severity == "critical":
            border_color = self.DANGER
            icon = "!"
        elif severity == "warning":
            border_color = self.WARNING
            icon = "!"
        else:
            border_color = self.ACCENT
            icon = ">"

        y = self.get_y()
        # Left border
        self.set_draw_color(*border_color)
        self.set_line_width(0.8)
        self.line(10, y, 10, y + 12)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        self.set_x(14)
        self.multi_cell(186, 5, text)
        self.ln(3)

    def add_table(self, headers, data, col_widths=None):
        """Add a simple table."""
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)

        # Header row
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(80, 80, 80)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, border=0, fill=True,
                      align="L" if i == 0 else "R")
        self.ln()

        # Data rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        for row_idx, row in enumerate(data):
            if row_idx % 2 == 1:
                self.set_fill_color(248, 248, 248)
                fill = True
            else:
                fill = False

            for i, cell in enumerate(row):
                self.cell(col_widths[i], 7, str(cell), border=0, fill=fill,
                          align="L" if i == 0 else "R")
            self.ln()

        self.ln(3)


class ReportGenerator:
    """Generate a complete MaintSignal assessment report."""

    def __init__(self, company_name="Client Company", plant_name="Main Plant",
                 assessment_date=None):
        self.company_name = company_name
        self.plant_name = plant_name
        self.assessment_date = assessment_date or datetime.now().strftime("%B %d, %Y")
        self.pdf = None

    def generate(self, quality_results, downtime_results, failure_results,
                 financial_results, production_value_per_hour=10000):
        """Generate the complete report."""
        self.pdf = MaintSignalPDF(
            company_name=self.company_name,
            plant_name=self.plant_name,
            assessment_date=self.assessment_date
        )
        self.pdf.alias_nb_pages()

        # Cover page
        self.pdf.add_cover_page()

        # Executive Summary
        self._add_executive_summary(quality_results, downtime_results,
                                      financial_results, production_value_per_hour)

        # Data Quality Analysis
        self._add_data_quality_section(quality_results)

        # Top Problem Assets
        self._add_downtime_section(downtime_results, production_value_per_hour)

        # Failure Analysis
        self._add_failure_section(failure_results)

        # Financial Impact
        self._add_financial_section(financial_results, production_value_per_hour)

        # Recommendations
        self._add_recommendations(quality_results, downtime_results, financial_results,
                                    production_value_per_hour)

        return self.pdf

    def _add_executive_summary(self, quality, downtime, financial, prod_value):
        """Add executive summary page."""
        self.pdf.add_page()
        self.pdf.section_header("Executive Summary", "Assessment Overview")

        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.set_text_color(60, 60, 60)
        self.pdf.multi_cell(0, 6,
            f"This report presents the findings of a comprehensive maintenance data intelligence "
            f"assessment conducted for {self.company_name} ({self.plant_name}). "
            f"The analysis evaluated {downtime.get('total_breakdowns', 0) + len(downtime.get('top_assets', []))} "
            f"work order records for data quality, failure patterns, and financial impact."
        )
        self.pdf.ln(8)

        # Key metrics
        self.pdf.set_font("Helvetica", "B", 12)
        self.pdf.set_text_color(0, 0, 0)
        self.pdf.cell(0, 8, "Key Findings", new_x="LMARGIN", new_y="NEXT")
        self.pdf.ln(3)

        score = quality.get("overall_score", 0)
        score_color = (34,214,138) if score >= 75 else (240,168,48) if score >= 55 else (240,88,88)
        self.pdf.metric_row("Overall Data Quality Score", f"{score}%", score_color)
        self.pdf.metric_row("Total Breakdown Work Orders",
                            f"{downtime.get('total_breakdowns', 0):,}")
        self.pdf.metric_row("Total Unplanned Downtime",
                            f"{downtime.get('total_downtime_hours', 0):,.0f} hours",
                            (240, 88, 88))

        total_loss = financial.get("total_estimated_loss", 0)
        if total_loss >= 1000000:
            loss_str = f"${total_loss/1000000:.1f}M"
        else:
            loss_str = f"${total_loss:,.0f}"
        self.pdf.metric_row("Estimated Annual Production Loss", loss_str, (240, 88, 88))
        self.pdf.metric_row("Production Value Assumption", f"${prod_value:,.0f}/hour")

        self.pdf.ln(8)

        # Critical findings
        self.pdf.set_font("Helvetica", "B", 12)
        self.pdf.cell(0, 8, "Critical Findings", new_x="LMARGIN", new_y="NEXT")
        self.pdf.ln(3)

        if quality.get("avg_completeness", 100) < 80:
            self.pdf.insight_box(
                f"Data completeness is at {quality['avg_completeness']}%. "
                f"Critical fields like Failure Codes are missing on a significant portion of work orders, "
                f"making root cause analysis unreliable.",
                "critical"
            )

        if downtime.get("top_assets"):
            worst = downtime["top_assets"][0]
            est_cost = worst["total_downtime_hours"] * prod_value
            self.pdf.insight_box(
                f"Equipment {worst['equipment_id']} ({worst['equipment_name']}) is the worst performer "
                f"with {worst['failure_count']} breakdowns and {worst['total_downtime_hours']:.0f} hours "
                f"of downtime, representing approximately ${est_cost:,.0f} in production losses.",
                "critical"
            )

        if quality.get("consistency_issues"):
            total_issues = sum(i["count"] for i in quality["consistency_issues"])
            self.pdf.insight_box(
                f"{total_issues:,} data consistency issues detected, including duplicate records "
                f"and date inconsistencies that undermine reporting accuracy.",
                "warning"
            )

    def _add_data_quality_section(self, quality):
        """Add data quality analysis section."""
        self.pdf.add_page()
        self.pdf.section_header("Data Quality Analysis", "Field Completeness & Consistency")

        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.set_text_color(60, 60, 60)
        self.pdf.multi_cell(0, 6,
            "The data quality assessment evaluates three dimensions: completeness (are critical "
            "fields filled in?), consistency (is the data logically valid?), and usability (are "
            "the values meaningful, or just generic placeholders like 'Other'?)."
        )
        self.pdf.ln(8)

        # Score summary
        self.pdf.metric_row("Overall Quality Score",
                            f"{quality.get('overall_score', 0)}%",
                            (34,214,138) if quality.get('overall_score', 0) >= 75
                            else (240,168,48) if quality.get('overall_score', 0) >= 55
                            else (240,88,88))
        self.pdf.ln(5)

        # Completeness bars
        self.pdf.set_font("Helvetica", "B", 11)
        self.pdf.set_text_color(0, 0, 0)
        self.pdf.cell(0, 8, "Completeness by Field", new_x="LMARGIN", new_y="NEXT")
        self.pdf.ln(3)

        for field, score in sorted(quality.get("completeness", {}).items(),
                                     key=lambda x: x[1]):
            self.pdf.progress_bar(field, score)

        # Consistency issues
        if quality.get("consistency_issues"):
            self.pdf.ln(5)
            self.pdf.set_font("Helvetica", "B", 11)
            self.pdf.set_text_color(0, 0, 0)
            self.pdf.cell(0, 8, "Consistency Issues", new_x="LMARGIN", new_y="NEXT")
            self.pdf.ln(3)

            for issue in quality["consistency_issues"]:
                self.pdf.insight_box(
                    f"{issue['issue']}: {issue['count']:,} records affected",
                    issue["severity"]
                )

    def _add_downtime_section(self, downtime, prod_value):
        """Add top problem assets section."""
        self.pdf.add_page()
        self.pdf.section_header("Downtime Intelligence", "Top Problem Assets")

        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.set_text_color(60, 60, 60)
        self.pdf.multi_cell(0, 6,
            "Assets ranked by total unplanned downtime hours. Financial impact estimated "
            f"using ${prod_value:,.0f}/hour production value."
        )
        self.pdf.ln(5)

        if "top_assets" in downtime:
            headers = ["Equipment", "Name", "Failures", "Downtime (hrs)", "MTTR (hrs)", "Est. Loss"]
            col_widths = [25, 45, 22, 30, 28, 40]

            data = []
            for asset in downtime["top_assets"]:
                est_loss = asset["total_downtime_hours"] * prod_value
                if est_loss >= 1000000:
                    loss_str = f"${est_loss/1000000:.1f}M"
                else:
                    loss_str = f"${est_loss:,.0f}"

                data.append([
                    asset["equipment_id"],
                    asset["equipment_name"][:20],
                    str(asset["failure_count"]),
                    f"{asset['total_downtime_hours']:.0f}",
                    f"{asset['mttr_hours']:.1f}",
                    loss_str
                ])

            self.pdf.add_table(headers, data, col_widths)

    def _add_failure_section(self, failures):
        """Add failure pattern analysis section."""
        self.pdf.add_page()
        self.pdf.section_header("Failure Pattern Analysis", "AI-Normalized Failure Categories")

        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.set_text_color(60, 60, 60)
        self.pdf.multi_cell(0, 6,
            f"Technician free-text descriptions were analyzed and normalized into "
            f"{failures.get('total_categories', 0)} standardized failure categories. "
            f"This reveals hidden patterns that are invisible in standard SAP reports "
            f"due to inconsistent data entry."
        )
        self.pdf.ln(5)

        self.pdf.insight_box(
            f"{failures.get('total_normalized', 0):,} work order descriptions analyzed. "
            f"{failures.get('uncategorized', 0):,} could not be automatically categorized.",
            "info"
        )
        self.pdf.ln(3)

        if failures.get("categories"):
            headers = ["Failure Category", "Work Orders", "Unique Descriptions"]
            col_widths = [80, 55, 55]

            data = []
            for cat in failures["categories"]:
                data.append([
                    cat["category"],
                    str(cat["count"]),
                    str(cat.get("unique_descriptions", "N/A"))
                ])

            self.pdf.add_table(headers, data, col_widths)

    def _add_financial_section(self, financial, prod_value):
        """Add financial impact section."""
        self.pdf.add_page()
        self.pdf.section_header("Financial Impact", "Downtime Cost Estimation")

        total_loss = financial.get("total_estimated_loss", 0)
        if total_loss >= 1000000:
            loss_str = f"${total_loss/1000000:.1f}M"
        else:
            loss_str = f"${total_loss:,.0f}"

        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.set_text_color(60, 60, 60)
        self.pdf.multi_cell(0, 6,
            f"Based on an estimated production value of ${prod_value:,.0f} per hour, "
            f"unplanned downtime across the analyzed period represents approximately "
            f"{loss_str} in lost production value. This estimate is conservative and "
            f"does not include secondary costs such as scrap, rework, expedited parts, "
            f"or overtime labor."
        )
        self.pdf.ln(5)

        self.pdf.insight_box(
            f"Total Estimated Annual Production Loss: {loss_str}",
            "critical"
        )
        self.pdf.ln(3)

        if "assets" in financial:
            headers = ["Equipment", "Name", "Downtime (hrs)", "Estimated Loss", "% of Total"]
            col_widths = [25, 45, 30, 45, 45]

            data = []
            for asset in financial["assets"]:
                loss = asset["estimated_production_loss"]
                pct = (loss / total_loss * 100) if total_loss > 0 else 0
                if loss >= 1000000:
                    l_str = f"${loss/1000000:.1f}M"
                else:
                    l_str = f"${loss:,.0f}"

                data.append([
                    asset["equipment_id"],
                    asset["equipment_name"][:20],
                    f"{asset['total_downtime_hours']:.0f}",
                    l_str,
                    f"{pct:.1f}%"
                ])

            self.pdf.add_table(headers, data, col_widths)

    def _add_recommendations(self, quality, downtime, financial, prod_value):
        """Add recommendations section."""
        self.pdf.add_page()
        self.pdf.section_header("Recommendations", "Prioritized Action Items")

        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.set_text_color(60, 60, 60)
        self.pdf.multi_cell(0, 6,
            "The following recommendations are prioritized based on potential impact "
            "and implementation effort. High-priority items should be addressed within "
            "30 days for maximum ROI."
        )
        self.pdf.ln(8)

        rec_num = 1

        # Dynamic recommendations based on data
        if quality.get("avg_completeness", 100) < 80:
            worst_field = min(quality.get("completeness", {}).items(),
                            key=lambda x: x[1], default=("N/A", 0))
            self._add_recommendation(
                rec_num, "HIGH",
                f"Improve {worst_field[0]} Data Entry",
                f"Currently at {worst_field[1]}% completeness. Make this field mandatory "
                f"on work order closure in SAP. This single change dramatically improves "
                f"ability to track failures and perform accurate reliability analysis."
            )
            rec_num += 1

        if quality.get("overall_score", 100) < 70:
            self._add_recommendation(
                rec_num, "HIGH",
                "Implement Standardized Failure Taxonomy",
                "With significant portions of failure codes missing, root cause analysis "
                "is unreliable. Implement a simplified failure code taxonomy (15-20 codes "
                "maximum) and provide technicians with a laminated quick-reference card."
            )
            rec_num += 1

        if downtime.get("top_assets"):
            worst = downtime["top_assets"][0]
            est_cost = worst["total_downtime_hours"] * prod_value
            self._add_recommendation(
                rec_num, "HIGH",
                f"Root Cause Analysis on {worst['equipment_id']}",
                f"This asset has {worst['failure_count']} breakdowns totaling "
                f"{worst['total_downtime_hours']:.0f} hours of downtime "
                f"(~${est_cost:,.0f} production loss). The failure pattern suggests "
                f"a systemic issue that reactive maintenance cannot solve. "
                f"Conduct a formal RCA and evaluate PM strategy changes."
            )
            rec_num += 1

        self._add_recommendation(
            rec_num, "MEDIUM",
            "Standardize Work Order Descriptions",
            "Technician free-text descriptions are highly inconsistent. The same failure "
            "mode is described dozens of different ways, making trend analysis impossible "
            "without AI normalization. Provide structured dropdown entry options alongside "
            "free text to improve future data quality."
        )
        rec_num += 1

        self._add_recommendation(
            rec_num, "MEDIUM",
            "Implement Recurring Data Assessments",
            "Schedule monthly data quality assessments to track improvement trends and "
            "identify emerging failure patterns early. This creates a continuous improvement "
            "loop for maintenance operations and data quality."
        )
        rec_num += 1

        self._add_recommendation(
            rec_num, "LOW",
            "Review PM Task List Effectiveness",
            "Cross-reference preventive maintenance task lists against actual breakdown "
            "patterns. If the same assets receiving regular PM are still experiencing "
            "frequent breakdowns, the PM tasks may not be addressing the right failure modes."
        )

    def _add_recommendation(self, number, priority, title, detail):
        """Add a single recommendation."""
        if priority == "HIGH":
            color = (240, 88, 88)
        elif priority == "MEDIUM":
            color = (240, 168, 48)
        else:
            color = (34, 214, 138)

        self.pdf.set_font("Helvetica", "B", 7)
        self.pdf.set_text_color(*color)
        self.pdf.cell(20, 6, f"[{priority}]")

        self.pdf.set_font("Helvetica", "B", 11)
        self.pdf.set_text_color(0, 0, 0)
        self.pdf.cell(0, 6, f"{number}. {title}", new_x="LMARGIN", new_y="NEXT")

        self.pdf.set_font("Helvetica", "", 9)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.multi_cell(0, 5, detail)
        self.pdf.ln(5)

    def add_compliance_section(self, compliance_results):
        """Add compliance gap analysis section to the report."""
        if not compliance_results or "frameworks_checked" not in compliance_results:
            return

        self.add_page()
        self.section_title("COMPLIANCE GAP ANALYSIS")
        self.ln(3)

        # Overall score
        score = compliance_results.get("overall_compliance_score", 0)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.WHITE)
        self.cell(0, 8, f"Overall Compliance Score: {score}%", new_x="LMARGIN", new_y="NEXT")

        # Framework results
        for fw in compliance_results.get("frameworks_checked", []):
            self.ln(4)
            self.set_font("Helvetica", "B", 10)
            color = self.ACCENT if fw["score"] >= 85 else self.WARNING if fw["score"] >= 65 else self.DANGER
            self.set_text_color(*color)
            self.cell(0, 7, f"{fw['name']}: {fw['score']}% ({fw['risk_level']} risk)", new_x="LMARGIN", new_y="NEXT")

            # Field scores table
            headers = ["Field", "Completeness", "Status"]
            data = []
            for field, score_data in fw.get("field_scores", {}).items():
                data.append([score_data["label"], f"{score_data['completeness']}%", score_data["status"].upper()])

            if data:
                self.add_table(headers, data, col_widths=[80, 40, 30])

        # Remediation actions
        actions = compliance_results.get("remediation_actions", [])
        if actions:
            self.ln(5)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*self.WHITE)
            self.cell(0, 7, "Priority Remediation Actions:", new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

            for i, action in enumerate(actions[:8], 1):
                self.set_font("Helvetica", "B", 9)
                color = self.DANGER if action["priority"] == "HIGH" else self.WARNING
                self.set_text_color(*color)
                self.cell(0, 6, f"  {i}. [{action['priority']}] {action['action']}", new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "", 8)
                self.set_text_color(*self.TEXT_MUTED)
                self.cell(0, 5, f"     {action['reason']}", new_x="LMARGIN", new_y="NEXT")

    def add_benchmarking_section(self, benchmark_results):
        """Add industry benchmarking section to the report."""
        if not benchmark_results or "comparisons" not in benchmark_results:
            return

        self.add_page()
        self.section_title("INDUSTRY BENCHMARKING")
        self.ln(3)

        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.WHITE)
        self.cell(0, 8, f"Industry Position: {benchmark_results.get('overall_rating', 'N/A')} ({benchmark_results.get('summary_score', 0)}%)", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 6, f"Compared against: {benchmark_results.get('industry', 'General Manufacturing')} peers", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

        headers = ["Metric", "Your Value", "Industry Avg", "World Class", "Rating"]
        data = []
        for comp in benchmark_results.get("comparisons", []):
            data.append([
                comp["metric"],
                f"{comp['client_value']}{comp['unit']}",
                f"{comp['industry_average']}{comp['unit']}",
                f"{comp['world_class']}{comp['unit']}",
                comp["rating_label"],
            ])

        if data:
            self.add_table(headers, data, col_widths=[55, 30, 30, 30, 35])

        # Strengths
        if benchmark_results.get("strengths"):
            self.ln(4)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*self.ACCENT)
            self.cell(0, 6, "Strengths:", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 8)
            for s in benchmark_results["strengths"]:
                self.cell(0, 5, f"  + {s}", new_x="LMARGIN", new_y="NEXT")

        # Weaknesses
        if benchmark_results.get("weaknesses"):
            self.ln(2)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*self.DANGER)
            self.cell(0, 6, "Gaps:", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*self.TEXT_MUTED)
            for w in benchmark_results["weaknesses"]:
                self.cell(0, 5, f"  - {w}", new_x="LMARGIN", new_y="NEXT")

    def add_cost_section(self, cost_results):
        """Add cost analysis section to the report."""
        if not cost_results or "error" in cost_results:
            return

        self.add_page()
        self.section_title("MAINTENANCE COST ANALYSIS")
        self.ln(3)

        stats = cost_results.get("stats", {})
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.WARNING)
        self.cell(0, 8, f"Total Maintenance Spend: ${stats.get('total_cost', 0):,.0f}", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 6, f"Average per work order: ${stats.get('avg_cost_per_wo', 0):,.0f} | Cost data coverage: {stats.get('cost_coverage', 0)}%", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

        # Emergency vs Planned
        evp = cost_results.get("emergency_vs_planned", {})
        if evp:
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*self.WHITE)
            self.cell(0, 7, "Emergency vs Planned Spend:", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*self.DANGER)
            self.cell(0, 6, f"  Emergency: ${evp.get('emergency_cost', 0):,.0f} ({evp.get('emergency_pct', 0)}%)", new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(*self.ACCENT)
            self.cell(0, 6, f"  Planned: ${evp.get('planned_cost', 0):,.0f} ({evp.get('planned_pct', 0)}%)", new_x="LMARGIN", new_y="NEXT")
            self.ln(3)

        # Top cost assets
        if cost_results.get("cost_by_asset"):
            headers = ["Asset", "Total Cost", "Work Orders", "Avg Cost", "% of Total"]
            data = []
            for a in cost_results["cost_by_asset"][:10]:
                data.append([a["asset_id"], f"${a['total_cost']:,.0f}", str(a["wo_count"]), f"${a['avg_cost']:,.0f}", f"{a['pct_of_total']}%"])
            self.add_table(headers, data, col_widths=[30, 40, 30, 35, 25])

        # Optimization opportunities
        opps = cost_results.get("optimization_opportunities", [])
        if opps:
            self.ln(4)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*self.WHITE)
            self.cell(0, 7, "Cost Optimization Opportunities:", new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
            for opp in opps:
                self.set_font("Helvetica", "B", 9)
                color = self.DANGER if opp["priority"] == "HIGH" else self.WARNING
                self.set_text_color(*color)
                self.cell(0, 6, f"  [{opp['priority']}] {opp['title']}", new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "", 8)
                self.set_text_color(*self.TEXT_MUTED)
                self.cell(0, 5, f"     Potential savings: ${opp['potential_savings']:,.0f}", new_x="LMARGIN", new_y="NEXT")
                self.cell(0, 5, f"     {opp['action'][:100]}", new_x="LMARGIN", new_y="NEXT")

    def save(self, filename):
        """Save the PDF to file."""
        self.pdf.output(filename)
        print(f"Report saved to {filename}")
        return filename


# ============================================================
# STANDALONE USAGE
# ============================================================

if __name__ == "__main__":
    """Generate a sample report using synthetic data."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))

    from generate_data import generate_data

    # Import analysis functions from main app
    # For standalone use, we include simplified versions here
    import pandas as pd
    import numpy as np

    print("Generating synthetic data...")
    df = generate_data(2000)

    print("Running analysis...")

    # Quick analysis (simplified versions of the main app functions)
    total = len(df)
    fields = {
        "Equipment_ID": "Equipment ID", "Functional_Location": "Functional Location",
        "Damage_Code": "Damage Code", "Cause_Code": "Cause Code",
        "Notification": "Notification Number",
        "Malfunction_Start": "Malfunction Start", "Malfunction_End": "Malfunction End"
    }
    completeness = {}
    for col, label in fields.items():
        filled = df[col].astype(str).str.strip().replace("", np.nan).notna().sum()
        completeness[label] = round((filled / total) * 100, 1)

    quality = {
        "completeness": completeness,
        "avg_completeness": round(np.mean(list(completeness.values())), 1),
        "consistency_score": 85.0,
        "usability_score": 62.0,
        "overall_score": 65.0,
        "consistency_issues": [
            {"issue": "Completion date before creation date", "count": 160, "severity": "critical"},
            {"issue": "Duplicate work orders", "count": 120, "severity": "warning"},
        ]
    }

    # Downtime
    breakdowns = df[df["Order_Type"] == "PM01"]
    breakdowns = breakdowns[breakdowns["Equipment_ID"].astype(str).str.strip() != ""]
    asset_list = []
    for eid in breakdowns["Equipment_ID"].unique():
        edata = breakdowns[breakdowns["Equipment_ID"] == eid]
        fc = len(edata)
        dt = edata["Actual_Hours"].sum()
        names = edata["Equipment_Name"].dropna().unique()
        name = names[0] if len(names) > 0 else eid
        asset_list.append({
            "equipment_id": eid, "equipment_name": name,
            "failure_count": fc, "total_downtime_hours": round(dt, 1),
            "mttr_hours": round(dt/fc, 1), "actual_cost": round(edata["Actual_Cost"].sum(), 2)
        })
    asset_list.sort(key=lambda x: x["total_downtime_hours"], reverse=True)

    downtime = {
        "top_assets": asset_list[:10],
        "total_breakdowns": len(breakdowns),
        "total_downtime_hours": sum(a["total_downtime_hours"] for a in asset_list)
    }

    # Failures
    failures = {
        "categories": [
            {"category": "Seal Failure", "count": 380, "unique_descriptions": 18},
            {"category": "Bearing Failure", "count": 290, "unique_descriptions": 15},
            {"category": "Motor Failure", "count": 250, "unique_descriptions": 15},
            {"category": "Preventive Maintenance", "count": 800, "unique_descriptions": 17},
            {"category": "Valve Failure", "count": 120, "unique_descriptions": 12},
            {"category": "Uncategorized", "count": 160, "unique_descriptions": 45},
        ],
        "total_normalized": 2000,
        "total_categories": 6,
        "uncategorized": 160
    }

    # Financial
    prod_value = 10000
    financial_assets = []
    for a in asset_list[:10]:
        financial_assets.append({
            **a,
            "estimated_production_loss": round(a["total_downtime_hours"] * prod_value, 2)
        })
    financial = {
        "assets": financial_assets,
        "total_estimated_loss": sum(a["estimated_production_loss"] for a in financial_assets)
    }

    print("Generating PDF report...")
    generator = ReportGenerator(
        company_name="Acme Manufacturing Corp",
        plant_name="Houston Production Facility",
        assessment_date="June 15, 2025"
    )
    generator.generate(quality, downtime, failures, financial, prod_value)
    generator.save("sample_assessment_report.pdf")
    print("Done! Open sample_assessment_report.pdf to view the report.")
