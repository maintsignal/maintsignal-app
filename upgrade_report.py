"""
Upgrade report_generator.py to include new analysis modules.
Adds: Compliance, Benchmarking, Cost Analysis sections to PDF.
Run: python3 upgrade_report.py
"""

with open("report_generator.py", "r") as f:
    content = f.read()

# Find the save method and add new sections before it
old_save = '''    def save(self, filename):'''

new_sections = '''    def add_compliance_section(self, compliance_results):
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

    def save(self, filename):'''

if "add_compliance_section" not in content:
    content = content.replace(old_save, new_sections)
    with open("report_generator.py", "w") as f:
        f.write(content)
    print("[OK] Added compliance, benchmarking, and cost sections to PDF generator")
else:
    print("[SKIP] Sections already present")

# Verify
import py_compile
try:
    py_compile.compile("report_generator.py", doraise=True)
    print("[OK] No syntax errors")
except py_compile.PyCompileError as e:
    print(f"[ERROR] {e}")

print("\n✅ PDF Report Generator upgraded with 3 new sections!")
