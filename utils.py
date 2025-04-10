import os
from pathlib import Path
import pdfkit

def converter_html_para_pdf(html_path, pdf_path):
    try:
        Path(os.path.dirname(pdf_path)).mkdir(parents=True, exist_ok=True)
        pdfkit.from_file(html_path, pdf_path)
        print(f"[PDF] PDF gerado com sucesso: {pdf_path}")
    except Exception as e:
        print(f"[ERRO] Falha ao converter HTML para PDF: {e}")
