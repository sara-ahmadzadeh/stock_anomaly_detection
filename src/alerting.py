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
        """Send professional email notification with full context and reasoning."""
        if not self.email_config['sender_email'] or not self.email_config['sender_password']:
            logger.warning("Email not configured. Skipping alert.")
            return False
        
        symbol = anomaly_data.get('symbol', 'Unknown')
        confidence = anomaly_data.get('confidence', 0)
        direction = anomaly_data.get('direction', 'unknown')
        z_score = anomaly_data.get('z_score', 0)
        price = anomaly_data.get('current_price', 0)
        change_pct = anomaly_data.get('price_change_pct', 0)
        recommendation = anomaly_data.get('recommendation', '')
        market_context = anomaly_data.get('market_context', '')
        rsi = anomaly_data.get('rsi', 'N/A')
        macd = anomaly_data.get('macd', 'N/A')
        indicator_action = anomaly_data.get('indicator_action', 'N/A')
        indicator_confidence = anomaly_data.get('indicator_confidence', 0)
        news_headlines = anomaly_data.get('news_headlines', [])
        
        # Confidence level
        if confidence >= 80:
            level = "🔴 HIGH"
        elif confidence >= 50:
            level = "🟠 MEDIUM"
        else:
            level = "🔵 LOW"
        
        direction_emoji = "🔺" if direction == 'up' else "🔻"
        
        # Build signal explanation
        if 'SELL' in str(indicator_action) and direction == 'up':
            signal_explanation = "📈 Price is UP but indicators suggest OVERBOUGHT — consider taking profits"
        elif 'SELL' in str(indicator_action) and direction == 'down':
            signal_explanation = "📉 Price is DOWN with bearish momentum — downtrend may continue"
        elif 'BUY' in str(indicator_action) and direction == 'down':
            signal_explanation = "📉 Price is DOWN but indicators suggest OVERSOLD — potential bounce opportunity"
        elif 'BUY' in str(indicator_action) and direction == 'up':
            signal_explanation = "📈 Price is UP with bullish momentum — trend may continue"
        else:
            signal_explanation = "📊 Mixed signals — wait for clearer direction"
        
        # Build reasoning chain
        reasoning_steps = []
        if abs(change_pct) > 2:
            word = "surged" if change_pct > 0 else "dropped"
            reasoning_steps.append(f"Price {word} {change_pct:+.1f}%")
        if rsi and rsi != 'N/A':
            if float(rsi) > 70:
                reasoning_steps.append(f"RSI={rsi} → Overbought")
            elif float(rsi) < 30:
                reasoning_steps.append(f"RSI={rsi} → Oversold")
        if abs(z_score) > 4:
            reasoning_steps.append(f"Z-Score={z_score} → Very unusual movement")
        reasoning_chain = " → ".join(reasoning_steps) if reasoning_steps else "Statistical anomaly detected"
        
        subject = f"{level} {direction_emoji} {symbol} Anomaly: {change_pct:+.2f}% (Confidence: {confidence}%)"
        
        # Build email body
        body = f"""
    ╔══════════════════════════════════════════════╗
    ║     CRYPTO ANOMALY DETECTION ALERT           ║
    ╚══════════════════════════════════════════════╝

    ASSET: {symbol}
    TIME:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    ALERT LEVEL: {level}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    📊 MARKET DATA
    Price:      ${price:,.2f}
    Change:     {change_pct:+.2f}%
    Direction:  {direction.upper()}
    Z-Score:    {z_score}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    🎯 DETECTION CONFIDENCE: {confidence}%
    Market Context: {market_context}

    🧠 REASONING:
    {reasoning_chain}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    📈 TECHNICAL INDICATORS
    RSI:           {rsi}
    MACD:          {macd}
    Signal:        {indicator_action} ({indicator_confidence}% confidence)
    Interpretation: {signal_explanation}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    💡 RECOMMENDED ACTION:
    {recommendation}
    """
        
        # Add news if available
        if news_headlines:
            body += """
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    📰 RELATED NEWS:"""
            for h in news_headlines:
                body += f"\n   • {h['title'][:100]}"
                if h.get('url'):
                    body += f"\n     {h['url']}\n"
        
        body += f"""
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    📊 Live Dashboard: http://localhost:8050

    ⚠️ DISCLAIMER:
    This is an automated decision support alert, not financial advice.
    Always do your own research before making trading decisions.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Sent by Crypto Anomaly Detection System v2.0
    """
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.email_config['smtp_server'], 
                            self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], 
                        self.email_config['sender_password'])
                server.send_message(msg)
            
            logger.info(f"✅ Alert email sent for {symbol}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Auth failed: Wrong email or password. Error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

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