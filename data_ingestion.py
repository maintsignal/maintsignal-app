"""
MaintSignal — Smart Data Ingestion Module
Handles CSV, Excel, and PDF files. Auto-detects columns and maps them
to the universal data model using keyword matching + LLM fallback.

Usage:
    from data_ingestion import DataIngestor
    
    ingestor = DataIngestor()
    result = ingestor.load_file("client_data.xlsx")
    # result.df = normalized DataFrame
    # result.mapping = column mapping used
    # result.warnings = any issues found during ingestion
"""

import pandas as pd
import numpy as np
import os
import re
import json
from datetime import datetime
from knowledge_base import COLUMN_ALIASES, guess_column_mapping


class IngestionResult:
    """Container for ingestion results."""
    def __init__(self):
        self.df = None                  # The normalized DataFrame
        self.raw_df = None              # Original data before normalization
        self.mapping = {}               # Column mapping used
        self.unmapped_columns = []      # Columns that couldn't be mapped
        self.file_type = ""             # csv, xlsx, pdf
        self.sheet_name = None          # For Excel files
        self.record_count = 0
        self.column_count = 0
        self.warnings = []              # Issues found during ingestion
        self.auto_detected = True       # Whether mapping was automatic


class DataIngestor:
    """Smart data ingestion that handles multiple file formats."""

    STANDARD_COLUMNS = [
        "order_id", "asset_id", "asset_name", "order_type", "priority",
        "created_date", "completed_date", "downtime_start", "downtime_end",
        "description", "failure_code", "cause_code", "labor_hours",
        "cost", "status", "location"
    ]

    def load_file(self, filepath, sheet_name=None, custom_mapping=None):
        """
        Load a maintenance data file and normalize it.
        
        Args:
            filepath: Path to CSV, Excel, or PDF file
            sheet_name: For Excel files, which sheet to read
            custom_mapping: Override auto-detection with manual mapping
            
        Returns:
            IngestionResult object
        """
        result = IngestionResult()
        ext = os.path.splitext(filepath)[1].lower()

        # Step 1: Read the raw file
        if ext == ".csv":
            result.raw_df = self._read_csv(filepath, result)
            result.file_type = "csv"
        elif ext in [".xlsx", ".xls", ".xlsm"]:
            result.raw_df = self._read_excel(filepath, sheet_name, result)
            result.file_type = "xlsx"
            result.sheet_name = sheet_name
        elif ext == ".pdf":
            result.raw_df = self._read_pdf(filepath, result)
            result.file_type = "pdf"
        else:
            result.warnings.append(f"Unsupported file type: {ext}")
            return result

        if result.raw_df is None or result.raw_df.empty:
            result.warnings.append("No data found in file")
            return result

        result.record_count = len(result.raw_df)
        result.column_count = len(result.raw_df.columns)

        # Step 2: Map columns to standard schema
        if custom_mapping:
            result.mapping = custom_mapping
            result.auto_detected = False
        else:
            result.mapping = self._auto_map_columns(result.raw_df.columns.tolist())

        # Track unmapped columns
        mapped_originals = set(result.mapping.keys())
        result.unmapped_columns = [
            c for c in result.raw_df.columns if c not in mapped_originals
        ]

        if result.unmapped_columns:
            result.warnings.append(
                f"{len(result.unmapped_columns)} columns could not be auto-mapped: "
                f"{', '.join(result.unmapped_columns[:5])}"
                f"{'...' if len(result.unmapped_columns) > 5 else ''}"
            )

        # Step 3: Normalize into standard DataFrame
        result.df = self._normalize(result.raw_df, result.mapping)

        # Step 4: Run basic validation
        self._validate(result)

        return result

    def _read_csv(self, filepath, result):
        """Read CSV with auto-detection of delimiter and encoding."""
        # Try common encodings
        for encoding in ["utf-8", "latin1", "iso-8859-1", "cp1252"]:
            try:
                # Detect delimiter
                with open(filepath, "r", encoding=encoding) as f:
                    sample = f.read(5000)

                # Count potential delimiters
                delimiters = {",": 0, ";": 0, "\t": 0, "|": 0}
                for d in delimiters:
                    delimiters[d] = sample.count(d)

                delimiter = max(delimiters, key=delimiters.get)

                df = pd.read_csv(
                    filepath,
                    delimiter=delimiter,
                    encoding=encoding,
                    low_memory=False,
                    on_bad_lines="skip"
                )

                # Clean column names
                df.columns = [str(c).strip() for c in df.columns]

                if len(df.columns) > 1:  # Valid parse
                    return df

            except Exception:
                continue

        result.warnings.append("Could not parse CSV file with any standard encoding")
        return None

    def _read_excel(self, filepath, sheet_name, result):
        """Read Excel file with sheet detection."""
        try:
            xls = pd.ExcelFile(filepath)
            available_sheets = xls.sheet_names

            if not available_sheets:
                result.warnings.append("Excel file has no sheets")
                return None

            # Pick the right sheet
            if sheet_name and sheet_name in available_sheets:
                target_sheet = sheet_name
            elif len(available_sheets) == 1:
                target_sheet = available_sheets[0]
            else:
                # Try to find the most likely data sheet
                target_sheet = self._guess_best_sheet(xls, available_sheets)
                result.warnings.append(
                    f"Multiple sheets found: {available_sheets}. "
                    f"Auto-selected: '{target_sheet}'"
                )

            df = pd.read_excel(filepath, sheet_name=target_sheet)
            df.columns = [str(c).strip() for c in df.columns]
            return df

        except Exception as e:
            result.warnings.append(f"Error reading Excel file: {str(e)}")
            return None

    def _guess_best_sheet(self, xls, sheets):
        """Guess which Excel sheet contains the main data."""
        best_sheet = sheets[0]
        best_rows = 0

        maintenance_keywords = [
            "work order", "wo", "maintenance", "data", "export",
            "orders", "notifications", "equipment", "main"
        ]

        for sheet in sheets:
            # Check if sheet name contains maintenance keywords
            sheet_lower = sheet.lower()
            for kw in maintenance_keywords:
                if kw in sheet_lower:
                    return sheet

            # Otherwise pick the sheet with most rows
            try:
                df = pd.read_excel(xls, sheet_name=sheet, nrows=5)
                rows = len(df)
                if rows > best_rows:
                    best_rows = rows
                    best_sheet = sheet
            except Exception:
                continue

        return best_sheet

    def _read_pdf(self, filepath, result):
        """
        Extract tabular data from PDF.
        Requires: pip install tabula-py (which needs Java)
        Fallback: pip install pdfplumber
        """
        # Try pdfplumber first (pure Python, no Java needed)
        try:
            import pdfplumber

            all_rows = []
            headers = None

            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if not table:
                            continue
                        if headers is None and table[0]:
                            headers = [str(h).strip() if h else f"Column_{i}"
                                      for i, h in enumerate(table[0])]
                            data_rows = table[1:]
                        else:
                            data_rows = table
                        all_rows.extend(data_rows)

            if headers and all_rows:
                df = pd.DataFrame(all_rows, columns=headers)
                df = df.dropna(how="all")  # Remove completely empty rows
                return df
            else:
                result.warnings.append("No tables found in PDF. Try CSV or Excel format instead.")
                return None

        except ImportError:
            result.warnings.append(
                "PDF reading requires pdfplumber: pip install pdfplumber"
            )
            return None

        except Exception as e:
            result.warnings.append(f"Error reading PDF: {str(e)}")
            return None

    def _auto_map_columns(self, columns):
        """Auto-detect column mapping using the knowledge base."""
        raw_mapping = guess_column_mapping(columns)

        # Convert to simple {original: standard} format
        mapping = {}
        used_standards = set()

        # Sort by confidence (highest first) to avoid conflicts
        sorted_items = sorted(
            raw_mapping.items(),
            key=lambda x: x[1]["confidence"],
            reverse=True
        )

        for original, match in sorted_items:
            standard = match["maps_to"]
            if standard not in used_standards:
                mapping[original] = standard
                used_standards.add(standard)

        return mapping

    def _normalize(self, raw_df, mapping):
        """Create a normalized DataFrame using the column mapping."""
        normalized = pd.DataFrame()

        # Map each standard column
        reverse_map = {v: k for k, v in mapping.items()}

        for std_col in self.STANDARD_COLUMNS:
            if std_col in reverse_map:
                original_col = reverse_map[std_col]
                if original_col in raw_df.columns:
                    normalized[std_col] = raw_df[original_col].copy()
                else:
                    normalized[std_col] = ""
            else:
                normalized[std_col] = ""

        # Convert dates
        for date_col in ["created_date", "completed_date", "downtime_start", "downtime_end"]:
            if date_col in normalized.columns:
                normalized[date_col] = pd.to_datetime(
                    normalized[date_col], errors="coerce"
                )

        # Convert numerics
        for num_col in ["labor_hours", "cost"]:
            if num_col in normalized.columns:
                normalized[num_col] = pd.to_numeric(
                    normalized[num_col].astype(str).str.replace(",", "").str.replace("$", ""),
                    errors="coerce"
                )

        # Clean strings
        for str_col in ["description", "asset_id", "asset_name", "failure_code",
                        "cause_code", "order_type", "priority", "status"]:
            if str_col in normalized.columns:
                normalized[str_col] = (
                    normalized[str_col]
                    .astype(str)
                    .str.strip()
                    .replace({"nan": "", "None": "", "NaN": ""})
                )

        return normalized

    def _validate(self, result):
        """Run basic validation checks on the normalized data."""
        df = result.df
        if df is None or df.empty:
            return

        # Check for required columns with data
        required = ["order_id", "description"]
        for col in required:
            non_empty = df[col].astype(str).str.strip().replace("", np.nan).notna().sum()
            if non_empty == 0:
                result.warnings.append(
                    f"Critical: No data found for '{col}'. "
                    f"Check column mapping."
                )

        # Check date consistency
        if "created_date" in df.columns and "completed_date" in df.columns:
            valid_dates = df.dropna(subset=["created_date", "completed_date"])
            backwards = valid_dates[valid_dates["completed_date"] < valid_dates["created_date"]]
            if len(backwards) > 0:
                result.warnings.append(
                    f"Found {len(backwards)} records where completion date "
                    f"is before creation date"
                )

        # Check for minimum useful data
        if result.record_count < 50:
            result.warnings.append(
                f"Only {result.record_count} records found. "
                f"Recommend at least 6-12 months of data (500+ records) for meaningful analysis."
            )

        # Estimate data quality
        total_cells = result.record_count * len(self.STANDARD_COLUMNS)
        filled_cells = sum(
            df[col].astype(str).str.strip().replace("", np.nan).notna().sum()
            for col in df.columns
        )
        fill_rate = (filled_cells / total_cells * 100) if total_cells > 0 else 0
        result.warnings.append(f"Overall data fill rate: {fill_rate:.1f}%")

    def get_mapping_summary(self, result):
        """Get a human-readable summary of the column mapping."""
        lines = []
        lines.append(f"File: {result.file_type.upper()} | {result.record_count:,} records | {result.column_count} columns")
        lines.append("")
        lines.append("Column Mapping:")

        for original, standard in sorted(result.mapping.items()):
            lines.append(f"  {original:30s} → {standard}")

        if result.unmapped_columns:
            lines.append("")
            lines.append("Unmapped Columns (preserved as-is):")
            for col in result.unmapped_columns:
                lines.append(f"  {col}")

        if result.warnings:
            lines.append("")
            lines.append("Warnings:")
            for w in result.warnings:
                lines.append(f"  ⚠ {w}")

        return "\n".join(lines)


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    """Test the ingestion module with a sample file."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python data_ingestion.py <filepath>")
        print("Supported: .csv, .xlsx, .xls, .pdf")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"Loading: {filepath}")

    ingestor = DataIngestor()
    result = ingestor.load_file(filepath)

    print(ingestor.get_mapping_summary(result))

    if result.df is not None:
        print(f"\nNormalized data preview:")
        print(result.df.head(10).to_string())
