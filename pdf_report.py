"""
PDF Report Generation
Creates professional PDF reports from analysis results
"""

from typing import Dict
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from app_config import get_config
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()


def generate_pdf_report(analysis_result: Dict, output_path: str) -> str:
    """
    Generate PDF report from analysis results
    
    Args:
        analysis_result: Analysis result dictionary
        output_path: Path to save PDF file
        
    Returns:
        Path to generated PDF file
    """
    try:
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        story.append(Paragraph("Security Audit Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata
        metadata_data = [
            ['Contract Name:', analysis_result.get('contract_name', 'Unknown')],
            ['Analysis Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Risk Score:', f"{analysis_result.get('risk_score', 0)}/100"],
            ['Overall Severity:', analysis_result.get('severity', 'UNKNOWN')],
            ['Vulnerabilities Found:', str(len(analysis_result.get('vulnerabilities', [])))],
            ['Lines of Code:', str(analysis_result.get('lines_of_code', 0))],
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        story.append(Paragraph("Executive Summary", heading_style))
        summary_text = f"""
        This security audit analyzed the smart contract <b>{analysis_result.get('contract_name', 'Unknown')}</b> 
        and identified <b>{len(analysis_result.get('vulnerabilities', []))}</b> potential vulnerabilities.
        The overall risk score is <b>{analysis_result.get('risk_score', 0)}/100</b>, 
        with a severity rating of <b>{analysis_result.get('severity', 'UNKNOWN')}</b>.
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Vulnerabilities
        vulnerabilities = analysis_result.get('vulnerabilities', [])
        if vulnerabilities:
            story.append(Paragraph("Vulnerabilities", heading_style))
            
            # Group by severity
            severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
            grouped = {}
            for vuln in vulnerabilities:
                sev = vuln.get('severity', 'INFO')
                if sev not in grouped:
                    grouped[sev] = []
                grouped[sev].append(vuln)
            
            for severity in severity_order:
                if severity in grouped:
                    story.append(Paragraph(
                        f"{severity} Severity ({len(grouped[severity])} found)",
                        ParagraphStyle('SeverityHeading', parent=styles['Heading3'], fontSize=14)
                    ))
                    
                    for i, vuln in enumerate(grouped[severity], 1):
                        vuln_text = f"""
                        <b>{i}. {vuln.get('type', 'Unknown').upper().replace('_', ' ')}</b><br/>
                        <b>Line:</b> {vuln.get('line', '?')}<br/>
                        <b>Description:</b> {vuln.get('description', 'N/A')}<br/>
                        <b>Confidence:</b> {vuln.get('confidence', 0.8):.1%}<br/>
                        <b>Remediation:</b> {vuln.get('remediation', 'N/A')}
                        """
                        story.append(Paragraph(vuln_text, styles['Normal']))
                        story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph("No vulnerabilities detected!", styles['Normal']))
        
        # LLM Audit Section
        if analysis_result.get('llm_audit'):
            story.append(PageBreak())
            story.append(Paragraph("AI Security Audit", heading_style))
            llm = analysis_result['llm_audit']
            
            story.append(Paragraph(f"<b>Risk Assessment:</b> {llm.get('risk_assessment', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            story.append(Paragraph("<b>Summary:</b>", styles['Heading3']))
            story.append(Paragraph(llm.get('summary', 'N/A'), styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            if llm.get('recommendations'):
                story.append(Paragraph("<b>Recommendations:</b>", styles['Heading3']))
                for rec in llm.get('recommendations', []):
                    story.append(Paragraph(f"• {rec}", styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            "<i>Generated by Solidity Vuln Scanner</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)
        ))
        story.append(Paragraph(
            "<i>⚠️ This report is for educational purposes only. Always conduct professional audits before deployment.</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.red)
        ))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF report generated: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}", exc_info=True)
        raise


def generate_pdf_report_bytes(analysis_result: Dict) -> bytes:
    """
    Generate PDF report as bytes (for API responses)
    
    Args:
        analysis_result: Analysis result dictionary
        
    Returns:
        PDF file as bytes
    """
    import io
    from reportlab.pdfgen import canvas
    
    buffer = io.BytesIO()
    # Use the same generation logic but write to buffer
    # For simplicity, we'll use a temp file approach
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp_path = tmp.name
    
    try:
        generate_pdf_report(analysis_result, tmp_path)
        with open(tmp_path, 'rb') as f:
            pdf_bytes = f.read()
        return pdf_bytes
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
