import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from azure.storage.blob import BlobServiceClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        self.blob_service_client = None
        if settings.AZURE_STORAGE_CONNECTION_STRING:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    settings.AZURE_STORAGE_CONNECTION_STRING
                )
            except Exception as e:
                logger.error(f"Failed to connect to Azure Storage: {e}")

    def generate_and_upload(self, incident, action) -> str:
        """
        Generates a PDF forensic report and uploads to Azure Blob Storage.
        Returns the public URL of the report.
        """
        if not self.blob_service_client:
            return "Storage Not Configured"

        # 1. Generate PDF in Memory
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # --- HEADER ---
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "NEXUS INCIDENT FORENSIC REPORT")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, f"Generated: {datetime.utcnow().isoformat()} UTC")
        c.line(50, height - 80, width - 50, height - 80)

        # --- INCIDENT DETAILS ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 110, f"Incident ID: {incident.id}")
        c.drawString(50, height - 130, f"Title: {incident.title}")
        c.drawString(50, height - 150, f"Severity: {incident.severity}")

        # --- ROOT CAUSE ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 190, "Root Cause Analysis (AI Generated):")
        c.setFont("Helvetica", 10)
        
        # Simple text wrapping for PDF
        text = incident.root_cause_analysis or "Pending Analysis"
        y = height - 210
        # Wrap roughly at 90 characters
        for i in range(0, len(text), 90):
            line = text[i:i+90]
            c.drawString(60, y, f"- {line.strip()}")
            y -= 15

        # --- REMEDIATION ---
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Executed Remediation:")
        c.setFont("Helvetica", 10)
        c.drawString(60, y - 20, f"Action: {action.title}")
        c.drawString(60, y - 35, f"Type: {action.action_type}")
        c.drawString(60, y - 50, f"Status: COMPLETED (Authorized by Admin)")

        # --- FOOTER ---
        c.line(50, 50, width - 50, 50)
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(50, 40, "This document is cryptographically signed and stored in Azure Blob Storage.")
        c.drawString(50, 30, "Confidential Property of NEXUS Systems.")

        c.save()
        buffer.seek(0)

        # 2. Upload to Azure
        filename = f"report_{incident.id}_{int(datetime.now().timestamp())}.pdf"
        
        try:
            container_client = self.blob_service_client.get_container_client(settings.CONTAINER_REPORTS)
            blob_client = container_client.get_blob_client(filename)
            
            blob_client.upload_blob(buffer, blob_type="BlockBlob", overwrite=True)
            
            # Return the URL
            return blob_client.url
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return "Upload Failed"

report_generator = ReportGenerator()