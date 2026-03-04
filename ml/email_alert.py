import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def send_heart_rate_alert(user_email, heart_rate):

    subject = "⚠️ Stress Alert: Sudden Heart Rate Spike Detected"

    body = f"""
Hello,

Your wearable device detected a sudden increase in heart rate.

Current Heart Rate: {heart_rate} BPM

This could be due to stress or physical strain.

Here are a few things you can try right now:

• Take 5 slow deep breaths
• Listen to calming music
• Take a short walk
• Talk to someone you trust
• Drink some water and relax

If you continue feeling stressed, consider taking a short break.

Stay safe and take care.

AI Stress Monitoring System
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = user_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, user_email, msg.as_string())