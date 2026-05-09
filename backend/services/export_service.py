"""
Export Service - Generate professional reports in PDF and JSON formats
"""
import json
import logging
import os
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available, PDF export will be limited")


class ExportService:
    """Generate professional reports and exports"""
    
    def __init__(self, reports_dir: str = "results/reports"):
        """
        Initialize export service
        
        Args:
            reports_dir: Directory to store generated reports
        """
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
    
    def export_json(
        self,
        analysis_data: Dict[str, Any],
        output_path: str = None,
        pretty: bool = True
    ) -> Dict[str, Any]:
        """
        Export analysis results as JSON
        
        Args:
            analysis_data: Complete analysis data
            output_path: Output file path
            pretty: Format JSON prettily
        
        Returns:
            Export result
        """
        try:
            if output_path is None:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(
                    self.reports_dir,
                    f"analysis_report_{timestamp}.json"
                )
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Prepare data for JSON serialization
            export_data = self._prepare_json_data(analysis_data)
            
            # Write JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(export_data, f, ensure_ascii=False)
            
            file_size = os.path.getsize(output_path)
            
            return {
                "status": "success",
                "export_type": "json",
                "output_path": output_path,
                "file_size": file_size,
                "timestamp": self._get_timestamp()
            }
        
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def export_pdf(
        self,
        analysis_data: Dict[str, Any],
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Export analysis results as PDF report
        
        Args:
            analysis_data: Complete analysis data
            output_path: Output file path
        
        Returns:
            Export result
        """
        if not REPORTLAB_AVAILABLE:
            return {
                "status": "error",
                "error": "ReportLab not available for PDF generation"
            }
        
        try:
            if output_path is None:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(
                    self.reports_dir,
                    f"analysis_report_{timestamp}.pdf"
                )
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a2e'),
                spaceAfter=30,
                alignment=1  # Center
            )
            elements.append(Paragraph("Video Analysis Report", title_style))
            elements.append(Spacer(1, 0.3*inch))
            
            # Metadata
            meta_data = [
                ['Analysis Date', self._get_timestamp()],
                ['Video File', analysis_data.get('video_filename', 'N/A')],
                ['Duration', self._format_duration(analysis_data.get('duration_seconds', 0))],
                ['Status', analysis_data.get('status', 'Unknown')]
            ]
            
            meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
            meta_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8e8e8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            elements.append(meta_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Summary Section
            elements.append(Paragraph("Analysis Summary", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            summary_text = analysis_data.get('caption_summary', 'No summary available')
            elements.append(Paragraph(summary_text, styles['BodyText']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Key Metrics
            elements.append(Paragraph("Key Metrics", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            metrics = []
            if 'confidence_scores' in analysis_data:
                for key, value in analysis_data['confidence_scores'].items():
                    metrics.append([key.replace('_', ' ').title(), f"{value*100:.1f}%"])
            
            if metrics:
                metrics_table = Table(metrics, colWidths=[2.5*inch, 2.5*inch])
                metrics_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(metrics_table)
            
            elements.append(Spacer(1, 0.3*inch))
            
            # Timeline Section
            if 'timeline' in analysis_data:
                elements.append(PageBreak())
                elements.append(Paragraph("Event Timeline", styles['Heading2']))
                elements.append(Spacer(1, 0.1*inch))
                
                timeline_events = analysis_data['timeline'].get('timeline', [])[:10]  # First 10 events
                
                for event in timeline_events:
                    event_text = f"<b>{event.get('timestamp', 'N/A')}</b> - {event.get('description', 'N/A')}"
                    elements.append(Paragraph(event_text, styles['BodyText']))
                    elements.append(Spacer(1, 0.05*inch))
            
            # Detections Summary
            elements.append(PageBreak())
            elements.append(Paragraph("Detection Results", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            detection_summary = analysis_data.get('detection_summary', {})
            if detection_summary:
                for key, value in detection_summary.items():
                    elements.append(Paragraph(f"<b>{key}:</b> {value}", styles['BodyText']))
                    elements.append(Spacer(1, 0.05*inch))
            
            # Build PDF
            doc.build(elements)
            
            file_size = os.path.getsize(output_path)
            
            return {
                "status": "success",
                "export_type": "pdf",
                "output_path": output_path,
                "file_size": file_size,
                "timestamp": self._get_timestamp()
            }
        
        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def export_combined(
        self,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Export both JSON and PDF reports
        
        Args:
            analysis_data: Complete analysis data
        
        Returns:
            Combined export results
        """
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            
            json_result = self.export_json(
                analysis_data,
                os.path.join(self.reports_dir, f"analysis_report_{timestamp}.json")
            )
            
            pdf_result = self.export_pdf(
                analysis_data,
                os.path.join(self.reports_dir, f"analysis_report_{timestamp}.pdf")
            )
            
            return {
                "status": "success",
                "json_export": json_result,
                "pdf_export": pdf_result,
                "timestamp": self._get_timestamp()
            }
        
        except Exception as e:
            logger.error(f"Error in combined export: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    def _prepare_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for JSON serialization (remove non-serializable objects)"""
        # Create a copy to avoid modifying original
        prepared = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                prepared[key] = ExportService._prepare_json_data(value)
            elif isinstance(value, list):
                prepared[key] = [
                    ExportService._prepare_json_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif hasattr(value, '__dict__'):
                # Handle custom objects
                prepared[key] = str(value)
            else:
                prepared[key] = value
        
        return prepared
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        if not seconds:
            return "N/A"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        return datetime.now(timezone.utc).isoformat()
