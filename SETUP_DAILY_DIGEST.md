# Daily Digest Email Setup Guide

This guide explains how to set up the daily digest email system on your Digital Ocean droplet.

## Overview

The system has been modified to work in two stages:

1. **`english_main.py`**: Continuously monitors Reddit and saves lead data to `pending_emails_YYYY-MM-DD.json` files
2. **`send_daily_digest.py`**: Runs once per day to compile all leads into a single digest email

## Benefits

- ✅ Receive one comprehensive email per day instead of dozens of individual emails
- ✅ Better overview of all leads collected
- ✅ Cleaner inbox
- ✅ Automatic archiving of sent digests

## Setup Instructions

### 1. Verify Email Configuration

Make sure your `.env` file has the email credentials:

```bash
EMAIL_ADDRESS=your-email@privateemail.com
EMAIL_PASSWORD=your-password
NOTIFICATION_EMAIL=your-email@privateemail.com  # Can be same or different
```

### 2. Test the Digest Script

Before setting up the cron job, test the script manually:

```bash
cd /path/to/AutoResponder
python3 send_daily_digest.py
```

This will:

- Check for any pending email files
- Send a digest if leads are found
- Archive the processed files to `email_archives/`

### 3. Set Up Cron Job on Digital Ocean Droplet

#### Option A: Daily Digest at 11:59 PM (Recommended)

This sends the digest at the end of each day:

```bash
# Open crontab editor
crontab -e

# Add this line (adjust path to your actual path):
59 23 * * * cd /path/to/AutoResponder && /usr/bin/python3 send_daily_digest.py >> digest_log.txt 2>&1
```

#### Option B: Daily Digest at 8:00 AM

This sends the previous day's digest in the morning:

```bash
0 8 * * * cd /path/to/AutoResponder && /usr/bin/python3 send_daily_digest.py >> digest_log.txt 2>&1
```

#### Verify Cron Job

```bash
# List current cron jobs
crontab -l

# Check if cron service is running
sudo systemctl status cron
```

### 4. Monitor the System

#### Check Log File

The cron job outputs to `digest_log.txt`:

```bash
cd /path/to/AutoResponder
tail -f digest_log.txt
```

#### Check Pending Emails

View today's pending leads:

```bash
cat pending_emails_$(date +%Y-%m-%d).json
```

#### Check Archive

View archived digests:

```bash
ls -lh email_archives/
```

## File Structure

```
AutoResponder/
├── english_main.py              # Main monitoring script (runs continuously)
├── send_daily_digest.py         # Daily digest sender (runs once per day)
├── pending_emails_YYYY-MM-DD.json  # Today's pending leads
├── digest_log.txt               # Log file for digest script
├── email_archives/              # Archive of sent digests
│   └── pending_emails_*.json    # Historical pending files
└── .env                         # Environment variables
```

## Cron Schedule Examples

| Time                      | Cron Expression | Description         |
| ------------------------- | --------------- | ------------------- |
| 11:59 PM daily            | `59 23 * * *`   | End of day digest   |
| 8:00 AM daily             | `0 8 * * *`     | Morning digest      |
| Noon daily                | `0 12 * * *`    | Midday digest       |
| Twice daily (9 AM & 9 PM) | `0 9,21 * * *`  | Morning and evening |

## Troubleshooting

### No Email Received

1. Check if cron job ran:

   ```bash
   grep CRON /var/log/syslog | tail -20
   ```

2. Check digest log:

   ```bash
   tail -50 digest_log.txt
   ```

3. Verify email credentials in `.env`

4. Test email sending manually:
   ```bash
   python3 send_daily_digest.py
   ```

### Cron Not Running

```bash
# Start cron service
sudo systemctl start cron

# Enable cron on boot
sudo systemctl enable cron
```

### Permission Issues

```bash
# Make script executable
chmod +x send_daily_digest.py

# Verify ownership
ls -lh send_daily_digest.py
```

### Python Not Found

Find the correct Python path:

```bash
which python3
# Use this path in your cron job
```

## Email Preview

The daily digest email includes:

- **Summary**: Total number of leads for the day
- **Individual Lead Cards**: Each with:
  - Username and subreddit
  - Content preview (title/body or comment)
  - Similarity score and matching topic
  - LLM verification reasoning
  - Recommended message to send
  - Direct links to DM user and view post
- **Beautiful HTML formatting** with color-coded sections

## Advanced Configuration

### Change Digest Time

Edit the cron schedule in `crontab -e`. Use [crontab.guru](https://crontab.guru) to help build schedules.

### Multiple Digests Per Day

Add multiple cron entries:

```bash
# Morning digest (9 AM)
0 9 * * * cd /path/to/AutoResponder && /usr/bin/python3 send_daily_digest.py >> digest_log.txt 2>&1

# Evening digest (9 PM)
0 21 * * * cd /path/to/AutoResponder && /usr/bin/python3 send_daily_digest.py >> digest_log.txt 2>&1
```

### Clean Up Old Archives

Add a monthly cleanup task:

```bash
# Delete archives older than 90 days on the 1st of each month at 3 AM
0 3 1 * * find /path/to/AutoResponder/email_archives -name "pending_emails_*.json" -mtime +90 -delete
```

## Switching Back to Individual Emails

If you want to revert to immediate individual emails:

1. In `english_main.py`, replace `save_email_notification_data()` calls back to `send_email_notification()`
2. Remove or disable the cron job:
   ```bash
   crontab -e
   # Comment out or delete the digest line
   ```

## Support

For issues or questions:

- Check the log files: `digest_log.txt`
- Review the cron logs: `grep CRON /var/log/syslog`
- Verify email settings in `.env`
