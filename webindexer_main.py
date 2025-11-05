import os
import praw
import time
import json
import gc
from datetime import datetime, timedelta
from dotenv import load_dotenv
import numpy as np
import cohere

# Load environment variables from .env file
load_dotenv()

# ==== GLOBAL COUNTERS ====
processed_count = 0
milestones = [10, 100, 1000]
next_milestone_index = 0

posts_processed = 0
comments_processed = 0
filtered_no_intent_keywords_count = 0
filtered_negative_keywords_count = 0
filtered_no_seeking_language_count = 0
filtered_low_similarity_count = 0
filtered_llm_failed_count = 0
leads_found_count = 0
replies_sent_count = 0
dms_sent_count = 0
errors_processing_count = 0
errors_responding_count = 0


def should_print_milestone(count):
    global next_milestone_index
    if next_milestone_index < len(milestones):
        if count >= milestones[next_milestone_index]:
            next_milestone_index += 1
            return True
    elif count >= 1000 and count % 10000 == 0:
        return True
    return False


def print_progress_summary(context_label):
    filtered_total = (
        filtered_no_intent_keywords_count
        + filtered_negative_keywords_count
        + filtered_no_seeking_language_count
        + filtered_low_similarity_count
        + filtered_llm_failed_count
    )
    print(
        f"\ud83d\udcc8 {context_label} | checked={processed_count} "
        f"(posts={posts_processed}, comments={comments_processed}) | "
        f"filtered={filtered_total} "
        f"(no_intent={filtered_no_intent_keywords_count}, "
        f"negative={filtered_negative_keywords_count}, "
        f"no_seek={filtered_no_seeking_language_count}, "
        f"low_sim={filtered_low_similarity_count}, "
        f"llm_fail={filtered_llm_failed_count}) | "
        f"leads={leads_found_count} | replies={replies_sent_count} | dms={dms_sent_count} | "
        f"errors(proc={errors_processing_count}, resp={errors_responding_count})"
    )


# ==== CONFIG ====
REDDIT_CLIENT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_CLIENT_SECRET = os.environ["REDDIT_CLIENT_SECRET"]
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "YOUR_USERNAME")
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "YOUR_PASSWORD")
USER_AGENT = os.environ.get("USER_AGENT", "WebIndexer Lead Bot v1.0")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "")

# Optional links
WEBINDEXER_SITE_URL = os.environ.get("WEBINDEXER_SITE_URL", "")
WEBINDEXER_DEMO_URL = os.environ.get("WEBINDEXER_DEMO_URL", "")
BOOKING_LINK = os.environ.get("BOOKING_LINK", "")

# Behavior flags
AUTO_RESPOND = False
SEND_DMS = False
RESPONSE_COOLDOWN_HOURS = 24

# Tracking
recent_interactions = {}
SAVE_FILTERED_CONTENT = False
identified_leads = {}
IDENTIFIED_LEADS_FILE = "identified_webindexer_leads.json"


# ==== INITIALIZE COHERE ====
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


# ==== TARGET SUBREDDITS (SMB/SME owners, ecom, SaaS, tools) ====
TARGET_SUBREDDITS = [
    "Entrepreneur", "smallbusiness", "business", "startups",
    "ecommerce", "shopify", "woocommerce",
    "marketing", "digital_marketing", "GrowthHacking",
    "webdev", "Wordpress", "web_design",
    "SaaS"
]


# ==== TOPICS FOR WEBSITE CHATBOTS / SUPPORT AUTOMATION INTENT ====
TARGET_TOPICS = [
    # Direct needs
    "I need a website chatbot",
    "looking for a live chat for my website",
    "how to add chat widget to website",
    "AI chatbot to answer customer questions",
    "24/7 customer support on website",
    "automate customer support responses",
    "reduce support tickets with a bot",
    "capture leads from website visitors",
    "increase website conversions with chat",
    "qualify leads on my website",
    "book meetings from website chat",
    "chatbot integrated with CRM",
    "FAQ bot for my site",
    "knowledge base chatbot",
    "intercom alternative",
    "drift alternative",
    "zendesk chat alternative",
    "tawk.to vs crisp vs tidio",
    "live chat for Shopify store",
    "support widget for ecommerce",
    "sales chatbot for SaaS",
]


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


# ==== FILTERING (EMBEDDINGS) ====
def is_relevant_item(text, threshold=0.5):
    try:
        response = cohere_client.embed(
            texts=[text],
            model='embed-english-v3.0',
            input_type='search_query'
        )
        text_embedding = np.array(response.embeddings)
        text_norm = text_embedding / np.linalg.norm(text_embedding, axis=1, keepdims=True)
        target_norm = target_embeddings / np.linalg.norm(target_embeddings, axis=1, keepdims=True)
        similarities = np.dot(text_norm, target_norm.T)[0]
        max_similarity = np.max(similarities)
        best_idx = int(np.argmax(similarities))
        return max_similarity > threshold, float(max_similarity), TARGET_TOPICS[best_idx]
    except Exception as e:
        print(f"⚠️ Error in embedding filtering: {e}")
        return False, 0.0, ""


# ==== LLM VERIFICATION ====
def verify_with_llm(text_content):
    if not cohere_client:
        return True, "LLM verification skipped (no API key)"
    try:
        prompt = f"""Analyze the following Reddit post or comment and determine if it's from a small/medium business owner, operator, or website owner who is actively seeking a WEBSITE chatbot/live chat solution to improve customer support, capture leads, qualify prospects, or book meetings.

Text: "{text_content}"

Criteria for YES:
- They want to add a chat/chatbot widget to a website or online store
- They ask for tools/vendors (e.g., Intercom, Drift, Zendesk, Crisp, Tidio, Tawk.to)
- They want to automate support, answer FAQs, or do 24/7 support
- They want to capture leads, improve conversions, or route to sales
- They mention Shopify/Shopify apps, WooCommerce, WordPress, SaaS product site

Criteria for NO:
- They discuss building bots/programming tutorials (not purchasing/using a tool)
- They talk about chat on Discord/Telegram only (not website chat)
- They are job-seeking, offering services, or promoting their own product
- They discuss academic research, theory, or general opinions (not seeking a solution)
- They only need translation or unrelated chat features

Answer with ONLY "YES" or "NO", followed by a brief one-sentence explanation.

Format: YES/NO - [reason]"""

        response = cohere_client.chat(
            message=prompt,
            model="command-a-03-2025",
            temperature=0.3,
            max_tokens=100
        )
        result_text = response.text.strip()
        is_verified = result_text.upper().startswith("YES")
        reasoning = result_text
        return is_verified, reasoning
    except Exception as e:
        print(f"⚠️ Error in LLM verification: {e}")
        return True, f"LLM verification error: {str(e)}"


# ==== RESPONSE TEMPLATES ====
def _compose_link_line():
    links = []
    if WEBINDEXER_SITE_URL:
        links.append(WEBINDEXER_SITE_URL)
    if WEBINDEXER_DEMO_URL:
        links.append(WEBINDEXER_DEMO_URL)
    if BOOKING_LINK:
        links.append(BOOKING_LINK)
    return " | ".join(links)


RESPONSE_TEMPLATES = {
    "direct_intent": f"""
Hey \ud83d\udc4b if you're exploring a website chatbot/live chat, we built WebIndexer — a site chatbot that answers FAQs, captures leads, qualifies prospects, and routes to your team. Happy to share a quick demo.{' ' + _compose_link_line() if _compose_link_line() else ''}
""",
    "support_focus": f"""
Hey \ud83d\udc4b sounds like you want to reduce support load and speed up responses. WebIndexer can deflect FAQs, do 24/7 answers, and hand off to humans when needed. Can send a quick demo if helpful.{' ' + _compose_link_line() if _compose_link_line() else ''}
""",
    "general": f"""
Hey \ud83d\udc4b we built WebIndexer — a no-fuss website chatbot for SMEs to capture more leads and automate support. If you want options or a demo, happy to help.{' ' + _compose_link_line() if _compose_link_line() else ''}
""",
}


def get_response_template(text_content):
    text = text_content.lower()
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


# ==== LEAD TRACKING ====
def load_identified_leads():
    global identified_leads
    try:
        if os.path.exists(IDENTIFIED_LEADS_FILE):
            with open(IDENTIFIED_LEADS_FILE, 'r', encoding='utf-8') as f:
                identified_leads = json.load(f)
            print(f"📂 Loaded {len(identified_leads)} previously identified WebIndexer leads")
        else:
            identified_leads = {}
            print("📂 No previous WebIndexer leads file found, starting fresh")
    except Exception as e:
        print(f"⚠️ Error loading identified leads: {e}")
        identified_leads = {}


def save_identified_leads():
    try:
        with open(IDENTIFIED_LEADS_FILE, 'w', encoding='utf-8') as f:
            json.dump(identified_leads, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error saving identified leads: {e}")


def is_already_identified_lead(username):
    return username in identified_leads


def record_identified_lead(username):
    identified_leads[username] = datetime.now().isoformat()
    save_identified_leads()


# ==== INTERACTION TRACKING ====
def can_interact_with_user(username):
    if username in recent_interactions:
        last = datetime.fromisoformat(recent_interactions[username])
        hours = (datetime.now() - last).total_seconds() / 3600
        return hours >= RESPONSE_COOLDOWN_HOURS
    return True


def record_interaction(username):
    recent_interactions[username] = datetime.now().isoformat()


# ==== MEMORY MANAGEMENT ====
def cleanup_memory():
    global recent_interactions
    while True:
        try:
            time.sleep(3600)
            print("🧹 Running memory cleanup...")
            cutoff = datetime.now() - timedelta(hours=RESPONSE_COOLDOWN_HOURS + 1)
            old_count = len(recent_interactions)
            recent_interactions = {
                u: ts for u, ts in recent_interactions.items()
                if datetime.fromisoformat(ts) > cutoff
            }
            cleaned = old_count - len(recent_interactions)
            gc.collect()
            print(f"✅ Memory cleanup complete. Removed {cleaned} old interactions. Current: {len(recent_interactions)}")
        except Exception as e:
            print(f"⚠️ Error during memory cleanup: {e}")


# ==== RESPOND ====
def respond_to_content(reddit_instance, content, content_type, text_content):
    try:
        global replies_sent_count, dms_sent_count, errors_responding_count
        username = str(content.author)
        if not can_interact_with_user(username):
            print(f"⏰ Skipping response to u/{username} (cooldown active)")
            return False

        response_text = get_response_template(text_content)

        if AUTO_RESPOND and content_type == 'post':
            content.reply(response_text)
            print(f"✅ Replied to post by u/{username}")
            record_interaction(username)
            replies_sent_count += 1
            return True
        elif AUTO_RESPOND and content_type == 'comment':
            content.reply(response_text)
            print(f"✅ Replied to comment by u/{username}")
            record_interaction(username)
            replies_sent_count += 1
            return True
        elif SEND_DMS:
            # reddit_instance.redditor(username).message(
            #     subject="Website Chatbot for Support & Sales",
            #     message=response_text
            # )
            print(f"📩 Sent DM to u/{username}")
            record_interaction(username)
            dms_sent_count += 1
            return True
    except Exception as e:
        print(f"⚠️ Error responding to u/{content.author}: {e}")
        errors_responding_count += 1
        return False
    return False


# ==== SAVE LEADS ====
def save_lead_to_json(lead_data):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"webindexer_leads_{today}.json"
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                leads = json.load(f)
        else:
            leads = []
        leads.append(lead_data)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
        print(f"💾 WebIndexer lead saved to {filename}")
    except Exception as e:
        print(f"⚠️ Error saving lead: {e}")


def save_filtered_content_to_json(filtered_data):
    if not SAVE_FILTERED_CONTENT:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"unfiltered_webindexer_leads_{today}.json"
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                filtered = json.load(f)
        else:
            filtered = []
        filtered.append(filtered_data)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, indent=2, ensure_ascii=False)
        print(f"💾 Filtered content saved to {filename}")
    except Exception as e:
        print(f"⚠️ Error saving filtered content: {e}")


# ==== LOAD IDENTIFIED LEADS ====
load_identified_leads()


# ==== SETUP REDDIT ====
reddit_read = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=USER_AGENT
)

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

print(f"🚀 Monitoring {len(TARGET_SUBREDDITS)} subreddits for WebIndexer SME leads...")
print(f"📍 Target subreddits: {', '.join(TARGET_SUBREDDITS)}")
print(f"🤖 Auto-respond: {'ON' if AUTO_RESPOND else 'OFF'}")
print(f"📩 Direct messages: {'ON' if SEND_DMS else 'OFF'}")


def process_content(content, content_type):
    global processed_count, posts_processed, comments_processed
    global filtered_no_intent_keywords_count, filtered_negative_keywords_count
    global filtered_no_seeking_language_count, filtered_low_similarity_count
    global filtered_llm_failed_count, leads_found_count, errors_processing_count

    processed_count += 1
    if content_type == 'post':
        posts_processed += 1
    else:
        comments_processed += 1

    if should_print_milestone(processed_count):
        print_progress_summary("Milestone")

    try:
        if content.author is None or content.author in ['AutoModerator']:
            return

        username = str(content.author)
        if is_already_identified_lead(username):
            print(f"⏭️ Skipping u/{username} - already identified as a lead")
            return

        if content_type == 'post':
            text_content = f"{content.title} {content.selftext}".lower()
            display_text = f"Title: {content.title}\nBody: {content.selftext[:200]}{'...' if len(content.selftext) > 200 else ''}"
        else:
            if getattr(content, 'body', '') in ['[deleted]', '[removed]']:
                return
            text_content = content.body.lower()
            display_text = content.body[:200] + ('...' if len(content.body) > 200 else '')

        # Embedding similarity (always compute)
        is_relevant, similarity_score, best_matching_topic = is_relevant_item(text_content)

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

        if content_type == 'post':
            base_data.update({
                'title': content.title,
                'selftext': content.selftext,
                'permalink': f"https://www.reddit.com{content.permalink}",
                'url': content.url if hasattr(content, 'url') else None
            })
        else:
            base_data.update({
                'comment': content.body,
                'permalink': f"https://www.reddit.com{content.permalink}"
            })

        # Intent keywords for website chatbot/live chat
        intent_keywords = [
            'chatbot', 'ai chatbot', 'live chat', 'chat widget', 'website chat', 'site chat',
            'customer support chat', 'support widget', 'faq bot', 'knowledge base chat',
            'lead capture', 'capture leads', 'qualify leads', 'qualification', 'book meetings',
            'meeting booking', 'routing to sales', 'crm integration', 'hubspot chat',
            'intercom', 'drift', 'zendesk', 'gorgias', 'crisp', 'tidio', 'tawk.to', 'olark', 'livechat',
            'shopify app', 'woocommerce plugin', 'wordpress plugin', 'reduce tickets', '24/7 support'
        ]

        has_intent_keywords = any(k in text_content for k in intent_keywords)
        if not has_intent_keywords:
            filtered_data = base_data.copy()
            filtered_data.update({
                'filter_reason': 'no_intent_keywords',
                'filter_description': 'Content does not contain website chatbot/live chat purchase intent keywords'
            })
            save_filtered_content_to_json(filtered_data)
            filtered_no_intent_keywords_count += 1
            return

        # Negative keywords to exclude unrelated contexts
        negative_keywords = [
            # Building/coding-only intent
            'how to code a chatbot', 'build my own chatbot', 'python chatbot', 'javascript chatbot',
            'nlp research', 'academic', 'homework', 'assignment',
            # Non-website chat contexts
            'discord bot', 'telegram bot', 'whatsapp bot', 'slack bot',
            # Non-buyer posts
            'hire me', 'for hire', 'job opening', 'looking for clients', 'portfolio'
        ]
        neg_matches = [n for n in negative_keywords if n in text_content]
        if neg_matches:
            print(f"🚫 Filtered out due to negative keywords: {display_text[:100]}...")
            filtered_data = base_data.copy()
            filtered_data.update({
                'filter_reason': 'negative_keywords',
                'filter_description': f'Content contains negative keywords: {", ".join(neg_matches)}'
            })
            save_filtered_content_to_json(filtered_data)
            filtered_negative_keywords_count += 1
            return

        # Seeking language (buying/recommendation intent)
        seeking_indicators = [
            'looking for', 'recommend', 'recommendations', 'which tool', 'what tool', 'best tool',
            'any tools', 'suggestions', 'advice on', 'how to add', 'how do i add', 'anyone using',
            'alternatives to', 'vs ', 'cost', 'pricing', 'vendor', 'provider'
        ]
        has_seeking_language = any(s in text_content for s in seeking_indicators)
        if not has_seeking_language:
            print(f"🚫 Filtered out - no seeking language: {display_text[:100]}...")
            filtered_data = base_data.copy()
            filtered_data.update({
                'filter_reason': 'no_seeking_language',
                'filter_description': 'Content does not contain buying/recommendation seeking language'
            })
            save_filtered_content_to_json(filtered_data)
            filtered_no_seeking_language_count += 1
            return

        # Embedding-based similarity gate
        if not is_relevant:
            print(f"🚫 Filtered out - low similarity score ({similarity_score:.2f}): {display_text[:100]}...")
            filtered_data = base_data.copy()
            filtered_data.update({
                'filter_reason': 'low_similarity',
                'filter_description': f'Similarity score ({similarity_score:.2f}) below threshold'
            })
            save_filtered_content_to_json(filtered_data)
            filtered_low_similarity_count += 1
            return

        # LLM verification
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
            filtered_llm_failed_count += 1
            return

        print(f"🔍 Found potential WebIndexer lead in {content_type}: {display_text}")
        print(f"   ✅ LLM Verified: {llm_reasoning}")

        record_identified_lead(username)

        lead_data = base_data.copy()
        lead_data.update({
            'responded': False,
            'dm_sent': False,
            'llm_verification': llm_reasoning,
            'product': 'WebIndexer'
        })

        print("\n===========================")
        print("🎯 WEBINDEXER LEAD FOUND!")
        print(f"📌 Content Type: {content_type.upper()}")
        print(f"📌 Subreddit: r/{content.subreddit.display_name}")
        print(f"👤 Author: u/{content.author}")
        if content_type == 'post':
            print(f"📝 Title: {getattr(content, 'title', '')}")
            print(f"💬 Body: {getattr(content, 'selftext', '')[:200]}{'...' if len(getattr(content, 'selftext', '')) > 200 else ''}")
        else:
            print(f"💬 Comment: {getattr(content, 'body', '')[:200]}{'...' if len(getattr(content, 'body', '')) > 200 else ''}")
        print(f"🔗 Link: https://www.reddit.com{content.permalink}")
        print(f"📊 Similarity Score: {similarity_score:.2f}")
        print(f"🎯 Best Matching Topic: {best_matching_topic}")
        print(f"📊 Reddit Score: {content.score}")
        print("===========================\n")

        leads_found_count += 1
        save_lead_to_json(lead_data)

        if (AUTO_RESPOND or SEND_DMS) and reddit_write:
            responded = respond_to_content(reddit_write, content, content_type, text_content)
            lead_data['responded'] = responded
            if responded:
                print("✅ Response sent!")
    except Exception as e:
        print(f"⚠️ Error processing {content_type}: {e}")
        errors_processing_count += 1


try:
    import threading
    import queue

    content_queue = queue.Queue()

    def monitor_posts():
        try:
            for post in subreddit.stream.submissions(skip_existing=True):
                content_queue.put(('post', post))
        except Exception as e:
            print(f"⚠️ Error monitoring posts: {e}")

    def monitor_comments():
        try:
            for comment in subreddit.stream.comments(skip_existing=True):
                content_queue.put(('comment', comment))
        except Exception as e:
            print(f"⚠️ Error monitoring comments: {e}")

    post_thread = threading.Thread(target=monitor_posts, daemon=True)
    comment_thread = threading.Thread(target=monitor_comments, daemon=True)
    cleanup_thread = threading.Thread(target=cleanup_memory, daemon=True)

    post_thread.start()
    comment_thread.start()
    cleanup_thread.start()

    print("🔄 Monitoring both posts and comments for WebIndexer leads...")
    print("🧹 Memory cleanup running in background (hourly)")
    print("💡 Tip: Set AUTO_RESPOND=True, SEND_DMS=True to automatically engage with leads")

    while True:
        try:
            content_type, content = content_queue.get(timeout=1)
            process_content(content, content_type)
            content_queue.task_done()
            if processed_count % 100 == 0:
                gc.collect()
                print_progress_summary("Every 100")
            time.sleep(2)
        except queue.Empty:
            continue
except KeyboardInterrupt:
    print("\n🛑 WebIndexer lead monitoring stopped by user.")
except Exception as e:
    print(f"⚠️ Error: {e}")


