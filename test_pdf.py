import fpdf
pdf = fpdf.FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=12)
pdf.multi_cell(0, 10, text="ID: US1 | Assignee: Acme Corp", align="L")
pdf.output("out.pdf")
