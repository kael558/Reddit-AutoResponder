# Reddit Lead Monitor for Web Developers & Small Business Owners

This script monitors specific Reddit subreddits to find potential leads for chatbot/web development services targeting web developers and small business owners.

## Features

- **Targeted Subreddit Monitoring**: Monitors 15 relevant subreddits including r/webdev, r/smallbusiness, r/entrepreneur, etc.
- **Local Embedding Filtering**: Uses sentence-transformers to semantically filter comments for relevance
- **Daily JSON Export**: Saves leads to timestamped JSON files for easy tracking
- **No Auto-Reply**: Safely monitors without automatically posting replies

## Setup

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Reddit API Setup**:

   - Go to https://www.reddit.com/prefs/apps
   - Create a new app (script type)
   - Note your client ID and secret

3. **Environment Variables**:
   Create a `.env` file with:
   ```
   REDDIT_CLIENT_ID=your_client_id_here
   REDDIT_CLIENT_SECRET=your_client_secret_here
   USER_AGENT=Reddit Chatbot Monitor v1.0
   ```

## Usage

```bash
python main.py
```

The script will:

- Monitor comments in real-time from target subreddits
- Filter comments using embeddings for relevance
- Display potential leads in the console
- Save leads to `leads_YYYY-MM-DD.json` files

## Monitored Subreddits

- **Web Development**: r/webdev, r/javascript, r/reactjs, r/Frontend, r/webdevelopment, r/coding, r/programming
- **Business**: r/smallbusiness, r/entrepreneur, r/startups, r/business, r/marketing, r/freelance, r/solopreneur, r/digitalnomad

## Target Topics

The embedding model filters for comments related to:

- Website help and development needs
- Web developer services
- Business website challenges
- Chatbot and automation needs
- Website optimization and maintenance

## Output Format

Leads are saved as JSON with the following structure:

```json
{
	"timestamp": "2024-01-15T10:30:00",
	"subreddit": "webdev",
	"author": "username",
	"comment": "Full comment text...",
	"permalink": "https://www.reddit.com/r/webdev/comments/...",
	"score": 5,
	"created_utc": 1705312200
}
```

## Customization

- **Adjust similarity threshold**: Modify the `threshold` parameter in `is_relevant_comment()` (default: 0.3)
- **Add more subreddits**: Update the `TARGET_SUBREDDITS` list
- **Modify target topics**: Update the `TARGET_TOPICS` list for different filtering criteria

# Automatically reply

# Automatically send DMs to web developers

web_design (no promotion allowed)
smallbusiness (no promotion allowed)

🙌 We're looking for beta testers for our NEW practice conversational English app !

---

https://discord.com/invite/yjaraMBuSG

We're looking for people who are interested in improving their English conversation skills. Come join our Discord community and we'll get you started with the app.
We want to hear YOUR feedback and improve the app based on your needs.

https://youtu.be/s5Mv91fBw_8

---

We're looking for people who are interested in improving their English conversation skills. Come join our Discord community and we'll get you started with the app.

We want to hear YOUR feedback and improve the app based on your needs.

Check out the app here: [Youtube Video](https://youtu.be/s5Mv91fBw_8)

---

Hey 👋 saw your post about practicing conversational English! We're building an app to do exactly that!

We'd love for you to join our friendly discord community and we can help each other: https://discord.com/invite/yjaraMBuSG

Hey 👋 saw your post about learning English! We're building an app to do exactly that! We'd love for you to join our friendly discord community and we can help each other: https://discord.com/invite/yjaraMBuSG

---

We're looking for people who are interested in improving their English conversation skills. Come join our Discord community and we'll get you started with the app.
We want to hear YOUR feedback and improve the app based on your needs.  
Check out the app here: [Youtube Video](https://youtu.be/s5Mv91fBw_8)
Join our discord community here: [Discord](https://discord.com/invite/yjaraMBuSG)
