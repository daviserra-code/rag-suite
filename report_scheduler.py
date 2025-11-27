"""
Scheduled Report Service
Runs automated reports on a schedule and emails them to recipients
"""
import os
import psycopg
from datetime import datetime, timedelta
from typing import List
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import schedule
import time
import sys
sys.path.insert(0, '/app')

from generate_report import generate_executive_report


DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
REPORT_EMAILS = os.getenv("REPORT_EMAILS", "").split(",")


def send_email_with_attachment(
    recipients: List[str],
    subject: str,
    body: str,
    attachment_bytes: bytes,
    attachment_name: str
):
    """Send email with PDF attachment"""
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("⚠️  Email not configured. Skipping email send.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'html'))
        
        # Add PDF attachment
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={attachment_name}')
        msg.attach(part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent to {len(recipients)} recipients")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def log_report_generation(report_type: str, period_start: str, period_end: str, 
                          file_size: int, recipients: int):
    """Log report generation to database"""
    try:
        conn = psycopg.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS report_history (
                report_id SERIAL PRIMARY KEY,
                report_type VARCHAR(50),
                period_start DATE,
                period_end DATE,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size_kb INTEGER,
                recipients_count INTEGER,
                status VARCHAR(20)
            )
        """)
        
        cur.execute("""
            INSERT INTO report_history 
            (report_type, period_start, period_end, file_size_kb, recipients_count, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (report_type, period_start, period_end, file_size // 1024, recipients, 'sent'))
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Could not log report: {e}")


def generate_and_send_report(report_type: str, days: int, recipients: List[str]):
    """Generate and send a scheduled report"""
    
    print(f"\n{'='*60}")
    print(f"📊 Generating {report_type} report...")
    print(f"{'='*60}")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"📅 Period: {start_date.date()} to {end_date.date()}")
    print(f"👥 Recipients: {len(recipients)}")
    
    try:
        # Generate report
        pdf_bytes = generate_executive_report(start_date, end_date, report_type)
        file_size = len(pdf_bytes)
        
        print(f"✅ Report generated: {file_size / 1024:.1f} KB")
        
        # Save to archive
        archive_dir = "/app/data/reports"
        os.makedirs(archive_dir, exist_ok=True)
        
        filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        archive_path = os.path.join(archive_dir, filename)
        
        with open(archive_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"💾 Archived to: {archive_path}")
        
        # Prepare email
        subject = f"{report_type.title()} Operations Report - {end_date.strftime('%B %d, %Y')}"
        
        body = f"""
        <html>
        <body style='font-family: Arial, sans-serif;'>
            <h2 style='color: #0d9488;'>Plant Operations {report_type.title()} Report</h2>
            
            <p>Please find attached the {report_type} operations report covering the period:</p>
            <p><strong>{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}</strong></p>
            
            <h3 style='color: #374151;'>Report Contents:</h3>
            <ul>
                <li>Executive Summary with Key Metrics</li>
                <li>Production Line Performance Analysis</li>
                <li>Downtime Analysis by Category</li>
                <li>Top 10 Issues and Root Causes</li>
                <li>Shift Performance Comparison</li>
            </ul>
            
            <p style='color: #6b7280; margin-top: 30px;'>
                This is an automated report generated by the Shopfloor Copilot system.<br>
                Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
            
            <hr style='border: 1px solid #e5e7eb; margin: 20px 0;'>
            
            <p style='color: #9ca3af; font-size: 12px;'>
                For questions or to adjust report settings, please contact the Production Management team.
            </p>
        </body>
        </html>
        """
        
        # Send email
        if recipients and recipients[0]:  # Check if recipients list is not empty
            if send_email_with_attachment(recipients, subject, body, pdf_bytes, filename):
                print(f"📧 Report emailed successfully")
            else:
                print(f"⚠️  Report generated but not emailed (check email configuration)")
        else:
            print(f"⚠️  No recipients configured. Report saved to archive only.")
        
        # Log to database
        log_report_generation(
            report_type,
            start_date.date(),
            end_date.date(),
            file_size,
            len(recipients)
        )
        
        print(f"{'='*60}\n")
        return True
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        print(f"{'='*60}\n")
        return False


def schedule_daily_report():
    """Schedule daily report at 6:00 AM"""
    generate_and_send_report("daily", 1, REPORT_EMAILS)


def schedule_weekly_report():
    """Schedule weekly report every Monday at 8:00 AM"""
    generate_and_send_report("weekly", 7, REPORT_EMAILS)


def schedule_monthly_report():
    """Schedule monthly report on 1st day at 9:00 AM"""
    generate_and_send_report("monthly", 30, REPORT_EMAILS)


def run_scheduler():
    """Run the report scheduler"""
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         SHOPFLOOR COPILOT - REPORT SCHEDULER              ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print(f"⏰ Scheduling reports...")
    print(f"📧 Recipients: {', '.join(REPORT_EMAILS) if REPORT_EMAILS[0] else 'None configured'}")
    print()
    
    # Schedule reports
    schedule.every().day.at("06:00").do(schedule_daily_report)
    schedule.every().monday.at("08:00").do(schedule_weekly_report)
    schedule.every().month.at("09:00").do(schedule_monthly_report)
    
    print("📅 Scheduled Reports:")
    print("   • Daily Report:    06:00 every day")
    print("   • Weekly Report:   08:00 every Monday")
    print("   • Monthly Report:  09:00 on 1st of month")
    print()
    print("✅ Scheduler is running. Press Ctrl+C to stop.")
    print()
    
    # Run immediately for testing (optional)
    if os.getenv("RUN_REPORT_ON_START", "false").lower() == "true":
        print("🚀 Running test report on startup...")
        schedule_daily_report()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    run_scheduler()
