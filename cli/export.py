import csv
import json
from pathlib import Path
from typing import List, Any
from core.models import PatentRecord
import fpdf

def _export_csv(records: List[PatentRecord], output_path: str):
    if not records:
        Path(output_path).touch()
        return
        
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Title", "Assignee", "Filed Date", "Status"])
        for record in records:
            writer.writerow([
                record.id,
                record.title,
                record.assignee,
                record.dates.get("filed", ""),
                record.status
            ])

def _export_json(records: List[PatentRecord], output_path: str):
    import dataclasses
    def _default(o: Any):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return str(o)
        
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([_default(r) for r in records], f, indent=2)

def _export_bibtex(records: List[PatentRecord], output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(f"@misc{{{record.id},\n")
            f.write(f"  title = {{{record.title}}},\n")
            f.write(f"  author = {{{record.assignee}}},\n")
            f.write(f"  year = {{{record.dates.get('filed', '')[:4] if record.dates.get('filed') else ''}}},\n")
            f.write(f"  note = {{Status: {record.status}}}\n")
            f.write("}\n\n")

def _export_markdown(records: List[PatentRecord], output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(f"# {record.title}\n\n")
            f.write(f"**ID**: {record.id} | **Assignee**: {record.assignee} | **Filed**: {record.dates.get('filed', '[?]')}\n\n")
            f.write(f"## Abstract\n{record.abstract}\n\n")
            f.write("---\n\n")

def _export_pdf(records: List[PatentRecord], output_path: str):
    """Generate PDF export with title page and individual patent pages."""
    pdf = fpdf.FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title page
    pdf.add_page()
    pdf.set_font("helvetica", style="B", size=24)
    pdf.ln(80)
    pdf.cell(0, 20, "RECON Export", align="C")
    pdf.ln(15)
    pdf.set_font("helvetica", size=18)
    pdf.cell(0, 20, f"{len(records)} Patents", align="C")
    pdf.set_font("helvetica", size=12)
    pdf.ln(50)
    pdf.cell(0, 10, f"Generated: {Path(output_path).stem}", align="C")
    
    # Patent pages
    for record in records:
        pdf.add_page()
        pdf.set_font("helvetica", style="B", size=14)
        safe_title = record.title.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(w=180, h=8, text=safe_title, align="L")
        pdf.ln(3)
        
        # ID, Assignee, Dates row
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(w=180, h=6, text=f"ID: {record.id}", align="L")
        safe_assignee = record.assignee.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(w=180, h=6, text=f"Assignee: {safe_assignee}", align="L")
        
        # Dates
        dates_str = " | ".join([f"{k}: {v}" for k, v in record.dates.items()])
        safe_dates = dates_str.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(w=180, h=6, text=safe_dates, align="L")
        pdf.multi_cell(w=180, h=6, text=f"Status: {record.status}", align="L")
        pdf.ln(5)
        
        # Abstract
        pdf.set_font("helvetica", style="B", size=11)
        pdf.cell(0, 8, "Abstract", align="L")
        pdf.ln(8)
        pdf.set_font("helvetica", size=10)
        safe_abstract = record.abstract.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(w=180, h=6, text=safe_abstract, align="L")
        pdf.ln(5)
        
        # Claims
        if record.claims:
            pdf.set_font("helvetica", style="B", size=11)
            pdf.cell(0, 8, "Claims", align="L")
            pdf.ln(8)
            pdf.set_font("helvetica", size=10)
            for i, claim in enumerate(record.claims, 1):
                safe_claim = claim.encode('latin-1', 'replace').decode('latin-1')
                claim_text = f"{i}. {safe_claim}"
                pdf.multi_cell(w=180, h=6, text=claim_text, align="L")
        
    pdf.output(output_path)

def export_records(records: List[PatentRecord], format: str, output_path: str):
    format = format.lower()
    try:
        if format == "csv":
            _export_csv(records, output_path)
        elif format == "json":
            _export_json(records, output_path)
        elif format == "bibtex":
            _export_bibtex(records, output_path)
        elif format == "markdown":
            _export_markdown(records, output_path)
        elif format == "pdf":
            _export_pdf(records, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    except Exception as e:
        print(f"ERR: Export to {format} failed. Reason: {e}")
        raise

def export_pdf(collection: List[PatentRecord], path: str) -> None:
    """
    Export patent collection to PDF file.
    Generates a title page followed by one page per patent.
    
    Args:
        collection: List of PatentRecord objects to export
        path: Output file path (e.g., '/path/to/export.pdf')
    
    Raises:
        ValueError: If collection is empty
        IOError: If file cannot be written
    """
    if not collection:
        raise ValueError("Cannot export empty collection.")
    try:
        _export_pdf(collection, path)
    except Exception as e:
        print(f"ERR: PDF export failed. Reason: {e}")
        raise
