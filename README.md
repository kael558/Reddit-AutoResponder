# English Learning Lead Monitor

A Python bot that monitors Reddit for users learning English and can automatically invite them to join your Discord community for speaking practice.

## Features

- **Smart Detection**: Uses AI embeddings to identify relevant English learning posts and comments
- **LLM Verification**: Uses Cohere AI to verify leads are genuinely seeking English practice
- **Targeted Subreddits**: Monitors 20+ English learning subreddits
- **Daily Digest Emails**: Receive one compiled email per day with all leads and filtering statistics
- **CSV Export**: Automatic CSV attachment with lead details (name, content, profile link, subreddit, post link)
- **Lead Tracking**: Saves leads to daily JSON files
- **Rate Limiting**: Respects Reddit API limits and user cooldowns
- **Multi-Stage Filtering**: Smart filtering pipeline to exclude spam and irrelevant content

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Create Reddit app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
3. Configure `.env` file (see Configuration section)
4. Run: `python english_main.py`

## Monitored Subreddits

The bot monitors 20+ English learning subreddits including:

- r/EnglishLearning (607k members)
- r/languagelearning (3.3M members)
- r/LearnEnglish
- r/language_exchange (199k members)
- r/IELTS, r/TOEFL, r/ESL
- And many more...

## Configuration

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages: `praw`, `python-dotenv`, `numpy`, `cohere`, `requests`

### 2. Create Reddit App

1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Choose "Script" as app type
4. Set redirect URI to `http://localhost:8080`
5. Note down your **Client ID** and **Client Secret**

### 3. Environment Variables

Create a `.env` file:

```env
# Reddit API Credentials (required)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here

# Reddit Account Credentials (only needed for auto-responding/DMing)
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# Cohere API Key (for LLM verification - required)
COHERE_API_KEY=your_cohere_api_key_here

# SMTP2GO Email Configuration (for daily digest - required)
SMTP2GO_API_KEY=your_smtp2go_api_key_here
EMAIL_ADDRESS=your_email@yourdomain.com
NOTIFICATION_EMAIL=your_email@yourdomain.com
REPLY_TO=your_email@yourdomain.com

# User Agent (optional)
USER_AGENT=English Learning Community Bot v1.0
```

**Get API Keys:**

- Cohere: [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys) (Free tier: 1000 calls/month)
- SMTP2GO: [smtp2go.com](https://www.smtp2go.com/) (Free tier: 1000 emails/month)

## Usage

### Basic Monitoring

```bash
python english_main.py
```

The bot will:

- Monitor all target subreddits for English learning content
- Display found leads in the console
- Save leads to `english_leads_YYYY-MM-DD.json`
- Create filtering statistics in `filtering_stats_YYYY-MM-DD.json`

### Daily Digest Email

The digest email system compiles all leads into one email sent at the end of each day.

#### Manual Test

```bash
python send_daily_digest.py
```

#### Automated Setup (cron)

Add to crontab (`crontab -e`):

```bash
# Send digest at 11:59 PM daily
59 23 * * * cd /root/Reddit-AutoResponder && source venv/bin/activate && python3 send_daily_digest.py >> digest_log.txt 2>&1
```

The daily digest includes:

- Summary count of leads
- Filtering performance report showing conversion at each stage
- CSV attachment with all lead details (name, content, profile_link, subreddit, post_link)

## Running as a System Service (systemd)

For production use, run the bot as a systemd service with auto-restart on crashes.

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/english-main.service
```

```ini
[Unit]
Description=English Reddit Lead Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Reddit-AutoResponder

# Use venv Python
ExecStart=/root/Reddit-AutoResponder/venv/bin/python3 -u english_main.py

Restart=on-failure
RestartSec=5

# Pause if it keeps crashing
StartLimitIntervalSec=600
StartLimitBurst=10

KillSignal=SIGINT
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now english-main
sudo systemctl status english-main
```

### 3. View Logs

```bash
# Follow logs in real-time
journalctl -u english-main -f

# View recent logs
journalctl -u english-main -n 100
```

### 4. Manage Service

```bash
# Stop service
sudo systemctl stop english-main

# Restart service
sudo systemctl restart english-main

# Reset if hit restart limit
sudo systemctl reset-failed english-main
sudo systemctl restart english-main
```

## Filtering Pipeline

The bot uses a multi-stage filtering approach:

1. **Practice Keywords Filter**: Checks for keywords like "looking for", "need practice", "conversation partner"
2. **Negative Keywords Filter**: Excludes spam, commercial content, and general discussions
3. **Seeking Language Filter**: Ensures content contains question/seeking language patterns
4. **Embedding Similarity Filter**: Uses AI embeddings to calculate semantic similarity to target topics
5. **LLM Verification** (Final Stage): Uses Cohere to verify genuine seeking of English speaking practice

All filtering statistics are saved daily and included in the digest email report.

## Output Files

### Lead Data (`english_leads_YYYY-MM-DD.json`)

```json
{
	"timestamp": "2025-01-15T10:30:00",
	"content_type": "post",
	"subreddit": "EnglishLearning",
	"author": "username",
	"similarity_score": 0.75,
	"best_matching_topic": "I need speaking practice",
	"reddit_score": 15,
	"llm_verification": "YES - User is explicitly seeking conversation partners",
	"title": "Looking for speaking practice partners",
	"selftext": "I'm an intermediate English learner...",
	"permalink": "https://www.reddit.com/r/EnglishLearning/..."
}
```

### CSV Export (`leads_YYYY-MM-DD.csv`)

Attached to daily digest email with columns:

- `name`: Reddit username
- `content`: Post title/body or comment text
- `profile_link`: Link to user's Reddit profile
- `subreddit`: Subreddit name
- `post_link`: Link to the post/comment

## Troubleshooting

### Authentication Errors

Check Reddit credentials in `.env`

### No Leads Found

- Lower similarity threshold in `english_main.py` (default: 0.35)
- Check filtering statistics in `filtering_stats_YYYY-MM-DD.json`

### Rate Limit Errors

Increase sleep time between requests in `english_main.py`

### Email Not Sending

- Verify SMTP2GO API key in `.env`
- Check `digest_log.txt` for error messages
- Test manually: `python send_daily_digest.py`

### Service Not Starting

```bash
# Check service status
sudo systemctl status english-main

# View detailed logs
journalctl -u english-main -n 50

# Verify Python path
ls /root/Reddit-AutoResponder/venv/bin/python3
```

## Safety & Best Practices

- **Respect Reddit API Guidelines**: Follow [Content Policy](https://www.redditinc.com/policies/content-policy) and [API Terms](https://www.redditinc.com/policies/data-api-terms)
- **Test First**: Run in monitoring mode before enabling auto-responses
- **Rate Limiting**: Built-in 2-second delays between processing
- **User Cooldown**: 24-hour cooldown between interactions
- **Community Guidelines**: Follow each subreddit's specific rules
- **Be Authentic**: Offer genuine value to the community

## Legal & Ethical Considerations

- Only use for legitimate community building
- Respect user privacy and consent
- Don't send unsolicited promotional messages
- Follow all applicable laws and platform terms of service
- Be transparent about your bot's purpose

## Support

If you encounter issues:

1. Check console output for error messages
2. Review log files (`digest_log.txt`, `journalctl -u english-main`)
3. Verify API credentials in `.env`
4. Test with manual script runs before automation
5. Check filtering statistics to understand what's being filtered

---

**Happy community building!**
