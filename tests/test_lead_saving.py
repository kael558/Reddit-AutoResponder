#!/usr/bin/env python3
"""
Test script to verify that leads are properly saved to JSON files.
This test simulates a lead passing all filters and ensures it gets saved.
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import from english_main
sys.path.insert(0, str(Path(__file__).parent))

def test_lead_saving():
    """Test that save_lead_to_json properly saves leads to the daily JSON file"""

    print("="*60)
    print("🧪 Testing Lead Saving Functionality")
    print("="*60)

    # Import the function we're testing
    from english_main import save_lead_to_json

    # Create a test lead with all required fields
    test_lead = {
        'timestamp': datetime.now().isoformat(),
        'content_type': 'post',
        'subreddit': 'EnglishLearning',
        'author': 'test_user_12345',
        'similarity_score': 0.75,
        'best_matching_topic': 'I need speaking practice',
        'reddit_score': 10,
        'created_utc': datetime.now().timestamp(),
        'title': 'Test Post: Looking for English practice partner',
        'selftext': 'Hi everyone, I am looking for someone to practice speaking English with. I want to improve my conversation skills.',
        'permalink': 'https://www.reddit.com/r/EnglishLearning/comments/test123',
        'url': 'https://www.reddit.com/r/EnglishLearning/comments/test123',
        'lead_type': 'practice_conversation',
        'responded': False,
        'dm_sent': False,
        'email_sent': False,
        'llm_verification': 'YES - User is actively looking for English speaking practice partner'
    }

    # Get expected filename
    today = datetime.now().strftime("%Y-%m-%d")
    expected_filename = f"english_leads_{today}.json"

    print(f"\n📝 Test Lead Details:")
    print(f"   - Author: {test_lead['author']}")
    print(f"   - Content Type: {test_lead['content_type']}")
    print(f"   - Lead Type: {test_lead['lead_type']}")
    print(f"   - Similarity Score: {test_lead['similarity_score']}")
    print(f"   - Expected File: {expected_filename}")

    # Check if file exists before test
    file_existed_before = os.path.exists(expected_filename)
    leads_count_before = 0

    if file_existed_before:
        with open(expected_filename, 'r', encoding='utf-8') as f:
            existing_leads = json.load(f)
            leads_count_before = len(existing_leads)
        print(f"\n📂 File exists with {leads_count_before} leads before test")
    else:
        print(f"\n📂 File does not exist yet - will be created")

    # Test 1: Try to save the lead
    print(f"\n🔄 Test 1: Attempting to save lead...")
    try:
        save_lead_to_json(test_lead)
        print("   ✅ save_lead_to_json() executed without errors")
    except Exception as e:
        print(f"   ❌ ERROR: save_lead_to_json() raised exception: {e}")
        return False

    # Test 2: Verify file was created
    print(f"\n🔄 Test 2: Verifying file exists...")
    if not os.path.exists(expected_filename):
        print(f"   ❌ FAILED: File {expected_filename} was not created!")
        return False
    else:
        print(f"   ✅ File {expected_filename} exists")

    # Test 3: Verify file contains valid JSON
    print(f"\n🔄 Test 3: Verifying file contains valid JSON...")
    try:
        with open(expected_filename, 'r', encoding='utf-8') as f:
            saved_leads = json.load(f)
        print(f"   ✅ File contains valid JSON")
    except json.JSONDecodeError as e:
        print(f"   ❌ FAILED: File contains invalid JSON: {e}")
        return False

    # Test 4: Verify lead count increased
    print(f"\n🔄 Test 4: Verifying lead was added...")
    expected_count = leads_count_before + 1
    actual_count = len(saved_leads)

    if actual_count != expected_count:
        print(f"   ❌ FAILED: Expected {expected_count} leads, but found {actual_count}")
        return False
    else:
        print(f"   ✅ Lead count increased from {leads_count_before} to {actual_count}")

    # Test 5: Verify the saved lead contains correct data
    print(f"\n🔄 Test 5: Verifying lead data is correct...")
    saved_lead = saved_leads[-1]  # Get the last lead (the one we just added)

    if saved_lead['author'] != test_lead['author']:
        print(f"   ❌ FAILED: Author mismatch - expected '{test_lead['author']}', got '{saved_lead['author']}'")
        return False

    if saved_lead['lead_type'] != test_lead['lead_type']:
        print(f"   ❌ FAILED: Lead type mismatch - expected '{test_lead['lead_type']}', got '{saved_lead['lead_type']}'")
        return False

    if saved_lead['similarity_score'] != test_lead['similarity_score']:
        print(f"   ❌ FAILED: Similarity score mismatch")
        return False

    print(f"   ✅ Lead data is correct:")
    print(f"      - Author: {saved_lead['author']}")
    print(f"      - Lead Type: {saved_lead['lead_type']}")
    print(f"      - Similarity Score: {saved_lead['similarity_score']}")
    print(f"      - Subreddit: r/{saved_lead['subreddit']}")

    # Test 6: Verify all required fields are present
    print(f"\n🔄 Test 6: Verifying all required fields are present...")
    required_fields = [
        'timestamp', 'content_type', 'subreddit', 'author',
        'similarity_score', 'best_matching_topic', 'reddit_score',
        'lead_type', 'responded', 'dm_sent', 'email_sent', 'llm_verification'
    ]

    missing_fields = [field for field in required_fields if field not in saved_lead]

    if missing_fields:
        print(f"   ❌ FAILED: Missing required fields: {', '.join(missing_fields)}")
        return False
    else:
        print(f"   ✅ All {len(required_fields)} required fields are present")

    # All tests passed!
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"   - File: {expected_filename}")
    print(f"   - Total leads in file: {actual_count}")
    print(f"   - Test lead saved successfully")
    print(f"   - All data fields verified")
    print("\n💡 You can now check the file to see your test lead:")
    print(f"   cat {expected_filename}")

    return True

def cleanup_test_lead():
    """Optional: Remove the test lead from the file"""
    print("\n" + "="*60)
    response = input("🧹 Do you want to remove the test lead from the file? (y/n): ").lower().strip()

    if response == 'y':
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"english_leads_{today}.json"

        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                leads = json.load(f)

            # Remove leads with test author
            original_count = len(leads)
            leads = [lead for lead in leads if lead.get('author') != 'test_user_12345']
            new_count = len(leads)

            # Save back
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)

            removed = original_count - new_count
            print(f"   ✅ Removed {removed} test lead(s)")
            print(f"   📊 File now contains {new_count} lead(s)")
        else:
            print(f"   ℹ️ File {filename} not found")
    else:
        print("   ℹ️ Keeping test lead in file")

if __name__ == "__main__":
    try:
        success = test_lead_saving()

        if success:
            cleanup_test_lead()
            sys.exit(0)
        else:
            print("\n❌ Tests failed!")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
