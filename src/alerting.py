# Alerting System
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class AlertManager:
    def __init__(self):
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': os.getenv('EMAIL_ADDRESS'),
            'sender_password': os.getenv('EMAIL_APP_PASSWORD'),
            'recipient_email': os.getenv('ALERT_EMAIL')
        }
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    
    def send_email_alert(self, anomaly_data):
        """Send email notification for detected anomaly."""
        subject = f"🚨 Stock Anomaly Alert: {anomaly_data['symbol']}"
        
        body = f"""
        ANOMALY DETECTED
        
        Symbol: {anomaly_data['symbol']}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Z-Score: {anomaly_data['z_score']}
        Direction: {anomaly_data['direction']}
        Current Price: ${anomaly_data['current_price']:.2f}
        
        This is an automated alert from your Anomaly Detection System.
        """
        
        msg = MIMEMultipart()
        msg['From'] = self.email_config['sender_email']
        msg['To'] = self.email_config['recipient_email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(self.email_config['smtp_server'], 
                            self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], 
                           self.email_config['sender_password'])
                server.send_message(msg)
            print(f"Alert sent for {anomaly_data['symbol']}")
        except Exception as e:
            print(f"Failed to send email: {e}")
    
    def send_slack_alert(self, anomaly_data):
        """Send Slack notification (optional enhancement)."""
        if not self.slack_webhook:
            return
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 Anomaly: {anomaly_data['symbol']}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Z-Score:* {anomaly_data['z_score']}"},
                        {"type": "mrkdwn", "text": f"*Direction:* {anomaly_data['direction']}"},
                        {"type": "mrkdwn", "text": f"*Price:* ${anomaly_data['current_price']:.2f}"},
                        {"type": "mrkdwn", "text": f"*Time:* {datetime.now().strftime('%H:%M:%S')}"}
                    ]
                }
            ]
        }
        
        try:
            requests.post(self.slack_webhook, json=message)
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")