#!/usr/bin/env python3
"""
WebIndexer Daily Lead Digest Sender
Sends a compiled email of WebIndexer leads collected throughout a day.

Usage examples:
  - Send today's digest:              python3 send_daily_webindexer_leads.py
  - Send a specific date's digest:    python3 send_daily_webindexer_leads.py --date 2025-11-05

This script mirrors the behavior of send_daily_digest.py but targets
the WebIndexer lead files (webindexer_leads_YYYY-MM-DD.json).
"""

import os
import json
import glob
from datetime import datetime
from dotenv import load_dotenv
import requests
import argparse


# Load environment variables
load_dotenv()


# ==== EMAIL CONFIGURATION ====
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
SMTP2GO_API_KEY = os.environ.get("SMTP2GO_API_KEY", "")
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL", EMAIL_ADDRESS)
SMTP2GO_API_URL = "https://api.smtp2go.com/v3/email/send"
REPLY_TO = os.environ.get("REPLY_TO", EMAIL_ADDRESS)


# ==== OPTIONAL WEBINDEXER LINKS ====
WEBINDEXER_SITE_URL = os.environ.get("WEBINDEXER_SITE_URL", "")
WEBINDEXER_DEMO_URL = os.environ.get("WEBINDEXER_DEMO_URL", "")
BOOKING_LINK = os.environ.get("BOOKING_LINK", "")


def _compose_link_line():
    links = []
    if WEBINDEXER_SITE_URL:
        links.append(WEBINDEXER_SITE_URL)
    if WEBINDEXER_DEMO_URL:
        links.append(WEBINDEXER_DEMO_URL)
    if BOOKING_LINK:
        links.append(BOOKING_LINK)
    return " | ".join(links)


# ==== RESPONSE TEMPLATES (mirrors webindexer_main.py) ====
_LINKS = _compose_link_line()
_LINKS_SUFFIX = (" " + _LINKS) if _LINKS else ""

RESPONSE_TEMPLATES = {
    "direct_intent": f"""
Hey 👋 if you're exploring a website chatbot/live chat, we built WebIndexer — a site chatbot that answers FAQs, captures leads, qualifies prospects, and routes to your team. Happy to share a quick demo.{_LINKS_SUFFIX}
""",
    "support_focus": f"""
Hey 👋 sounds like you want to reduce support load and speed up responses. WebIndexer can deflect FAQs, do 24/7 answers, and hand off to humans when needed. Can send a quick demo if helpful.{_LINKS_SUFFIX}
""",
    "general": f"""
Hey 👋 we built WebIndexer — a no-fuss website chatbot for SMEs to capture more leads and automate support. If you want options or a demo, happy to help.{_LINKS_SUFFIX}
""",
}


def get_response_template(text_content):
    """Choose appropriate response template based on content."""
    text = (text_content or "").lower()
    direct_keywords = [
        'chatbot', 'live chat', 'chat widget', 'website chat', 'site chat', 'intercom',
        'drift', 'zendesk', 'gorgias', 'crisp', 'tidio', 'tawk.to', 'userlike', 'livechat', 'olark',
        'lead capture', 'qualify leads', 'book meetings', 'meeting booking', 'crm', 'hubspot'
    ]
    support_keywords = [
        'customer support', 'support tickets', 'faq', '24/7', 'response time',
        'reduce tickets', 'deflect', 'help desk', 'knowledge base'
    ]
    if any(k in text for k in direct_keywords):
        return RESPONSE_TEMPLATES["direct_intent"]
    if any(k in text for k in support_keywords):
        return RESPONSE_TEMPLATES["support_focus"]
    return RESPONSE_TEMPLATES["general"]


def generate_digest_email(leads, digest_date_str=None):
    """Generate HTML and text versions of the WebIndexer daily lead digest."""
    total_leads = len(leads)

    # Determine display date (defaults to now if not provided or invalid)
    try:
        display_date = datetime.strptime(digest_date_str, '%Y-%m-%d') if digest_date_str else datetime.now()
    except Exception:
        display_date = datetime.now()

    # Build lead cards HTML
    lead_cards_html = ""
    for idx, lead in enumerate(leads, 1):
        username = lead.get('author', 'Unknown')
        subreddit = lead.get('subreddit', 'Unknown')
        content_type = lead.get('content_type', 'unknown')
        similarity_score = float(lead.get('similarity_score', 0) or 0)
        best_topic = lead.get('best_matching_topic', 'N/A')
        reddit_score = lead.get('reddit_score', 0)
        timestamp = lead.get('timestamp', 'N/A')
        llm_verification = lead.get('llm_verification', 'N/A')
        product = lead.get('product', 'WebIndexer')

        # URLs
        reddit_profile_url = f"https://www.reddit.com/user/{username}"
        content_url = lead.get('permalink', '')

        # Content preview and recommended message
        if content_type == 'post':
            title = lead.get('title', 'N/A')
            body = lead.get('selftext', '')
            content_preview = f"""
                <p><strong>Title:</strong> {title}</p>
                <p><strong>Body:</strong> {body[:300]}{'...' if len(body) > 300 else ''}</p>
            """
            text_content = f"{title} {body}".lower()
            recommended_message = get_response_template(text_content)
        else:
            comment = lead.get('comment', '')
            content_preview = f"""
                <p><strong>Comment:</strong> {comment[:300]}{'...' if len(comment) > 300 else ''}</p>
            """
            text_content = comment.lower()
            recommended_message = get_response_template(text_content)

        lead_cards_html += f"""
        <div style="background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #1a73e8;">
            <h3 style="color: #1a73e8; margin-top: 0;">Lead #{idx} - u/{username} ({product})</h3>

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
                <a href="{reddit_profile_url}" style="display: inline-block; padding: 10px 20px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px; font-size: 14px;">
                    📧 DM User
                </a>
                <a href="{content_url}" style="display: inline-block; padding: 10px 20px; background-color: #0f9d58; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px; font-size: 14px;">
                    🔗 View Post
                </a>
            </div>
        </div>
        """

    # HTML wrapper
    html_content = f"""
<html>
<head></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5;">
    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #1a73e8; color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
            <h1 style="margin: 0; font-size: 32px;">📊 WebIndexer Daily Lead Digest</h1>
            <p style="margin: 10px 0 0 0; font-size: 18px;">Website Chatbot Leads</p>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{display_date.strftime('%A, %B %d, %Y')}</p>
        </div>

        <div style="background-color: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="background-color: #e8f4f8; padding: 20px; border-radius: 5px; text-align: center; margin-bottom: 30px;">
                <h2 style="color: #1a73e8; margin: 0; font-size: 48px;">{total_leads}</h2>
                <p style="color: #666; margin: 5px 0 0 0; font-size: 18px;">Total Leads</p>
            </div>

            {lead_cards_html if total_leads > 0 else '<p style="text-align: center; color: #666; font-size: 18px; padding: 40px 0;">No WebIndexer leads were collected.</p>'}
        </div>

        <div style="text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 14px;">
            <p>This is an automated daily digest from your WebIndexer lead monitoring bot.</p>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""

    # Plain text version
    text_content = f"""
WebIndexer Daily Lead Digest
{display_date.strftime('%A, %B %d, %Y')}

{'='*60}
SUMMARY
{'='*60}
Total Leads: {total_leads}

"""

    if total_leads > 0:
        for idx, lead in enumerate(leads, 1):
            username = lead.get('author', 'Unknown')
            subreddit = lead.get('subreddit', 'Unknown')
            content_type = lead.get('content_type', 'unknown')
            similarity_score = float(lead.get('similarity_score', 0) or 0)
            reddit_profile_url = f"https://www.reddit.com/user/{username}"
            content_url = lead.get('permalink', '')

            if content_type == 'post':
                title = lead.get('title', 'N/A')
                body = (lead.get('selftext', '') or '')[:200]
                content_text = f"Title: {title}\nBody: {body}"
            else:
                comment = (lead.get('comment', '') or '')[:200]
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
        text_content += "No WebIndexer leads were collected.\n"

    text_content += f"""
{'='*60}
Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}
"""

    return html_content, text_content


def send_digest_email(leads, date_str):
    """Send the WebIndexer daily digest email."""
    if not EMAIL_ADDRESS or not SMTP2GO_API_KEY:
        print("⚠️ SMTP2GO not configured: missing EMAIL_ADDRESS or SMTP2GO_API_KEY")
        return False

    try:
        html_content, text_content = generate_digest_email(leads, date_str)

        recipients = [r.strip() for r in NOTIFICATION_EMAIL.replace(';', ',').split(',') if r.strip()]
        try:
            nice_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y") if date_str else datetime.now().strftime("%B %d, %Y")
        except Exception:
            nice_date = date_str or datetime.now().strftime("%B %d, %Y")

        subject = f'WebIndexer Daily Lead Digest - {nice_date} ({len(leads)} leads)'

        payload = {
            "sender": EMAIL_ADDRESS,
            "to": recipients,
            "subject": subject,
            "text_body": text_content,
            "html_body": html_content,
            "custom_headers": [
                {"header": "Reply-To", "value": REPLY_TO}
            ],
        }

        headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
            "X-Smtp2go-Api-Key": SMTP2GO_API_KEY,
        }

        response = requests.post(SMTP2GO_API_URL, json=payload, headers=headers, timeout=20)

        ok = False
        if response.status_code == 200:
            try:
                resp_json = response.json()
                data_obj = resp_json.get("data") if isinstance(resp_json, dict) else None
                if isinstance(data_obj, dict) and isinstance(data_obj.get("succeeded"), int):
                    ok = data_obj.get("succeeded", 0) >= 1
            except Exception:
                ok = False

        if ok:
            print(f"✅ WebIndexer digest email sent to {', '.join(recipients)} ({len(leads)} leads)")
            return True
        else:
            print(f"⚠️ SMTP2GO send failed: status={response.status_code}, body={response.text}")
            return False

    except Exception as e:
        print(f"⚠️ Error sending WebIndexer digest: {e}")
        return False


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="WebIndexer Daily Lead Digest Sender")
    parser.add_argument("-d", "--date", help="Date to send digest for (YYYY-MM-DD)")
    return parser.parse_args()


def archive_leads_file(filename):
    """Move leads file to archive directory."""
    try:
        archive_dir = "email_archives"
        os.makedirs(archive_dir, exist_ok=True)
        archive_path = os.path.join(archive_dir, os.path.basename(filename))
        os.rename(filename, archive_path)
        print(f"📦 Archived {filename} to {archive_path}")
        return True
    except Exception as e:
        print(f"⚠️ Error archiving file: {e}")
        return False


def main():
    """Main function to send WebIndexer daily digest."""
    print("="*60)
    print("📧 WebIndexer Daily Lead Digest Sender")
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    args = parse_args()
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
            target_date = args.date
        except Exception:
            print(f"⚠️ Invalid date format for --date: {args.date}. Expected YYYY-MM-DD.")
            return
    else:
        target_date = datetime.now().strftime("%Y-%m-%d")

    leads_file = f"webindexer_leads_{target_date}.json"

    # If no file for the target date, optionally send any unsent older files
    if not os.path.exists(leads_file):
        if args.date:
            print(f"ℹ️ No WebIndexer leads file found for {target_date}")
            print("ℹ️ No leads to send for the specified date")
            return
        else:
            print(f"ℹ️ No WebIndexer leads file found for {target_date}")
            print("ℹ️ Checking for older WebIndexer lead files to send...")

            older_files = glob.glob("webindexer_leads_*.json")
            # Exclude today's (already missing); send oldest first for determinism
            older_files = sorted(older_files)
            if older_files:
                print(f"\n⚠️ Found {len(older_files)} older WebIndexer leads file(s):")
                for old_file in older_files:
                    print(f"   - {old_file}")
                    try:
                        with open(old_file, 'r', encoding='utf-8') as f:
                            old_leads = json.load(f)

                        old_date = old_file.replace('webindexer_leads_', '').replace('.json', '')

                        print(f"\n📧 Sending WebIndexer digest for {old_date} ({len(old_leads)} leads)...")
                        if send_digest_email(old_leads, old_date):
                            archive_leads_file(old_file)
                    except Exception as e:
                        print(f"⚠️ Error processing {old_file}: {e}")

            return

    try:
        with open(leads_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)

        print(f"📊 Found {len(leads)} WebIndexer lead(s) for {target_date}")

        if send_digest_email(leads, target_date):
            archive_leads_file(leads_file)
        else:
            print("⚠️ Failed to send WebIndexer digest. Leads file will be kept for retry.")

    except Exception as e:
        print(f"⚠️ Error: {e}")
        return

    print("\n✅ WebIndexer daily digest process completed")
    print("="*60)


if __name__ == "__main__":
    main()


