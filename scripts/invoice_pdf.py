import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class RagworthInvoiceGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_pdf(self, invoice_id, date_str, client_name, client_address, service_desc, amount):
        filename = f"{invoice_id}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Setup document: letter size, 0.75-inch (54 points) margins
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )
        
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Color palette definition (Old Money / Quiet Luxury)
        PRIMARY_COLOR = colors.HexColor("#0B0B0D")  # Deep Obsidian
        ACCENT_COLOR = colors.HexColor("#8D7859")   # Warm Bronze/Stone
        TEXT_MUTED = colors.HexColor("#6F6961")     # Soft Graphite
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=24,
            leading=28,
            textColor=PRIMARY_COLOR,
            spaceAfter=4
        )
        
        subtitle_style = ParagraphStyle(
            'InvoiceSubtitle',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=8,
            leading=10,
            textColor=TEXT_MUTED,
            spaceAfter=20,
            textTransform='uppercase'
        )
        
        meta_label_style = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=ACCENT_COLOR
        )
        
        meta_value_style = ParagraphStyle(
            'MetaValue',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=PRIMARY_COLOR
        )
        
        section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=10,
            leading=12,
            textColor=PRIMARY_COLOR,
            spaceAfter=6
        )
        
        body_style = ParagraphStyle(
            'InvoiceBody',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=9,
            leading=12,
            textColor=PRIMARY_COLOR
        )
        
        muted_body_style = ParagraphStyle(
            'InvoiceBodyMuted',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=8,
            leading=11,
            textColor=TEXT_MUTED
        )
        
        th_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white
        )
        
        # --- 1. Header Section ---
        header_data = [
            [
                Paragraph("RAGWORTH", title_style),
                Paragraph("<b>INVOICE</b>", ParagraphStyle('InvText', parent=styles['Normal'], fontName='Times-Bold', fontSize=20, textColor=PRIMARY_COLOR, alignment=2))
            ],
            [
                Paragraph("RAGON CO TECH CONGLOMERATE", subtitle_style),
                Spacer(1, 1)
            ]
        ]
        header_table = Table(header_data, colWidths=[250, 250])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))
        
        # --- 2. Meta Details (Invoice ID, Date, Status) ---
        meta_data = [
            [
                Paragraph("<b>INVOICE ID:</b>", meta_label_style),
                Paragraph(invoice_id, meta_value_style),
                Paragraph("<b>DATE:</b>", meta_label_style),
                Paragraph(date_str, meta_value_style),
                Paragraph("<b>STATUS:</b>", meta_label_style),
                Paragraph("<b>DUE UPON RECEIPT</b>", ParagraphStyle('DueText', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=ACCENT_COLOR))
            ]
        ]
        meta_table = Table(meta_data, colWidths=[80, 100, 50, 100, 60, 110])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINEBELOW', (0,0), (-1,-1), 1, ACCENT_COLOR),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))
        
        # --- 3. Billed To / Remit To ---
        billed_text = f"<b>{client_name}</b><br/>{client_address}"
        remit_text = "<b>Ragon Co. Limited</b><br/>HSBC Private Banking, London Branch<br/>SWIFT/IBAN: INVOICING SECURE NODE"
        
        address_data = [
            [Paragraph("BILLED TO:", section_heading_style), Paragraph("REMIT PAYMENT TO:", section_heading_style)],
            [Paragraph(billed_text, body_style), Paragraph(remit_text, body_style)]
        ]
        address_table = Table(address_data, colWidths=[250, 250])
        address_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(address_table)
        story.append(Spacer(1, 30))
        
        # --- 4. Line Items Table ---
        table_headers = [
            Paragraph("DESCRIPTION OF INFRASTRUCTURE DELIVERABLE", th_style),
            Paragraph("QTY", th_style),
            Paragraph("RATE (USD)", th_style),
            Paragraph("TOTAL (USD)", th_style)
        ]
        
        item_row = [
            Paragraph(service_desc, body_style),
            Paragraph("1", body_style),
            Paragraph(f"${amount:,.2f}", body_style),
            Paragraph(f"${amount:,.2f}", ParagraphStyle('TotalText', parent=body_style, fontName='Times-Bold'))
        ]
        
        items_data = [table_headers, item_row]
        
        items_table = Table(items_data, colWidths=[310, 40, 75, 75])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1CFC9")),
            ('LINEBELOW', (0,0), (-1,0), 1.5, PRIMARY_COLOR),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 15))
        
        # --- 5. Summary Totals Section ---
        totals_data = [
            [Paragraph("Subtotal:", body_style), Paragraph(f"${amount:,.2f}", body_style)],
            [Paragraph("VAT / Service Taxes (0%):", body_style), Paragraph("$0.00", body_style)],
            [Paragraph("<b>Grand Total (USD):</b>", ParagraphStyle('GTotal', parent=styles['Normal'], fontName='Times-Bold', fontSize=10)), Paragraph(f"<b>${amount:,.2f}</b>", ParagraphStyle('GTotalVal', parent=styles['Normal'], fontName='Times-Bold', fontSize=10))]
        ]
        
        totals_table = Table(totals_data, colWidths=[380, 120])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('LINEABOVE', (0,2), (1,2), 1, PRIMARY_COLOR),
            ('LINEBELOW', (0,2), (1,2), 2.5, PRIMARY_COLOR), # Double accounting lines
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 40))
        
        # --- 6. Terms of Business ---
        terms_text = (
            "<b>Terms of Business:</b><br/>"
            "Standard payment terms are net-30 upon receipt of invoice. All architecture, CRM pipelines, "
            "and software implementations remain the secure structural property of Ragon Co. until full cash "
            "remittance is verified. Standard SLA and NDA protocols apply."
        )
        terms_paragraph = Paragraph(terms_text, muted_body_style)
        
        terms_table = Table([[terms_paragraph]], colWidths=[500])
        terms_table.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 0.5, ACCENT_COLOR),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(terms_table)
        
        # Draw document
        doc.build(story)
        print(f"[✔] ReportLab generated pristine invoice: {filepath}")
        return filepath
