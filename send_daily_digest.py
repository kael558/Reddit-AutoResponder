#!/usr/bin/env python3
"""
Daily Digest Email Sender
Sends a compiled email of all leads collected throughout the day.
Run this script at the end of each day using cron on Digital Ocean droplet.

Example crontab entry (runs at 11:59 PM daily):
59 23 * * * cd /path/to/AutoResponder && /usr/bin/python3 send_daily_digest.py >> digest_log.txt 2>&1
"""

import os
import json
import smtplib
import glob
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==== EMAIL CONFIGURATION ====
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_SMTP_SERVER = "mail.privateemail.com"
EMAIL_SMTP_PORT = 587
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL", EMAIL_ADDRESS)

def generate_digest_email(leads):
    """Generate HTML email with all daily leads"""
    
    total_leads = len(leads)
    
    # Generate lead cards HTML
    lead_cards_html = ""
    for idx, lead in enumerate(leads, 1):
        username = lead.get('username', 'Unknown')
        subreddit = lead.get('subreddit', 'Unknown')
        content_type = lead.get('content_type', 'unknown')
        similarity_score = lead.get('similarity_score', 0)
        best_topic = lead.get('best_matching_topic', 'N/A')
        reddit_score = lead.get('reddit_score', 0)
        timestamp = lead.get('timestamp', 'N/A')
        llm_verification = lead.get('llm_verification', 'N/A')
        recommended_message = lead.get('recommended_message', '')
        reddit_profile_url = lead.get('reddit_profile_url', '')
        content_url = lead.get('content_url', '')
        
        # Get content preview
        content_data = lead.get('content_data', {})
        if content_type == 'post':
            title = content_data.get('title', 'N/A')
            body = content_data.get('body', '')
            content_preview = f"""
                <p><strong>Title:</strong> {title}</p>
                <p><strong>Body:</strong> {body[:300]}{'...' if len(body) > 300 else ''}</p>
            """
        else:  # comment
            comment = content_data.get('comment', '')
            content_preview = f"""
                <p><strong>Comment:</strong> {comment[:300]}{'...' if len(comment) > 300 else ''}</p>
            """
        
        lead_cards_html += f"""
        <div style="background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #ff4500;">
            <h3 style="color: #ff4500; margin-top: 0;">Lead #{idx} - u/{username}</h3>
            
            <div style="background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 3px;">
                <p style="margin: 5px 0;"><strong>Subreddit:</strong> r/{subreddit}</p>
                <p style="margin: 5px 0;"><strong>Content Type:</strong> {content_type.upper()}</p>
                <p style="margin: 5px 0;"><strong>Similarity Score:</strong> {similarity_score:.2f}</p>
                <p style="margin: 5px 0;"><strong>Reddit Score:</strong> {reddit_score}</p>
                <p style="margin: 5px 0;"><strong>Matching Topic:</strong> {best_topic}</p>
                <p style="margin: 5px 0;"><strong>Time:</strong> {timestamp}</p>
            </div>
            
            <div style="margin: 15px 0;">
                <h4 style="color: #1a73e8; margin-bottom: 10px;">Content:</h4>
                {content_preview}
            </div>
            
            <div style="margin: 15px 0;">
                <h4 style="color: #1a73e8; margin-bottom: 10px;">Recommended Message:</h4>
                <div style="background-color: #f0f0f0; padding: 12px; border-left: 4px solid #1a73e8; white-space: pre-wrap; font-size: 14px;">
{recommended_message}
                </div>
            </div>
            
            <div style="margin: 15px 0;">
                <h4 style="color: #1a73e8; margin-bottom: 10px;">LLM Verification:</h4>
                <p style="font-size: 14px; color: #666;">{llm_verification}</p>
            </div>
            
            <div style="margin-top: 20px; text-align: center;">
                <a href="{reddit_profile_url}" style="display: inline-block; padding: 10px 20px; background-color: #ff4500; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px; font-size: 14px;">
                    📧 DM User
                </a>
                <a href="{content_url}" style="display: inline-block; padding: 10px 20px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px; font-size: 14px;">
                    🔗 View Post
                </a>
            </div>
        </div>
        """
    
    # Create complete HTML email
    html_content = f"""
<html>
<head></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5;">
    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #ff4500; color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
            <h1 style="margin: 0; font-size: 32px;">📊 Daily Lead Digest</h1>
            <p style="margin: 10px 0 0 0; font-size: 18px;">Fluent Future - English Learning Leads</p>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{datetime.now().strftime('%A, %B %d, %Y')}</p>
        </div>
        
        <div style="background-color: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="background-color: #e8f4f8; padding: 20px; border-radius: 5px; text-align: center; margin-bottom: 30px;">
                <h2 style="color: #1a73e8; margin: 0; font-size: 48px;">{total_leads}</h2>
                <p style="color: #666; margin: 5px 0 0 0; font-size: 18px;">Total Leads Today</p>
            </div>
            
            {lead_cards_html if total_leads > 0 else '<p style="text-align: center; color: #666; font-size: 18px; padding: 40px 0;">No leads were collected today.</p>'}
        </div>
        
        <div style="text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 14px;">
            <p>This is an automated daily digest from your Reddit lead monitoring bot.</p>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Create plain text version
    text_content = f"""
Daily Lead Digest - Fluent Future
{datetime.now().strftime('%A, %B %d, %Y')}

{'='*60}
SUMMARY
{'='*60}
Total Leads Today: {total_leads}

"""
    
    if total_leads > 0:
        for idx, lead in enumerate(leads, 1):
            username = lead.get('username', 'Unknown')
            subreddit = lead.get('subreddit', 'Unknown')
            content_type = lead.get('content_type', 'unknown')
            similarity_score = lead.get('similarity_score', 0)
            reddit_profile_url = lead.get('reddit_profile_url', '')
            content_url = lead.get('content_url', '')
            
            content_data = lead.get('content_data', {})
            if content_type == 'post':
                title = content_data.get('title', 'N/A')
                body = content_data.get('body', '')[:200]
                content_text = f"Title: {title}\nBody: {body}"
            else:
                comment = content_data.get('comment', '')[:200]
                content_text = f"Comment: {comment}"
            
            text_content += f"""
{'='*60}
LEAD #{idx}: u/{username}
{'='*60}
Subreddit: r/{subreddit}
Content Type: {content_type.upper()}
Similarity Score: {similarity_score:.2f}

Content:
{content_text}

Links:
- DM User: {reddit_profile_url}
- View Post: {content_url}

"""
    else:
        text_content += "No leads were collected today.\n"
    
    text_content += f"""
{'='*60}
Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}
"""
    
    return html_content, text_content

def send_digest_email(leads, date_str):
    """Send the daily digest email"""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("⚠️ Email credentials not configured")
        return False
    
    try:
        # Generate email content
        html_content, text_content = generate_digest_email(leads)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Daily Lead Digest - {datetime.now().strftime("%B %d, %Y")} ({len(leads)} leads)'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = NOTIFICATION_EMAIL
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Connect to SMTP server and send
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Daily digest email sent to {NOTIFICATION_EMAIL} ({len(leads)} leads)")
        return True
        
    except Exception as e:
        print(f"⚠️ Error sending daily digest email: {e}")
        return False

def archive_pending_file(filename):
    """Move pending email file to archive"""
    try:
        archive_dir = "email_archives"
        os.makedirs(archive_dir, exist_ok=True)
        
        # Move file to archive
        archive_path = os.path.join(archive_dir, os.path.basename(filename))
        os.rename(filename, archive_path)
        print(f"📦 Archived {filename} to {archive_path}")
        return True
    except Exception as e:
        print(f"⚠️ Error archiving file: {e}")
        return False

def main():
    """Main function to send daily digest"""
    print("="*60)
    print("📧 Daily Digest Email Sender")
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")
    pending_file = f"pending_emails_{today}.json"
    
    # Check if pending file exists
    if not os.path.exists(pending_file):
        print(f"ℹ️ No pending email file found for {today}")
        print("ℹ️ No leads to send today")
        
        # Also check for any older pending files
        older_files = glob.glob("pending_emails_*.json")
        if older_files:
            print(f"\n⚠️ Found {len(older_files)} older pending file(s):")
            for old_file in older_files:
                print(f"   - {old_file}")
                try:
                    with open(old_file, 'r', encoding='utf-8') as f:
                        old_leads = json.load(f)
                    
                    # Extract date from filename
                    old_date = old_file.replace('pending_emails_', '').replace('.json', '')
                    
                    print(f"\n📧 Sending digest for {old_date} ({len(old_leads)} leads)...")
                    if send_digest_email(old_leads, old_date):
                        archive_pending_file(old_file)
                except Exception as e:
                    print(f"⚠️ Error processing {old_file}: {e}")
        
        return
    
    try:
        # Load pending emails
        with open(pending_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        
        print(f"📊 Found {len(leads)} lead(s) for {today}")
        
        # Send digest email
        if send_digest_email(leads, today):
            # Archive the pending file
            archive_pending_file(pending_file)
        else:
            print("⚠️ Failed to send digest email. Pending file will be kept for retry.")
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return
    
    print("\n✅ Daily digest process completed")
    print("="*60)

if __name__ == "__main__":
    main()

