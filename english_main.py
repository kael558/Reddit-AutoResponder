import os
import praw
import re
import time
import json
import gc
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
import numpy as np
import cohere

# Load environment variables from .env file
load_dotenv()

# ==== GLOBAL COUNTER ====
processed_count = 0
milestones = [10, 100, 1000]  # Base 10 exponential until 1000
next_milestone_index = 0

def should_print_milestone(count):
    """Check if we should print a milestone for the current count"""
    global next_milestone_index
    
    if next_milestone_index < len(milestones):
        if count >= milestones[next_milestone_index]:
            next_milestone_index += 1
            return True
    elif count >= 1000 and count % 1000 == 0:
        # Every 1000 after 1000
        return True
    return False

# ==== CONFIGURE YOUR CREDENTIALS HERE ====
REDDIT_CLIENT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_CLIENT_SECRET = os.environ["REDDIT_CLIENT_SECRET"]
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "YOUR_USERNAME")  # For responding/DMing
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "YOUR_PASSWORD")  # For responding/DMing
USER_AGENT = os.environ.get("USER_AGENT", "English Learning Community Bot v1.0")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "")  # For LLM verification

# ==== EMAIL CONFIGURATION (Namecheap Private Email) ====
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")  # Your Namecheap email
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")  # Your email password
EMAIL_SMTP_SERVER = "mail.privateemail.com"  # Namecheap Private Email SMTP
EMAIL_SMTP_PORT = 587  # STARTTLS port
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL", EMAIL_ADDRESS)  # Email to receive notifications

# Discord community details
DISCORD_INVITE_LINK = "https://discord.com/invite/yjaraMBuSG"  # Replace with your actual Discord invite
COMMUNITY_NAME = "Practice Speaking English - Fluent Future"

# ==== TARGET SUBREDDITS FOR ENGLISH LEARNERS ====
TARGET_SUBREDDITS = [
    "EnglishLearning", "LearningEnglish", "languagelearning", "language_exchange",
    "learningEnglishOnline", "LearnEnglishOnReddit", "Grammar", "TEFL"
]

# ==== AUTO-RESPONSE SETTINGS ====
AUTO_RESPOND = False  # Set to True to enable auto-responding
SEND_DMS = False     # Set to True to enable direct messaging
SEND_EMAILS = True   # Set to True to enable email notifications for leads
RESPONSE_COOLDOWN_HOURS = 24  # Hours to wait before responding to same user again

# Track recent interactions to avoid spam
recent_interactions = {}

SAVE_FILTERED_CONTENT = False  # Set to True to save filtered content to json

# Track users who have already been identified as leads
identified_leads = {}  # {username: first_identified_timestamp}
IDENTIFIED_LEADS_FILE = "identified_leads.json"

# ==== INITIALIZE COHERE CLIENT ====
cohere_client = None
if COHERE_API_KEY:
    try:
        cohere_client = cohere.Client(COHERE_API_KEY)
        print("✅ Cohere client initialized for embeddings and LLM verification")
    except Exception as e:
        print(f"⚠️ Could not initialize Cohere client: {e}")
        print("⚠️ Cannot proceed without Cohere API - embeddings and LLM verification required")
        exit(1)
else:
    print("⚠️ No COHERE_API_KEY found - Cohere is required for this bot")
    exit(1)

# ==== TARGET TOPICS FOR ENGLISH LEARNERS SEEKING PRACTICE ====
TARGET_TOPICS = [
    # Direct practice requests
    "I need speaking practice",
    "I want to practice speaking English",
    "I'm looking for conversation partner",
    "I need someone to talk to in English",
    "looking for English speaking partner",
    "need English conversation practice",
    "want to practice English conversation",
    "seeking English practice partner",
    "looking for language exchange partner",
    "need English speaking buddy",
    
    # Practice-seeking questions
    "how can I practice speaking English",
    "where can I practice English speaking",
    "how to practice English conversation",
    "where to find English practice partner",
    "how to improve English speaking",
    "where can I practice English",
    "how do I practice speaking",
    "best way to practice English speaking",
    "apps for English speaking practice",
    "websites for English practice",
    
    # Community seeking for practice
    "looking for English learning community",
    "need English study group",
    "want to join English practice group",
    "looking for English discord server",
    "English learning discord",
    "online English practice community",
    "English conversation group",
    "voice chat for English practice",
    "English speaking club online",
    "study buddy for English",
    
    # Confidence and fear about speaking
    "afraid to speak English",
    "nervous about speaking English",
    "scared to practice English speaking",
    "lack confidence in English speaking",
    "too shy to speak English",
    "embarrassed about my English",
    "anxious about English conversation",
    "need confidence in English",
    
    # Specific practice needs
    "practice English pronunciation",
    "improve my English accent",
    "practice business English speaking",
    "conversational English practice",
    "casual English conversation practice",
    "IELTS speaking practice partner",
    "TOEFL speaking practice",
    "English job interview practice"
]

# Pre-compute embeddings for target topics using Cohere
print("🔄 Computing target topic embeddings using Cohere...")
try:
    response = cohere_client.embed(
        texts=TARGET_TOPICS,
        model='embed-english-v3.0',
        input_type='search_document'
    )
    target_embeddings = np.array(response.embeddings)
    print(f"✅ Computed {len(target_embeddings)} target topic embeddings")
except Exception as e:
    print(f"⚠️ Error computing embeddings: {e}")
    exit(1)

# ==== FILTERING FUNCTION ====
def is_relevant_comment(comment_text, threshold=0.5):
    """
    Use embedding similarity to determine if a comment is relevant to English learners
    Returns: (is_relevant: bool, similarity_score: float, best_matching_topic: str)
    """
    try:
        # Get embedding from Cohere
        response = cohere_client.embed(
            texts=[comment_text],
            model='embed-english-v3.0',
            input_type='search_query'
        )
        comment_embedding = np.array(response.embeddings)
        
        # Calculate cosine similarity
        # Normalize vectors
        comment_norm = comment_embedding / np.linalg.norm(comment_embedding, axis=1, keepdims=True)
        target_norm = target_embeddings / np.linalg.norm(target_embeddings, axis=1, keepdims=True)
        
        # Compute similarities
        similarities = np.dot(comment_norm, target_norm.T)[0]
        max_similarity = np.max(similarities)
        best_topic_index = np.argmax(similarities)
        best_matching_topic = TARGET_TOPICS[best_topic_index]
        
        return max_similarity > threshold, float(max_similarity), best_matching_topic
    except Exception as e:
        print(f"⚠️ Error in embedding filtering: {e}")
        return False, 0.0, ""

def verify_with_llm(text_content):
    """
    Use Cohere LLM to verify if the content is genuinely about someone looking to practice English
    Returns: (is_verified: bool, reasoning: str)
    """
    if not cohere_client:
        # If Cohere is not available, skip this check
        return True, "LLM verification skipped (no API key)"
    
    try:
        prompt = f"""Analyze the following Reddit post or comment and determine if it's from someone who is actively looking to improve their English or practice speaking English or seeking English conversation practice.

Text: "{text_content}"

Criteria for YES:
- The person is explicitly looking for a conversation partner, speaking practice, or language exchange
- They are asking where/how to find English speaking practice
- They want to join a community or group for practicing English
- They are seeking help with improving their spoken/conversational English
- They express a need or desire to practice speaking with others
- They are seeking English practice partners

Criteria for NO:
- They are giving advice or recommendations (not seeking)
- They are discussing language theory or grammar rules
- They are asking for translation or writing help only
- They are promoting a service or product
- They are engaged in general debate or opinion-sharing
- They are only asking about reading or writing (not speaking/conversation)

Answer with ONLY "YES" or "NO", followed by a brief one-sentence explanation.

Format: YES/NO - [reason]"""

        response = cohere_client.chat(
            message=prompt,
            model="command-a-03-2025",
            temperature=0.3,
            max_tokens=100
        )
        
        result_text = response.text.strip()
        
        # Parse the response
        is_verified = result_text.upper().startswith("YES")
        reasoning = result_text
        
        return is_verified, reasoning
        
    except Exception as e:
        print(f"⚠️ Error in LLM verification: {e}")
        # On error, allow the content through (fail open)
        return True, f"LLM verification error: {str(e)}"

# ==== RESPONSE TEMPLATES ====
RESPONSE_TEMPLATES = {
    "speaking_practice": f"""
Hey 👋 saw your post about practicing spoken English! We're building an app to do exactly that and we'd love for you to join our friendly discord community to help each other: {DISCORD_INVITE_LINK}
""",
    
    "learning_support": f"""
Hey 👋 saw your post about English learning! I'm in the same boat and we're building a community to help each other out. Would love for you to join our discord: {DISCORD_INVITE_LINK}
""",
    
    "general_invite": f"""
Hey 👋 saw your post! We're building a friendly English learning community on discord where we practice and help each other. Would love for you to join us: {DISCORD_INVITE_LINK}
"""
}

def get_response_template(text_content):
    """Choose appropriate response template based on content"""
    speaking_keywords = ['speaking', 'conversation', 'talk', 'practice speaking', 'oral', 'pronunciation']
    support_keywords = ['struggling', 'difficult', 'hard', 'frustrated', 'give up', 'stuck', 'plateau']
    
    if any(keyword in text_content.lower() for keyword in speaking_keywords):
        return RESPONSE_TEMPLATES["speaking_practice"]
    elif any(keyword in text_content.lower() for keyword in support_keywords):
        return RESPONSE_TEMPLATES["learning_support"]
    else:
        return RESPONSE_TEMPLATES["general_invite"]

# ==== LEAD TRACKING ====
def load_identified_leads():
    """Load identified leads from JSON file"""
    global identified_leads
    try:
        if os.path.exists(IDENTIFIED_LEADS_FILE):
            with open(IDENTIFIED_LEADS_FILE, 'r', encoding='utf-8') as f:
                identified_leads = json.load(f)
            print(f"📂 Loaded {len(identified_leads)} previously identified leads")
        else:
            identified_leads = {}
            print("📂 No previous leads file found, starting fresh")
    except Exception as e:
        print(f"⚠️ Error loading identified leads: {e}")
        identified_leads = {}

def save_identified_leads():
    """Save identified leads to JSON file"""
    try:
        with open(IDENTIFIED_LEADS_FILE, 'w', encoding='utf-8') as f:
            json.dump(identified_leads, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error saving identified leads: {e}")

def is_already_identified_lead(username):
    """Check if user has already been identified as a lead"""
    return username in identified_leads

def record_identified_lead(username):
    """Record that a user has been identified as a lead"""
    identified_leads[username] = datetime.now().isoformat()
    save_identified_leads()

# ==== INTERACTION TRACKING ====
def can_interact_with_user(username):
    """Check if we can interact with a user (respecting cooldown)"""
    if username in recent_interactions:
        last_interaction = datetime.fromisoformat(recent_interactions[username])
        hours_passed = (datetime.now() - last_interaction).total_seconds() / 3600
        return hours_passed >= RESPONSE_COOLDOWN_HOURS
    return True

def record_interaction(username):
    """Record interaction with user"""
    recent_interactions[username] = datetime.now().isoformat()

# ==== MEMORY MANAGEMENT ====
def cleanup_memory():
    """Periodically clean up memory to prevent issues on droplet"""
    global recent_interactions
    
    while True:
        try:
            # Sleep for 1 hour between cleanups
            time.sleep(3600)
            
            print("🧹 Running memory cleanup...")
            
            # Clean up old interactions (older than cooldown period + 1 hour buffer)
            cutoff_time = datetime.now() - timedelta(hours=RESPONSE_COOLDOWN_HOURS + 1)
            old_count = len(recent_interactions)
            
            recent_interactions = {
                username: timestamp 
                for username, timestamp in recent_interactions.items()
                if datetime.fromisoformat(timestamp) > cutoff_time
            }
            
            cleaned_count = old_count - len(recent_interactions)
            
            # Force garbage collection
            gc.collect()
            
            print(f"✅ Memory cleanup complete. Removed {cleaned_count} old interactions. "
                  f"Current interactions in memory: {len(recent_interactions)}")
            
        except Exception as e:
            print(f"⚠️ Error during memory cleanup: {e}")

# ==== EMAIL NOTIFICATION FUNCTION ====
def send_email_notification(lead_data, content, content_type, text_content):
    """Send email notification about a new lead"""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("⚠️ Email credentials not configured")
        return False
    
    try:
        username = str(content.author)
        subreddit_name = content.subreddit.display_name
        
        # Get the recommended response template
        recommended_message = get_response_template(text_content)
        
        # Create Reddit profile link
        reddit_profile_url = f"https://www.reddit.com/user/{username}"
        
        # Create permalink to content
        content_url = f"https://www.reddit.com{content.permalink}"
        
        # Build email content
        if content_type == 'post':
            content_preview = f"""
<strong>Title:</strong> {content.title}<br>
<strong>Body:</strong> {content.selftext[:500]}{'...' if len(content.selftext) > 500 else ''}
"""
        else:  # comment
            content_preview = f"""
<strong>Comment:</strong> {content.body[:500]}{'...' if len(content.body) > 500 else ''}
"""
        
        # Create HTML email
        html_content = f"""
<html>
<head></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
        <h2 style="color: #ff4500; border-bottom: 2px solid #ff4500; padding-bottom: 10px;">
            🎯 New Reddit Lead - Fluent Future
        </h2>
        
        <div style="background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="color: #1a73e8; margin-top: 0;">Lead Information</h3>
            <p><strong>Username:</strong> u/{username}</p>
            <p><strong>Subreddit:</strong> r/{subreddit_name}</p>
            <p><strong>Content Type:</strong> {content_type.upper()}</p>
            <p><strong>Reddit Score:</strong> {content.score}</p>
            <p><strong>Similarity Score:</strong> {lead_data.get('similarity_score', 0):.2f}</p>
            <p><strong>Matching Topic:</strong> {lead_data.get('best_matching_topic', 'N/A')}</p>
        </div>
        
        <div style="background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="color: #1a73e8; margin-top: 0;">Content Preview</h3>
            {content_preview}
        </div>
        
        <div style="background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="color: #1a73e8; margin-top: 0;">Recommended Message</h3>
            <p style="background-color: #f0f0f0; padding: 15px; border-left: 4px solid #ff4500; white-space: pre-wrap;">{recommended_message}</p>
        </div>
        
        <div style="margin: 30px 0; text-align: center;">
            <a href="{reddit_profile_url}" style="display: inline-block; padding: 12px 30px; background-color: #ff4500; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px;">
                📧 DM User on Reddit
            </a>
            <a href="{content_url}" style="display: inline-block; padding: 12px 30px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px;">
                🔗 View Original Post
            </a>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
            <p><strong>LLM Verification:</strong> {lead_data.get('llm_verification', 'N/A')}</p>
            <p><strong>Timestamp:</strong> {lead_data.get('timestamp', 'N/A')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Create plain text version as fallback
        text_content_email = f"""
New Reddit Lead - Fluent Future

=== LEAD INFORMATION ===
Username: u/{username}
Subreddit: r/{subreddit_name}
Content Type: {content_type.upper()}
Reddit Score: {content.score}
Similarity Score: {lead_data.get('similarity_score', 0):.2f}
Matching Topic: {lead_data.get('best_matching_topic', 'N/A')}

=== CONTENT PREVIEW ===
{'Title: ' + content.title if content_type == 'post' else ''}
{'Body: ' + content.selftext[:500] if content_type == 'post' else 'Comment: ' + content.body[:500]}

=== RECOMMENDED MESSAGE ===
{recommended_message}

=== LINKS ===
DM User: {reddit_profile_url}
View Content: {content_url}

=== ADDITIONAL INFO ===
LLM Verification: {lead_data.get('llm_verification', 'N/A')}
Timestamp: {lead_data.get('timestamp', 'N/A')}
"""
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'New Reddit Lead - Fluent Future'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = NOTIFICATION_EMAIL
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content_email, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Connect to SMTP server and send
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"📧 Email notification sent to {NOTIFICATION_EMAIL}")
        return True
        
    except Exception as e:
        print(f"⚠️ Error sending email notification: {e}")
        return False

# ==== RESPONSE FUNCTIONS ====
def respond_to_content(reddit_instance, content, content_type, text_content):
    """Respond to relevant content (comment or DM)"""
    try:
        username = str(content.author)
        
        if not can_interact_with_user(username):
            print(f"⏰ Skipping response to u/{username} (cooldown active)")
            return False
            
        response_text = get_response_template(text_content)
        
        if AUTO_RESPOND and content_type == 'post':
            # Reply to post
            content.reply(response_text)
            print(f"✅ Replied to post by u/{username}")
            record_interaction(username)
            return True
            
        elif AUTO_RESPOND and content_type == 'comment':
            # Reply to comment
            content.reply(response_text)
            print(f"✅ Replied to comment by u/{username}")
            record_interaction(username)
            return True
            
        elif SEND_DMS:
            # Send direct message
            """reddit_instance.redditor(username).message(
                subject=f"English Learning Community Invitation",
                message=response_text
            )"""
            print(f"📩 Sent DM to u/{username}")
            record_interaction(username)
            return True
            
    except Exception as e:
        print(f"⚠️ Error responding to u/{content.author}: {e}")
        return False
    
    return False

# ==== SAVE LEADS TO JSON ====
def save_lead_to_json(lead_data):
    """
    Save lead data to a daily JSON file
    """
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"english_leads_{today}.json"
    
    try:
        # Load existing data or create new list
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                leads = json.load(f)
        else:
            leads = []
        
        # Add new lead
        leads.append(lead_data)
        
        # Save back to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
        
        print(f"💾 English lead saved to {filename}")
        
    except Exception as e:
        print(f"⚠️ Error saving lead: {e}")

def save_filtered_content_to_json(filtered_data):
    """
    Save filtered content data to a daily JSON file
    """'
    if not SAVE_FILTERED_CONTENT:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"unfiltered_english_leads_{today}.json"
    
    try:
        # Load existing data or create new list
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                filtered_leads = json.load(f)
        else:
            filtered_leads = []
        
        # Add new filtered content
        filtered_leads.append(filtered_data)
        
        # Save back to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(filtered_leads, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Filtered content saved to {filename}")
        
    except Exception as e:
        print(f"⚠️ Error saving filtered content: {e}")

# ==== LOAD IDENTIFIED LEADS ====
load_identified_leads()

# ==== SETUP REDDIT INSTANCE ====
# For read-only monitoring
reddit_read = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=USER_AGENT
)

# For responding/DMing (requires username/password)
reddit_write = None
if (AUTO_RESPOND or SEND_DMS) and REDDIT_USERNAME != "YOUR_USERNAME":
    try:
        reddit_write = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
            user_agent=USER_AGENT
        )
        print("✅ Authenticated for responding/DMing")
    except Exception as e:
        print(f"⚠️ Could not authenticate for responses: {e}")
        AUTO_RESPOND = False
        SEND_DMS = False

# ==== MONITOR MULTIPLE SUBREDDITS ====
subreddit_string = "+".join(TARGET_SUBREDDITS)
subreddit = reddit_read.subreddit(subreddit_string)

print(f"🚀 Monitoring {len(TARGET_SUBREDDITS)} subreddits for English learning leads...")
print(f"📍 Target subreddits: {', '.join(TARGET_SUBREDDITS)}")
print(f"🤖 Auto-respond: {'ON' if AUTO_RESPOND else 'OFF'}")
print(f"📩 Direct messages: {'ON' if SEND_DMS else 'OFF'}")
print(f"📧 Email notifications: {'ON' if SEND_EMAILS else 'OFF'}")

def process_content(content, content_type):
    """
    Process either a post or comment and check if it's a relevant English learning lead
    """
    global processed_count
    processed_count += 1

    if should_print_milestone(processed_count):
        print(f"Processed {processed_count} items...")

    try:
        # Skip deleted/removed content
        if content.author is None or content.author in ['AutoModerator']:
            return
        
        # Check if user has already been identified as a lead
        username = str(content.author)
        if is_already_identified_lead(username):
            print(f"⏭️ Skipping u/{username} - already identified as a lead")
            return
        
        # Get text content based on type
        if content_type == 'post':
            text_content = f"{content.title} {content.selftext}".lower()
            display_text = f"Title: {content.title}\nBody: {content.selftext[:200]}{'...' if len(content.selftext) > 200 else ''}"
        else:  # comment
            if content.body in ['[deleted]', '[removed]']:
                return
            text_content = content.body.lower()
            display_text = content.body[:200] + ('...' if len(content.body) > 200 else '')
        
        # Always get similarity score for all content
        is_relevant, similarity_score, best_matching_topic = is_relevant_comment(text_content)
        
        # Prepare base data for both filtered and unfiltered content
        base_data = {
            'timestamp': datetime.now().isoformat(),
            'content_type': content_type,
            'subreddit': content.subreddit.display_name,
            'author': str(content.author),
            'similarity_score': similarity_score,
            'best_matching_topic': best_matching_topic,
            'reddit_score': content.score,
            'created_utc': content.created_utc
        }
        
        # Add content-specific data
        if content_type == 'post':
            base_data.update({
                'title': content.title,
                'selftext': content.selftext,
                'permalink': f"https://www.reddit.com{content.permalink}",
                'url': content.url if hasattr(content, 'url') else None
            })
        else:  # comment
            base_data.update({
                'comment': content.body,
                'permalink': f"https://www.reddit.com{content.permalink}"
            })
        
        # First pass: Basic keyword filtering - ONLY for people seeking practice
        practice_seeking_keywords = [
            # Direct practice requests (first person)
            'i need', 'i want', 'i am looking', 'i\'m looking', 'looking for', 'need someone',
            'seeking', 'searching for', 'trying to find', 'anyone want to', 'anyone know',
            
            # Practice-specific terms
            'practice speaking', 'speaking practice', 'conversation practice', 'practice english',
            'practice partner', 'conversation partner', 'speaking partner', 'language exchange',
            'study buddy', 'speaking buddy', 'practice with', 'talk with', 'chat with',
            
            # Community seeking
            'discord server', 'discord group', 'english discord', 'practice group', 'study group',
            'english community', 'speaking club', 'conversation group', 'voice chat',
            
            # Questions about practice
            'how can i practice', 'where can i practice', 'how to practice', 'best way to practice',
            'apps for practice', 'websites for practice', 'where to practice', 'how do i practice',
            
            # Confidence/fear related to speaking
            'afraid to speak', 'scared to speak', 'nervous about speaking', 'shy to speak',
            'confidence in speaking', 'embarrassed about', 'anxious about speaking'
        ]
        
        has_practice_keywords = any(keyword in text_content for keyword in practice_seeking_keywords)
        
        if not has_practice_keywords:
            # Save to filtered content
            filtered_data = base_data.copy()
            filtered_data.update({
                'filter_reason': 'no_practice_keywords',
                'filter_description': 'Content does not contain practice-seeking keywords'
            })
            save_filtered_content_to_json(filtered_data)
            return
        
        # Negative keyword filtering - exclude irrelevant content
        negative_keywords = [
            # Commercial/spam
            'translate', 'translation service', 'homework help', 'essay writing service',
            'pay for', 'selling', 'buy my', 'crypto', 'bitcoin', 'investment',
            'spam', 'advertisement', 'promotion', 'affiliate', 'referral code',
            
            # General discussion/debate (not seeking practice)
            'totally representative', 'isolated case', 'asshole', 'population',
            'heard something recently', 'generally due to', 'step back', 'forest for the trees',
            'in my opinion', 'i think that', 'personally i believe', 'from my experience',
            'it depends on', 'there are many factors', 'it varies', 
            
            # Academic/theoretical discussions
            'research shows', 'studies indicate', 'according to', 'evidence suggests',
            'linguistically speaking', 'from a linguistic perspective', 'grammar rules',
            'language acquisition theory', 'second language acquisition',
            
            # Giving advice (not seeking)
            'you should', 'i recommend', 'try this', 'what works for me',
            'in my experience', 'i suggest', 'my advice would be'
        ]
        
        matching_negative_keywords = [neg_keyword for neg_keyword in negative_keywords if neg_keyword in text_content]
        if matching_negative_keywords:
            print(f"🚫 Filtered out due to negative keywords: {display_text[:100]}...")
            filtered_data = base_data.copy()
            filtered_data.update({
                'filter_reason': 'negative_keywords',
                'filter_description': f'Content contains negative keywords: {", ".join(matching_negative_keywords)}'
            })
            save_filtered_content_to_json(filtered_data)
            return
        
        # Additional check: Must contain seeking/question language for first person
        seeking_indicators = [
            'i need', 'i want', 'i am looking', 'i\'m looking', 'looking for',
            'how can i', 'where can i', 'how do i', 'where do i', 'help me',
            'anyone know', 'does anyone', 'can someone', 'recommendations for',
            'suggestions for', 'advice on', 'tips for'
        ]
        
        has_seeking_language = any(indicator in text_content for indicator in seeking_indicators)
        
        if not has_seeking_language:
            print(f"🚫 Filtered out - no seeking language: {display_text[:100]}...")
            filtered_data = base_data.copy()
            filtered_data.update({
                'filter_reason': 'no_seeking_language',
                'filter_description': 'Content does not contain seeking/question language indicators'
            })
            save_filtered_content_to_json(filtered_data)
            return
        
        # Embedding-based filtering
        if not is_relevant:
            print(f"🚫 Filtered out - low similarity score ({similarity_score:.2f}): {display_text[:100]}...")
            filtered_data = base_data.copy()
            filtered_data.update({
                'filter_reason': 'low_similarity',
                'filter_description': f'Similarity score ({similarity_score:.2f}) below threshold'
            })
            save_filtered_content_to_json(filtered_data)
            return
        
        # Final LLM verification using Cohere
        llm_verified, llm_reasoning = verify_with_llm(text_content)
        
        if not llm_verified:
            print(f"🚫 Filtered out - LLM verification failed: {display_text[:100]}...")
            print(f"   LLM Reasoning: {llm_reasoning}")
            filtered_data = base_data.copy()
            filtered_data.update({
                'filter_reason': 'llm_verification_failed',
                'filter_description': f'LLM verification: {llm_reasoning}'
            })
            save_filtered_content_to_json(filtered_data)
            return
        
        print(f"🔍 Found potential English learning lead in {content_type}: {display_text}")
        print(f"   ✅ LLM Verified: {llm_reasoning}")

        # Content passed all filters - it's a valid lead
        # Record this user as an identified lead to prevent duplicates
        record_identified_lead(username)
        
        lead_data = base_data.copy()
        lead_data.update({
            'responded': False,
            'dm_sent': False,
            'email_sent': False,
            'llm_verification': llm_reasoning
        })
        
        # Display the lead
        print("\n===========================")
        print(f"🎯 ENGLISH LEARNING LEAD FOUND!")
        print(f"📌 Content Type: {content_type.upper()}")
        print(f"📌 Subreddit: r/{content.subreddit.display_name}")
        print(f"👤 Author: u/{content.author}")
        if content_type == 'post':
            print(f"📝 Title: {content.title}")
            print(f"💬 Body: {content.selftext[:200]}{'...' if len(content.selftext) > 200 else ''}")
        else:
            print(f"💬 Comment: {content.body[:200]}{'...' if len(content.body) > 200 else ''}")
        print(f"🔗 Link: https://www.reddit.com{content.permalink}")
        print(f"📊 Similarity Score: {similarity_score:.2f}")
        print(f"🎯 Best Matching Topic: {best_matching_topic}")
        print(f"📊 Reddit Score: {content.score}")
        
        # Send email notification if enabled
        if SEND_EMAILS:
            email_sent = send_email_notification(lead_data, content, content_type, text_content)
            lead_data['email_sent'] = email_sent
            if email_sent:
                print("✅ Email notification sent!")
        
        # Try to respond if enabled
        if (AUTO_RESPOND or SEND_DMS) and reddit_write:
            responded = respond_to_content(reddit_write, content, content_type, text_content)
            lead_data['responded'] = responded
            if responded:
                print("✅ Response sent!")
        
        print("===========================\n")
        
        # Save to JSON
        save_lead_to_json(lead_data)
        
    except Exception as e:
        print(f"⚠️ Error processing {content_type}: {e}")

try:
    import threading
    import queue
    
    # Create a queue for processing content
    content_queue = queue.Queue()
    
    def monitor_posts():
        """Monitor new posts"""
        try:
            for post in subreddit.stream.submissions(skip_existing=True):
                content_queue.put(('post', post))
        except Exception as e:
            print(f"⚠️ Error monitoring posts: {e}")
    
    def monitor_comments():
        """Monitor new comments"""
        try:
            for comment in subreddit.stream.comments(skip_existing=True):
                content_queue.put(('comment', comment))
        except Exception as e:
            print(f"⚠️ Error monitoring comments: {e}")
    
    # Start monitoring threads
    post_thread = threading.Thread(target=monitor_posts, daemon=True)
    comment_thread = threading.Thread(target=monitor_comments, daemon=True)
    
    # Start memory cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_memory, daemon=True)
    
    post_thread.start()
    comment_thread.start()
    cleanup_thread.start()
    
    print("🔄 Monitoring both posts and comments for English learning leads...")
    print("🧹 Memory cleanup running in background (hourly)")
    print("💡 Tip: Set AUTO_RESPOND=True, SEND_DMS=True, or SEND_EMAILS=True to automatically engage with leads")
    
    # Process content from queue
    while True:
        try:
            content_type, content = content_queue.get(timeout=1)
            process_content(content, content_type)
            content_queue.task_done()
            
            # Periodic garbage collection every 100 items
            if processed_count % 100 == 0:
                gc.collect()
            
            time.sleep(2)  # Rate limiting (slightly slower for politeness)
        except queue.Empty:
            continue

except KeyboardInterrupt:
    print("\n🛑 English learning lead monitoring stopped by user.")
except Exception as e:
    print(f"⚠️ Error: {e}")