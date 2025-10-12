# English Learning Lead Monitor 🎯

This Python script monitors Reddit for users learning English and can automatically invite them to join your Discord community for speaking practice.

## Features

- 🔍 **Smart Detection**: Uses AI embeddings to identify relevant English learning posts and comments
- 🤖 **LLM Verification**: Uses Cohere AI to verify leads are genuinely seeking English practice
- 🎯 **Targeted Subreddits**: Monitors 20+ English learning subreddits
- 🤖 **Auto-Response**: Optional automatic replies to posts/comments
- 📩 **Direct Messaging**: Optional DM functionality
- 📧 **Email Notifications**: Receive beautiful HTML emails with lead info and one-click DM links
- 💾 **Lead Tracking**: Saves leads to daily JSON files (`english_leads_YYYY-MM-DD.json`)
- ⏰ **Rate Limiting**: Respects Reddit API limits and user cooldowns
- 🚫 **Smart Filtering**: Multi-stage filtering to exclude spam and irrelevant content

## Monitored Subreddits

- r/EnglishLearning (607k members)
- r/languagelearning (3.3M members)
- r/LearnEnglish
- r/learnEnglishOnline (40k members)
- r/EnglishTips
- r/grammar
- r/writing
- r/SpeakingPractice
- r/IELTS
- r/TOEFL
- r/ESL
- r/EnglishStudy
- r/pronunciation
- r/vocabulary
- r/conversationpractice
- r/language_exchange (199k members)
- r/speakingpartners
- r/englishconversation
- r/studybuddy
- r/LearnEnglishOnReddit (6k members)
- r/LearnEnglishFree (3k members)
- r/Learn_English (3k members)
- r/EnglishPractice

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install praw sentence-transformers scikit-learn python-dotenv numpy cohere
```

### 2. Create Reddit App

1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Choose "Script" as app type
4. Set redirect URI to `http://localhost:8080`
5. Note down your **Client ID** and **Client Secret**

### 3. Configure Environment

Create a `.env` file in your project directory:

```env
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here

# Reddit Account Credentials (only needed for auto-responding/DMing)
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# Cohere API Key (for LLM verification)
COHERE_API_KEY=your_cohere_api_key_here

# Email Configuration (Namecheap Private Email - optional)
EMAIL_ADDRESS=your_email@yourdomain.com
EMAIL_PASSWORD=your_email_password
NOTIFICATION_EMAIL=your_email@yourdomain.com

# User Agent (optional)
USER_AGENT=English Learning Community Bot v1.0
```

**Note**: Get your Cohere API key from [Cohere Dashboard](https://dashboard.cohere.com/api-keys). The free tier includes 1000 API calls per month.

### 4. Configure Discord Settings

Edit the following variables in `english_main.py`:

```python
# Discord community details
DISCORD_INVITE_LINK = "https://discord.gg/your-actual-invite"  # Your Discord invite
COMMUNITY_NAME = "Your Community Name"  # Your community name
```

### 5. Configure Response Settings

```python
# Auto-response settings
AUTO_RESPOND = False  # Set to True to enable auto-replies
SEND_DMS = False      # Set to True to enable direct messaging
SEND_EMAILS = True    # Set to True to enable email notifications
RESPONSE_COOLDOWN_HOURS = 24  # Hours between interactions with same user
```

**Note**: For email notifications, see [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed configuration instructions.

## Usage

### Basic Monitoring (Read-Only)

```bash
python english_main.py
```

This will:

- Monitor all target subreddits for English learning content
- Display found leads in the console
- Save leads to `english_leads_YYYY-MM-DD.json`

### With Auto-Response

1. Set `AUTO_RESPOND = True` in the script
2. Ensure `REDDIT_USERNAME` and `REDDIT_PASSWORD` are set in `.env`
3. Run the script

The bot will automatically reply to relevant posts/comments with your Discord invite.

### With Direct Messaging

1. Set `SEND_DMS = True` in the script
2. Ensure `REDDIT_USERNAME` and `REDDIT_PASSWORD` are set in `.env`
3. Run the script

The bot will send direct messages to users instead of public replies.

### With Email Notifications

1. Set `SEND_EMAILS = True` in the script
2. Add email credentials to `.env`:
   ```env
   EMAIL_ADDRESS=your_email@yourdomain.com
   EMAIL_PASSWORD=your_email_password
   NOTIFICATION_EMAIL=your_email@yourdomain.com
   ```
3. Run the script

The bot will send beautiful HTML email notifications with:

- Complete lead information
- Recommended message template
- Direct link to DM the user
- Link to view the original post

See [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed configuration.

## Filtering Pipeline

The script uses a multi-stage filtering approach to ensure high-quality leads:

1. **Keyword Filtering**: Checks for practice-seeking keywords like "looking for", "need practice", "conversation partner"
2. **Negative Keyword Filtering**: Excludes spam, commercial content, and general discussions
3. **Seeking Language Detection**: Ensures content contains question/seeking language patterns
4. **Embedding Similarity**: Uses AI embeddings to calculate semantic similarity to target topics
5. **LLM Verification** (Final Stage): Uses Cohere's language model to verify the person is genuinely seeking English speaking practice

All filtered content is saved to `unfiltered_english_leads_YYYY-MM-DD.json` with the reason for filtering, allowing you to review and refine the filters if needed.

## Response Templates

The script includes three response templates:

1. **Speaking Practice**: For users seeking conversation partners
2. **Learning Support**: For users struggling with English
3. **General Invite**: Default template for other relevant content

Templates are automatically selected based on content analysis.

## Lead Data Structure

Each lead is saved with the following information:

```json
{
	"timestamp": "2025-01-15T10:30:00",
	"content_type": "post",
	"subreddit": "EnglishLearning",
	"author": "username",
	"similarity_score": 0.75,
	"best_matching_topic": "I need speaking practice",
	"reddit_score": 15,
	"created_utc": 1642248600,
	"responded": false,
	"dm_sent": false,
	"email_sent": true,
	"llm_verification": "YES - User is explicitly seeking conversation partners for English practice",
	"title": "Looking for speaking practice partners",
	"selftext": "I'm an intermediate English learner...",
	"permalink": "https://www.reddit.com/r/EnglishLearning/...",
	"url": null
}
```

## Safety Features

- **Rate Limiting**: 2-second delays between processing
- **User Cooldown**: 24-hour cooldown between interactions with same user
- **Spam Prevention**: Filters out promotional/spam content
- **Error Handling**: Graceful handling of API errors and network issues
- **Keyword Filtering**: Excludes irrelevant content using negative keywords

## Monitoring Output

```
🚀 Monitoring 22 subreddits for English learning leads...
📍 Target subreddits: EnglishLearning, languagelearning, LearnEnglish...
🤖 Auto-respond: OFF
📩 Direct messages: OFF
📧 Email notifications: ON
🔄 Monitoring both posts and comments for English learning leads...

===========================
🎯 ENGLISH LEARNING LEAD FOUND!
📌 Content Type: POST
📌 Subreddit: r/EnglishLearning
👤 Author: u/learner123
📝 Title: Looking for conversation practice
💬 Body: I'm looking for someone to practice speaking English with...
🔗 Link: https://www.reddit.com/r/EnglishLearning/...
📊 Similarity Score: 0.78
📊 Reddit Score: 12
✅ Email notification sent!
===========================

💾 English lead saved to english_leads_2025-01-15.json
```

## Important Notes

### Reddit API Guidelines

- Respect Reddit's [Content Policy](https://www.redditinc.com/policies/content-policy)
- Follow [API Terms of Use](https://www.redditinc.com/policies/data-api-terms)
- Avoid spamming - use cooldowns and rate limiting
- Be helpful and genuine in your responses

### Best Practices

1. **Test First**: Run in read-only mode before enabling responses
2. **Monitor Results**: Check the quality of detected leads
3. **Adjust Thresholds**: Fine-tune similarity thresholds if needed
4. **Community Guidelines**: Follow each subreddit's specific rules
5. **Be Authentic**: Make your Discord community genuinely helpful

### Troubleshooting

**Authentication Errors**: Check your Reddit credentials in `.env`

**No Leads Found**: Lower the similarity threshold (default: 0.35)

**Rate Limit Errors**: Increase sleep time between requests

**Permission Errors**: Ensure your Reddit account can post/message

## Legal & Ethical Considerations

- Only use this for legitimate community building
- Respect user privacy and consent
- Don't send unsolicited promotional messages
- Follow all applicable laws and platform terms of service
- Be transparent about your bot's purpose

## Support

If you encounter issues:

1. Check the console output for error messages
2. Verify your Reddit API credentials
3. Ensure all dependencies are installed
4. Test with a smaller set of subreddits first

---

**Happy community building! 🎉**
