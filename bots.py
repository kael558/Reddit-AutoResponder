import asyncio
import json
import random
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import os
from dotenv import load_dotenv

load_dotenv()

# Load accounts from JSON
with open('accounts.json') as f:
    accounts = json.load(f)

async def run_session(account):
    async with async_playwright() as p:
        # Launch browser with proxy and fingerprint settings
        browser = await p.chromium.launch(
            headless=False,
            proxy={
                "server": account['stealth']['proxy'],
                "username": os.getenv('PROXY_USER'),
                "password": os.getenv('PROXY_PASS')
            },
            args=[
                f"--window-size={account['stealth']['viewport']['width']},{account['stealth']['viewport']['height']}",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = await browser.new_context(
            user_agent=account['stealth']['userAgent'],
            viewport=account['stealth']['viewport'],
            timezone_id=account['stealth']['timezone'],
            locale=account['stealth']['locale']
        )

        page = await context.new_page()
        await stealth_async(page)  # Apply stealth plugins

        # Random mouse movement pattern
        async def random_mouse():
            for _ in range(random.randint(3, 7)):
                x = random.randint(0, account['stealth']['viewport']['width'])
                y = random.randint(0, account['stealth']['viewport']['height'])
                await page.mouse.move(x, y)
                await page.wait_for_timeout(random.randint(200, 1500))

        # Human-like scrolling
        async def human_scroll():
            scroll_steps = random.randint(5, 15)
            for _ in range(scroll_steps):
                scroll_amount = random.randint(200, 800)
                await page.mouse.wheel(0, scroll_amount)
                await page.wait_for_timeout(random.randint(800, 3000))

        # Login to Reddit
        await page.goto('https://www.reddit.com/login', timeout=60000)
        await random_mouse()
        
        # Type with human-like delays
        async def human_type(selector, text):
            for char in text:
                await page.type(selector, char, delay=random.uniform(50, 150))
                if random.random() > 0.9:  # 10% chance of "mistake"
                    await page.keyboard.press('Backspace')
                    await page.wait_for_timeout(random.randint(100, 300))
                    await page.type(selector, char)

        await human_type('#loginUsername', account['email'])
        await page.wait_for_timeout(random.randint(500, 2000))
        await human_type('#loginPassword', account['password'])
        await page.wait_for_timeout(random.randint(1000, 3000))
        
        # Click login with random delay
        await page.click('button[type=submit]', delay=random.randint(50, 250))
        await page.wait_for_timeout(5000)  # Wait for login

        # Main activity loop (5 minutes)
        end_time = asyncio.get_event_loop().time() + 300  # 5 minutes
        while asyncio.get_event_loop().time() < end_time:
            # Randomly choose an action
            action = random.choice([
                "scroll", "click_post", "back", "visit_subreddit"
            ])

            if action == "scroll":
                await human_scroll()
            elif action == "click_post":
                posts = await page.query_selector_all('a[data-click-id="body"]')
                if posts:
                    await random_mouse()
                    await posts[random.randint(0, len(posts)-1)].click(delay=random.randint(50, 250))
                    await page.wait_for_timeout(random.randint(3000, 8000))
            elif action == "back":
                await page.go_back()
                await page.wait_for_timeout(random.randint(2000, 5000))
            elif action == "visit_subreddit":
                await page.goto(f"https://www.reddit.com/r/{random.choice(['news','askreddit','worldnews'])}")
                await page.wait_for_timeout(random.randint(4000, 7000))

            # Random short break between actions
            await page.wait_for_timeout(random.randint(1000, 3000))

        await browser.close()

async def main():
    # Run 5 accounts simultaneously
    tasks = [run_session(account) for account in accounts[:5]]
    await asyncio.gather(*tasks)

asyncio.run(main())