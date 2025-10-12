import os
import praw
import re
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

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
REDDIT_USERNAME = 'YOUR_USERNAME'
REDDIT_PASSWORD = 'YOUR_PASSWORD'
USER_AGENT = os.environ.get("USER_AGENT", "Reddit Chatbot Monitor v1.0")

# ==== TARGET SUBREDDITS FOR WEB DEVELOPERS & SMALL BUSINESS OWNERS ====
TARGET_SUBREDDITS = [
    "webdev", "javascript", "reactjs", "Frontend", "webdevelopment", 
    "coding", "programming", "smallbusiness", "entrepreneur", "startups", 
    "business", "marketing", "freelance", "solopreneur", "digitalnomad", "ProgrammerHumor", "technology", "artificial", "ArtificialIntelligence", "web_design", "freelance", "freelance_forhire", "webdevelopment"
]

# ==== LOAD LOCAL EMBEDDING MODEL ====
print("🔄 Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# ==== TARGET TOPICS FOR FILTERING ====
TARGET_TOPICS = [
    # Web Developer Whitelabeling Opportunities
    "looking for tools to offer clients",
    "need services to add value for clients",
    "white label solutions for web developers",
    "reseller programs for web developers",
    "additional services for web development clients",
    "how to increase web development revenue",
    "upsell services for web development",
    "client wants chatbot for website",
    "customer asking for AI chatbot",
    "need chatbot integration for client",
    "web development agency looking for solutions",
    "freelance web developer additional services",
    "partner program for web developers",
    
    # Business Conversion & AI Chatbot Needs
    "improve website conversion rate",
    "increase website conversions",
    "low website conversion rate",
    "website conversion optimization",
    "boost website sales",
    "website not converting visitors",
    "need better customer engagement",
    "website visitors not buying",
    "improve customer support on website",
    "automate customer service",
    "reduce customer support workload",
    "AI chatbot for website",
    "chatbot for customer support",
    "automated customer service solution",
    "need live chat for website",
    "website needs better user experience",
    "qualify leads automatically",
    "capture more leads from website",
    "24/7 customer support solution",
    "reduce customer support costs",
    "improve response time to customers",
    "need AI assistant for website",
    "website engagement too low",
    "visitors leaving website without buying",
    "need help with customer inquiries",
    "overwhelmed with customer questions",
    "need automated lead qualification",
    "improve website user experience",
    "website needs interactive features"
]

# Pre-compute embeddings for target topics
print("🔄 Computing target topic embeddings...")
target_embeddings = model.encode(TARGET_TOPICS)

# ==== FILTERING FUNCTION ====
def is_relevant_comment(comment_text, threshold=0.4):
    """
    Use embedding similarity to determine if a comment is relevant to our target audience
    Returns: (is_relevant: bool, similarity_score: float)
    """
    try:
        comment_embedding = model.encode([comment_text])
        similarities = cosine_similarity(comment_embedding, target_embeddings)[0]
        max_similarity = np.max(similarities)
        return max_similarity > threshold, float(max_similarity)
    except Exception as e:
        print(f"⚠️ Error in embedding filtering: {e}")
        return False, 0.0

# ==== SAVE LEADS TO JSON ====
def save_lead_to_json(comment_data):
    """
    Save lead data to a daily JSON file
    """
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"leads_{today}.json"
    
    try:
        # Load existing data or create new list
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                leads = json.load(f)
        else:
            leads = []
        
        # Add new lead
        leads.append(comment_data)
        
        # Save back to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Lead saved to {filename}")
        
    except Exception as e:
        print(f"⚠️ Error saving lead: {e}")

# ==== SETUP REDDIT INSTANCE ====
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=USER_AGENT
)

# ==== MONITOR MULTIPLE SUBREDDITS ====
subreddit_string = "+".join(TARGET_SUBREDDITS)
subreddit = reddit.subreddit(subreddit_string)

print(f"🚀 Monitoring {len(TARGET_SUBREDDITS)} subreddits for web dev/business leads...")
print(f"📍 Target subreddits: {', '.join(TARGET_SUBREDDITS)}")

def process_content(content, content_type):
    """
    Process either a post or comment and check if it's a relevant lead
    """
    global processed_count
    processed_count += 1

    if should_print_milestone(processed_count):
        print(f"Processed {processed_count} items...")

    try:
        # Skip deleted/removed content
        if content.author is None or content.author in ['AutoModerator']:
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
        
        # First pass: Basic keyword filtering - More specific targeting
        basic_keywords = [
            # Web Developer Keywords
            'client wants', 'client needs', 'client asking', 'offer clients', 'white label', 'reseller', 
            'freelance web dev', 'web dev agency', 'web development service', 'additional service',
            'upsell', 'partner program', 'revenue stream',
            
            # Business Chatbot/Conversion Keywords  
            'chatbot', 'conversion rate', 'website conversion', 'lead generation', 'customer support',
            'automate customer', 'live chat', 'ai assistant', 'user engagement', 'website engagement',
            'qualify leads', 'capture leads', 'customer inquiries', 'response time', 'support costs',
            'visitors leaving', 'not converting', 'website sales', 'customer service automation', 'conversion', 'website',
            'web site', 'visitors', 'users', 'CTA', 'CTAs'
        ]
        
        if any(keyword in text_content for keyword in basic_keywords):
            # Negative keyword filtering - exclude irrelevant content
            negative_keywords = [
                'cryptocurrency', 'crypto', 'bitcoin', 'trading card', 'pokemon', 'gaming', 
                'card game', 'board game', 'nft', 'blockchain', 'mining', 'gpu', 'graphics card',
                'dropshipping', 'amazon fba', 'affiliate marketing', 'mlm', 'pyramid scheme',
                'day trading', 'forex', 'stock market', 'investing', 'real estate', 'restaurant',
                'food truck', 'physical store', 'brick and mortar', 'retail location', 'warehouse'
            ]
            
            if any(neg_keyword in text_content for neg_keyword in negative_keywords):
                print(f"🚫 Filtered out due to negative keywords: {display_text[:100]}...")
                return
            
            print(f"🔍 Found potential lead in {content_type}: {display_text}")

            # Second pass: Embedding-based filtering
            is_relevant, similarity_score = is_relevant_comment(text_content)
            if is_relevant:
                
                # Prepare lead data
                lead_data = {
                    'timestamp': datetime.now().isoformat(),
                    'content_type': content_type,
                    'subreddit': content.subreddit.display_name,
                    'author': str(content.author),
                    'similarity_score': similarity_score,
                    'reddit_score': content.score,
                    'created_utc': content.created_utc
                }
                
                # Add content-specific data
                if content_type == 'post':
                    lead_data.update({
                        'title': content.title,
                        'selftext': content.selftext,
                        'permalink': f"https://www.reddit.com{content.permalink}",
                        'url': content.url if hasattr(content, 'url') else None
                    })
                else:  # comment
                    lead_data.update({
                        'comment': content.body,
                        'permalink': f"https://www.reddit.com{content.permalink}"
                    })
                
                # Display the lead
                print("\n===========================")
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
                print(f"📊 Reddit Score: {content.score}")
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
    
    post_thread.start()
    comment_thread.start()
    
    print("🔄 Monitoring both posts and comments...")
    
    # Process content from queue
    while True:
        try:
            content_type, content = content_queue.get(timeout=1)
            process_content(content, content_type)
            content_queue.task_done()
            time.sleep(1)  # Rate limiting
        except queue.Empty:
            continue

except KeyboardInterrupt:
    print("\n🛑 Monitoring stopped by user.")
except Exception as e:
    print(f"⚠️ Error: {e}")
