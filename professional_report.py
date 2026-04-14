"""
Professional Audit Report Generator
Creates comprehensive reports suitable for professional security audits
"""

from typing import Dict
from datetime import datetime
from professional_auditor import ProfessionalAuditResult
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import json


def generate_professional_audit_report_pdf(audit_result: ProfessionalAuditResult, output_path: str = None):
    """
    Generate professional PDF audit report
    
    Args:
        audit_result: ProfessionalAuditResult object
        output_path: Optional output file path
        
    Returns:
        PDF bytes if output_path not provided, otherwise writes to file
    """
    if output_path is None:
        output_path = f"/tmp/{audit_result.contract_name}_audit_report.pdf"
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
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
        spaceBefore=20
    )
    
    # Title
    story.append(Paragraph("Professional Security Audit Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(f"<b>Contract:</b> {audit_result.contract_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Audit Date:</b> {audit_result.analysis_date}", styles['Normal']))
    story.append(Paragraph(f"<b>Audit Version:</b> {audit_result.audit_version}", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    # Risk Assessment
    severity_color = {
        "CRITICAL": colors.red,
        "HIGH": colors.orange,
        "MEDIUM": colors.yellow,
        "LOW": colors.blue,
        "SAFE": colors.green
    }.get(audit_result.overall_severity, colors.black)
    
    story.append(Paragraph(
        f"<b>Overall Severity:</b> <font color='{severity_color.hexval()}'>{audit_result.overall_severity}</font>",
        styles['Normal']
    ))
    story.append(Paragraph(f"<b>Risk Score:</b> {audit_result.risk_score:.1f}/100", styles['Normal']))
    story.append(Paragraph(f"<b>Confidence Level:</b> {audit_result.confidence_level}", styles['Normal']))
    story.append(Paragraph(f"<b>Total Vulnerabilities:</b> {len(audit_result.vulnerabilities)}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Critical Findings
    if audit_result.critical_findings:
        story.append(Paragraph("Critical Findings", heading_style))
        for finding in audit_result.critical_findings:
            story.append(Paragraph(f"• {finding}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # Compliance Section
    story.append(Paragraph("Compliance Assessment", heading_style))
    story.append(Paragraph(f"<b>SWC Compliance Status:</b> {audit_result.compliance_status}", styles['Normal']))
    story.append(Paragraph(f"<b>SWC Issues Found:</b> {audit_result.swc_compliance.get('total_swc_issues', 0)}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # SWC Findings Table
    if audit_result.swc_compliance.get('swc_findings'):
        story.append(Paragraph("SWC Classified Vulnerabilities", styles['Heading3']))
        swc_data = [['SWC ID', 'Title', 'Count', 'Severity']]
        for finding in audit_result.swc_compliance['swc_findings']:
            swc_data.append([
                finding['swc_id'],
                finding['swc_title'],
                str(finding['count']),
                finding['severity']
            ])
        
        swc_table = Table(swc_data, colWidths=[1*inch, 3*inch, 0.8*inch, 1.2*inch])
        swc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(swc_table)
        story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # Vulnerability Details
    story.append(Paragraph("Detailed Vulnerability Findings", heading_style))
    
    for i, vuln in enumerate(audit_result.vulnerabilities, 1):
        story.append(Paragraph(f"{i}. {vuln.vuln_type.upper()} - Line {vuln.line_number}", styles['Heading3']))
        story.append(Paragraph(f"<b>Severity:</b> {vuln.severity}", styles['Normal']))
        story.append(Paragraph(f"<b>SWC ID:</b> {get_swc_info(vuln.vuln_type)['swc_id']}", styles['Normal']))
        story.append(Paragraph(f"<b>Description:</b> {vuln.description}", styles['Normal']))
        story.append(Paragraph(f"<b>Confidence:</b> {vuln.confidence:.1%}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph("<b>Code Snippet:</b>", styles['Normal']))
        story.append(Paragraph(f"<pre>{vuln.code_snippet[:200]}</pre>", styles['Code']))
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph("<b>Remediation:</b>", styles['Normal']))
        story.append(Paragraph(vuln.remediation, styles['Normal']))
        story.append(Spacer(1, 0.15*inch))
    
    story.append(PageBreak())
    
    # Code Metrics
    story.append(Paragraph("Code Metrics", heading_style))
    metrics_data = [
        ['Metric', 'Value'],
        ['Lines of Code', str(audit_result.lines_of_code)],
        ['Total Functions', str(audit_result.function_count)],
        ['Public/External Functions', str(audit_result.public_function_count)],
        ['Cyclomatic Complexity', f"{audit_result.cyclomatic_complexity:.2f}"],
        ['Risk Score', f"{audit_result.risk_score:.1f}/100"]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Recommendations
    story.append(Paragraph("Recommendations", heading_style))
    story.append(Paragraph("<b>High Priority:</b>", styles['Heading3']))
    for rec in audit_result.high_priority_recommendations:
        story.append(Paragraph(f"• {rec}", styles['Normal']))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Audit Notes", heading_style))
    for note in audit_result.audit_notes:
        story.append(Paragraph(f"• {note}", styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "<i>This is an automated security analysis report. For production deployments, "
        "engage professional security auditors for comprehensive manual review.</i>",
        styles['Italic']
    ))
    
    # Build PDF
    doc.build(story)
    
    if output_path:
        with open(output_path, 'rb') as f:
            return f.read()
    return None


def generate_professional_audit_report_json(audit_result: ProfessionalAuditResult) -> Dict:
    """Generate JSON format professional audit report"""
    return audit_result.to_dict()


def generate_professional_audit_report_html(audit_result: ProfessionalAuditResult) -> str:
    """Generate HTML format professional audit report"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Professional Audit Report - {audit_result.contract_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; }}
            .severity-critical {{ color: #ef4444; font-weight: bold; }}
            .severity-high {{ color: #f59e0b; font-weight: bold; }}
            .severity-medium {{ color: #eab308; font-weight: bold; }}
            .severity-low {{ color: #3b82f6; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #667eea; color: white; }}
            .code-block {{ background: #f4f4f4; padding: 15px; border-left: 4px solid #667eea; margin: 10px 0; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Professional Security Audit Report</h1>
            <p><strong>Contract:</strong> {audit_result.contract_name}</p>
            <p><strong>Audit Date:</strong> {audit_result.analysis_date}</p>
            <p><strong>Audit Version:</strong> {audit_result.audit_version}</p>
        </div>
        
        <h2>Executive Summary</h2>
        <p><strong>Overall Severity:</strong> <span class="severity-{audit_result.overall_severity.lower()}">{audit_result.overall_severity}</span></p>
        <p><strong>Risk Score:</strong> {audit_result.risk_score:.1f}/100</p>
        <p><strong>Confidence Level:</strong> {audit_result.confidence_level}</p>
        <p><strong>Total Vulnerabilities:</strong> {len(audit_result.vulnerabilities)}</p>
        
        <h2>Critical Findings</h2>
        <ul>
    """
    
    for finding in audit_result.critical_findings:
        html += f"<li>{finding}</li>"
    
    html += """
        </ul>
        
        <h2>Compliance Assessment</h2>
        <p><strong>SWC Compliance:</strong> """ + audit_result.compliance_status + """</p>
        <p><strong>SWC Issues Found:</strong> """ + str(audit_result.swc_compliance.get('total_swc_issues', 0)) + """</p>
        
        <h2>Vulnerability Details</h2>
    """
    
    for i, vuln in enumerate(audit_result.vulnerabilities, 1):
        swc_info = get_swc_info(vuln.vuln_type)
        html += f"""
        <h3>{i}. {vuln.vuln_type.upper()} - Line {vuln.line_number}</h3>
        <p><strong>Severity:</strong> <span class="severity-{vuln.severity.lower()}">{vuln.severity}</span></p>
        <p><strong>SWC ID:</strong> {swc_info['swc_id']}</p>
        <p><strong>CWE:</strong> {swc_info.get('cwe', 'N/A')}</p>
        <p><strong>OWASP:</strong> {swc_info.get('owasp', 'N/A')}</p>
        <p><strong>Description:</strong> {vuln.description}</p>
        <p><strong>Confidence:</strong> {vuln.confidence:.1%}</p>
        <div class="code-block">{vuln.code_snippet}</div>
        <p><strong>Remediation:</strong> {vuln.remediation}</p>
        <hr>
        """
    
    html += """
        <h2>Recommendations</h2>
        <h3>High Priority</h3>
        <ul>
    """
    
    for rec in audit_result.high_priority_recommendations:
        html += f"<li>{rec}</li>"
    
    html += """
        </ul>
        
        <h2>Code Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Lines of Code</td><td>""" + str(audit_result.lines_of_code) + """</td></tr>
            <tr><td>Total Functions</td><td>""" + str(audit_result.function_count) + """</td></tr>
            <tr><td>Public Functions</td><td>""" + str(audit_result.public_function_count) + """</td></tr>
            <tr><td>Cyclomatic Complexity</td><td>""" + f"{audit_result.cyclomatic_complexity:.2f}" + """</td></tr>
        </table>
        
        <hr>
        <p><em>This is an automated security analysis report. For production deployments, engage professional security auditors for comprehensive manual review.</em></p>
    </body>
    </html>
    """
    
    return html
