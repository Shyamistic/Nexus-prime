import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel

from app.core.config import settings
from app.models.incident import Incident, SeverityLevel

logger = logging.getLogger(__name__)

class NotificationChannel(str, Enum):
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"

class NotificationRule(BaseModel):
    severity_levels: List[SeverityLevel]
    channels: List[NotificationChannel]
    recipients: List[str]
    delay_minutes: int = 0
    escalate_after_minutes: Optional[int] = None

class NotificationService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def send_incident_notification(
        self, 
        incident: Incident, 
        event_type: str = "created",
        rules: List[NotificationRule] = None
    ):
        """Send notifications based on incident severity and rules"""
        
        if not rules:
            rules = self._get_default_rules(incident.severity)
            
        for rule in rules:
            if incident.severity in rule.severity_levels:
                if rule.delay_minutes > 0:
                    await asyncio.sleep(rule.delay_minutes * 60)
                    
                await self._send_to_channels(incident, event_type, rule)
                
    async def _send_to_channels(self, incident: Incident, event_type: str, rule: NotificationRule):
        """Send to all channels in parallel"""
        tasks = []
        
        for channel in rule.channels:
            if channel == NotificationChannel.SLACK:
                tasks.append(self._send_slack(incident, event_type, rule.recipients))
            elif channel == NotificationChannel.TEAMS:
                tasks.append(self._send_teams(incident, event_type, rule.recipients))
            elif channel == NotificationChannel.EMAIL:
                tasks.append(self._send_email(incident, event_type, rule.recipients))
            elif channel == NotificationChannel.SMS:
                tasks.append(self._send_sms(incident, event_type, rule.recipients))
            elif channel == NotificationChannel.TELEGRAM:
                tasks.append(self._send_telegram(incident, event_type, rule.recipients))
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_slack(self, incident: Incident, event_type: str, recipients: List[str]):
        """Send Slack notification with enhanced HITL features"""
        try:
            webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
            if not webhook_url:
                logger.info(f"📱 [MOCK] Slack notification: {event_type.title()} - {incident.title} (SEV{incident.severity.value[-1]})")
                return
                
            color = self._get_severity_color(incident.severity)
            
            # Enhanced payload with action buttons for HITL
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"🚨 Incident {event_type.title()}: {incident.title}",
                    "text": incident.summary,
                    "fields": [
                        {"title": "Severity", "value": incident.severity.value, "short": True},
                        {"title": "Status", "value": incident.status.value, "short": True},
                        {"title": "ID", "value": incident.id[:8], "short": True},
                        {"title": "Created", "value": incident.created_at.strftime("%Y-%m-%d %H:%M UTC"), "short": True}
                    ],
                    "actions": [
                        {
                            "type": "button",
                            "text": "🔍 View Details",
                            "url": f"http://localhost:3000/incidents/{incident.id}"
                        },
                        {
                            "type": "button",
                            "text": "✅ Acknowledge",
                            "style": "primary",
                            "value": f"ack_{incident.id}"
                        },
                        {
                            "type": "button",
                            "text": "🚨 Escalate",
                            "style": "danger",
                            "value": f"escalate_{incident.id}"
                        }
                    ],
                    "footer": "Nexus Prime | AI-Powered Incident Management",
                    "ts": int(incident.created_at.timestamp())
                }]
            }
            
            await self.client.post(webhook_url, json=payload)
            logger.info(f"📱 Slack notification sent for incident {incident.id}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            # Fallback to console log
            logger.info(f"📱 [FALLBACK] Slack notification: {event_type.title()} - {incident.title} (SEV{incident.severity.value[-1]})")
    
    async def _send_teams(self, incident: Incident, event_type: str, recipients: List[str]):
        """Send Microsoft Teams notification with enhanced features"""
        try:
            webhook_url = getattr(settings, 'TEAMS_WEBHOOK_URL', None)
            if not webhook_url:
                logger.info(f"💼 [MOCK] Teams notification: {event_type.title()} - {incident.title} (SEV{incident.severity.value[-1]})")
                return
                
            color = self._get_severity_color(incident.severity)
            
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color.replace("#", ""),
                "summary": f"Incident {event_type}: {incident.title}",
                "sections": [{
                    "activityTitle": f"🚨 Incident {event_type.title()}",
                    "activitySubtitle": incident.title,
                    "text": incident.summary,
                    "facts": [
                        {"name": "Severity", "value": incident.severity.value},
                        {"name": "Status", "value": incident.status.value},
                        {"name": "ID", "value": incident.id[:8]},
                        {"name": "AI Confidence", "value": f"{getattr(incident, 'ai_confidence', 0.85)*100:.0f}%"}
                    ]
                }],
                "potentialAction": [
                    {
                        "@type": "OpenUri",
                        "name": "View Incident",
                        "targets": [
                            {"os": "default", "uri": f"http://localhost:3000/incidents/{incident.id}"}
                        ]
                    }
                ]
            }
            
            await self.client.post(webhook_url, json=payload)
            logger.info(f"💼 Teams notification sent for incident {incident.id}")
            
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            logger.info(f"💼 [FALLBACK] Teams notification: {event_type.title()} - {incident.title} (SEV{incident.severity.value[-1]})")
    
    async def _send_email(self, incident: Incident, event_type: str, recipients: List[str]):
        """Send real email notification using SMTP"""
        try:
            # Email configuration from environment
            smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = getattr(settings, 'SMTP_PORT', 587)
            smtp_username = getattr(settings, 'SMTP_USERNAME', None)
            smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
            from_email = getattr(settings, 'FROM_EMAIL', smtp_username)
            
            if not smtp_username or not smtp_password:
                logger.info(f"📧 [MOCK] Email notification: {event_type.title()} - {incident.title} (No SMTP credentials)")
                return
            
            # Real recipient emails from environment or use defaults
            real_recipients = getattr(settings, 'EMAIL_RECIPIENTS', 'sre-team@company.com,on-call@company.com').split(',')
            
            subject = f"🚨 [{incident.severity.value}] Incident {event_type.title()}: {incident.title}"
            
            # Create HTML email content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <div style="border-left: 4px solid {self._get_severity_color(incident.severity)}; padding-left: 20px;">
                    <h2 style="color: #333;">🚨 Incident {event_type.title()}</h2>
                    <h3 style="color: {self._get_severity_color(incident.severity)};">{incident.title}</h3>
                    
                    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                        <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Severity:</td><td style="padding: 8px; border: 1px solid #ddd;">{incident.severity.value}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Status:</td><td style="padding: 8px; border: 1px solid #ddd;">{incident.status.value}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Incident ID:</td><td style="padding: 8px; border: 1px solid #ddd;">{incident.id[:8]}...</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Created:</td><td style="padding: 8px; border: 1px solid #ddd;">{incident.created_at.strftime('%Y-%m-%d %H:%M UTC')}</td></tr>
                    </table>
                    
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4>Summary:</h4>
                        <p>{incident.summary}</p>
                    </div>
                    
                    {f'<div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;"><h4>AI Analysis:</h4><p>{incident.ai_summary}</p></div>' if hasattr(incident, 'ai_summary') and incident.ai_summary else ''}
                    
                    <div style="margin: 20px 0;">
                        <a href="http://localhost:3000/incidents/{incident.id}" 
                           style="background-color: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Incident Details</a>
                    </div>
                    
                    <hr style="margin: 30px 0;">
                    <p style="color: #666; font-size: 12px;">This is an automated notification from Nexus Prime AI Incident Management System.</p>
                </div>
            </body>
            </html>
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = ', '.join(real_recipients)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"📧 Email sent successfully to {', '.join(real_recipients)}")
            logger.info(f"📧 Subject: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            # Fallback to mock for demo
            logger.info(f"📧 [FALLBACK] Email notification: {event_type.title()} - {incident.title}")
    
    async def _send_sms(self, incident: Incident, event_type: str, recipients: List[str]):
        """Send real SMS notification using Twilio"""
        try:
            # Try Twilio first
            twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            twilio_from = getattr(settings, 'TWILIO_FROM_NUMBER', None)
            
            if twilio_sid and twilio_token and twilio_from:
                try:
                    from twilio.rest import Client
                    
                    client = Client(twilio_sid, twilio_token)
                    
                    # Real phone numbers from environment
                    phone_numbers = getattr(settings, 'SMS_RECIPIENTS', '+1234567890').split(',')
                    
                    message = f"🚨 NEXUS ALERT [{incident.severity.value}]\n{incident.title}\nStatus: {incident.status.value}\nID: {incident.id[:8]}\nView: http://localhost:3000/incidents/{incident.id}"
                    
                    for phone in phone_numbers:
                        phone = phone.strip()
                        message_obj = client.messages.create(
                            body=message,
                            from_=twilio_from,
                            to=phone
                        )
                        logger.info(f"📱 SMS sent to {phone}, SID: {message_obj.sid}")
                    
                    return
                except ImportError:
                    logger.warning("Twilio not installed, trying AWS SNS")
            
            # Fallback to AWS SNS
            try:
                import boto3
                
                sns_region = getattr(settings, 'AWS_SNS_REGION', 'us-east-1')
                aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
                aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
                
                if aws_access_key and aws_secret_key:
                    sns = boto3.client(
                        'sns',
                        region_name=sns_region,
                        aws_access_key_id=aws_access_key,
                        aws_secret_access_key=aws_secret_key
                    )
                    
                    phone_numbers = getattr(settings, 'SMS_RECIPIENTS', '+1234567890').split(',')
                    message = f"🚨 NEXUS ALERT [{incident.severity.value}]\n{incident.title}\nStatus: {incident.status.value}\nID: {incident.id[:8]}\nView: http://localhost:3000/incidents/{incident.id}"
                    
                    for phone in phone_numbers:
                        phone = phone.strip()
                        response = sns.publish(
                            PhoneNumber=phone,
                            Message=message
                        )
                        logger.info(f"📱 SMS sent via AWS SNS to {phone}, MessageId: {response['MessageId']}")
                    
                    return
            except ImportError:
                logger.warning("boto3 not installed for AWS SNS")
            
            # No SMS service configured
            logger.info(f"📱 [MOCK] SMS notification: {event_type.title()} - {incident.title} (No SMS service configured)")
            
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
            logger.info(f"📱 [FALLBACK] SMS notification: {event_type.title()} - {incident.title}")
    
    async def _send_telegram(self, incident: Incident, event_type: str, recipients: List[str]):
        """Send real Telegram notification"""
        try:
            bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
            chat_ids = getattr(settings, 'TELEGRAM_CHAT_IDS', '').split(',')
            
            if not bot_token or not chat_ids[0]:
                logger.info(f"📱 [MOCK] Telegram notification: {event_type.title()} - {incident.title} (No Telegram credentials)")
                return
            
            message = f"""🚨 *Incident {event_type.title()}*

*{incident.title}*

📊 *Severity:* {incident.severity.value}
📈 *Status:* {incident.status.value}
🆔 *ID:* `{incident.id[:8]}`
⏰ *Created:* {incident.created_at.strftime('%Y-%m-%d %H:%M UTC')}

📝 *Summary:*
{incident.summary}

[View Details](http://localhost:3000/incidents/{incident.id})

_Nexus Prime AI Incident Management_"""
            
            # Send to each chat ID
            for chat_id in chat_ids:
                chat_id = chat_id.strip()
                if not chat_id:
                    continue
                    
                telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                }
                
                async with self.client.post(telegram_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"📱 Telegram message sent to {chat_id}, message_id: {result.get('result', {}).get('message_id')}")
                    else:
                        logger.error(f"Failed to send Telegram message to {chat_id}: {response.status}")
            
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            logger.info(f"📱 [FALLBACK] Telegram notification: {event_type.title()} - {incident.title}")
    
    def _get_severity_color(self, severity: SeverityLevel) -> str:
        """Get color code for severity level"""
        colors = {
            SeverityLevel.SEV1: "#FF0000",  # Red
            SeverityLevel.SEV2: "#FF8C00",  # Orange
            SeverityLevel.SEV3: "#FFD700",  # Yellow
            SeverityLevel.SEV4: "#32CD32"   # Green
        }
        return colors.get(severity, "#808080")
    
    def _get_default_rules(self, severity: SeverityLevel) -> List[NotificationRule]:
        """Get default notification rules based on severity with enhanced HITL"""
        if severity == SeverityLevel.SEV1:
            return [
                NotificationRule(
                    severity_levels=[SeverityLevel.SEV1],
                    channels=[NotificationChannel.SLACK, NotificationChannel.SMS, NotificationChannel.EMAIL, NotificationChannel.TELEGRAM],
                    recipients=["@channel", "sre-oncall", "engineering-leads"],
                    delay_minutes=0
                )
            ]
        elif severity == SeverityLevel.SEV2:
            return [
                NotificationRule(
                    severity_levels=[SeverityLevel.SEV2],
                    channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
                    recipients=["@here", "sre-team"],
                    delay_minutes=0
                )
            ]
        else:
            return [
                NotificationRule(
                    severity_levels=[SeverityLevel.SEV3, SeverityLevel.SEV4],
                    channels=[NotificationChannel.SLACK, NotificationChannel.TELEGRAM],
                    recipients=["#incidents", "@sre_team"],
                    delay_minutes=0
                )
            ]

# Global instance
notification_service = NotificationService()