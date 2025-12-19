#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the new digest features:
1. CSV generation
2. Filtering statistics report
"""

import sys
import json
from datetime import datetime
from send_daily_digest import generate_csv_from_leads, load_filtering_stats, generate_filtering_report_html, generate_digest_email

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Create sample leads data
sample_leads = [
    {
        "timestamp": "2025-12-15T10:30:00",
        "content_type": "post",
        "subreddit": "EnglishLearning",
        "author": "test_user_1",
        "title": "Looking for English speaking partner",
        "selftext": "I need someone to practice speaking English with. I'm a beginner and would love to improve my conversation skills.",
        "permalink": "/r/EnglishLearning/comments/abc123/looking_for_english_speaking_partner/",
        "similarity_score": 0.85,
        "best_matching_topic": "I need speaking practice",
        "reddit_score": 15,
        "llm_verification": "YES - User is explicitly seeking English speaking practice partner"
    },
    {
        "timestamp": "2025-12-15T11:45:00",
        "content_type": "comment",
        "subreddit": "languagelearning",
        "author": "test_user_2",
        "comment": "Does anyone know where I can practice English speaking online? I'm struggling with confidence.",
        "permalink": "/r/languagelearning/comments/def456/comment/xyz789/",
        "similarity_score": 0.78,
        "best_matching_topic": "where can I practice English speaking",
        "reddit_score": 8,
        "llm_verification": "YES - User is asking for English speaking practice resources"
    }
]

# Create sample filtering statistics
sample_filtering_stats = {
    "EnglishLearning": {
        "total_posts": 100,
        "total_comments": 80,
        "no_practice_keywords": {
            "posts": 40,
            "comments": 30,
            "samples": [
                {"type": "post", "text": "What's the difference between 'affect' and 'effect'? I always get confused."},
                {"type": "comment", "text": "You should try reading more books. That's what helped me improve my English."},
                {"type": "post", "text": "Can someone translate this sentence for me? Thanks!"}
            ]
        },
        "negative_keywords": {
            "posts": 15,
            "comments": 10,
            "samples": [
                {"type": "post", "text": "I think that English grammar is totally representative of linguistic complexity in general."},
                {"type": "comment", "text": "From my experience, I recommend you try this app (affiliate link)."},
                {"type": "post", "text": "Professional translation service - get your essays translated!"}
            ]
        },
        "no_seeking_language": {
            "posts": 10,
            "comments": 8,
            "samples": [
                {"type": "comment", "text": "English pronunciation can be quite difficult for many learners."},
                {"type": "post", "text": "The importance of speaking practice in language acquisition is well documented."},
                {"type": "comment", "text": "Speaking English daily really helps improve fluency."}
            ]
        },
        "low_similarity": {
            "posts": 20,
            "comments": 15,
            "samples": [
                {"type": "post", "text": "I need help with my English homework, can someone check my essay?"},
                {"type": "comment", "text": "Looking for a tutor who can help me with TOEFL writing section."},
                {"type": "post", "text": "Where can I find English grammar exercises for intermediate level?"}
            ]
        },
        "llm_verification_failed": {
            "posts": 10,
            "comments": 12,
            "samples": [
                {"type": "post", "text": "I'm looking for English practice materials to study grammar rules."},
                {"type": "comment", "text": "Anyone know where I can practice English reading comprehension?"},
                {"type": "post", "text": "Need someone to help me with English writing assignments."}
            ]
        },
        "passed": {
            "posts": 5,
            "comments": 5
        }
    },
    "languagelearning": {
        "total_posts": 50,
        "total_comments": 45,
        "no_practice_keywords": {
            "posts": 25,
            "comments": 20,
            "samples": [
                {"type": "post", "text": "What language should I learn after English?"},
                {"type": "comment", "text": "Duolingo is a great app for learning vocabulary."}
            ]
        },
        "negative_keywords": {
            "posts": 8,
            "comments": 7,
            "samples": [
                {"type": "post", "text": "Buy my language learning course - 50% off today!"}
            ]
        },
        "no_seeking_language": {
            "posts": 5,
            "comments": 5,
            "samples": [
                {"type": "comment", "text": "Language learning requires consistent practice."}
            ]
        },
        "low_similarity": {
            "posts": 7,
            "comments": 8,
            "samples": [
                {"type": "post", "text": "Looking for French language exchange partner."}
            ]
        },
        "llm_verification_failed": {
            "posts": 3,
            "comments": 3,
            "samples": [
                {"type": "comment", "text": "I need help understanding English grammar concepts."}
            ]
        },
        "passed": {
            "posts": 2,
            "comments": 2
        }
    }
}

def test_csv_generation():
    """Test CSV generation from leads"""
    print("="*60)
    print("Testing CSV Generation")
    print("="*60)
    
    csv_content = generate_csv_from_leads(sample_leads)
    print("\nGenerated CSV:")
    print(csv_content)
    
    # Verify CSV has correct headers and data
    lines = csv_content.strip().split('\n')
    # Check header (should start with header row)
    assert 'name' in lines[0] and 'content' in lines[0] and 'profile_link' in lines[0], "CSV header incorrect"
    # CSV may have multiple lines due to multi-line content, just check it has content
    assert len(lines) >= 3, f"Expected at least 3 lines (header + 2 leads), got {len(lines)}"
    # Check for user names in CSV
    assert 'test_user_1' in csv_content, "Missing test_user_1 in CSV"
    assert 'test_user_2' in csv_content, "Missing test_user_2 in CSV"
    
    print("✅ CSV generation test passed!")
    return csv_content

def test_filtering_report():
    """Test filtering report generation"""
    print("\n" + "="*60)
    print("Testing Filtering Report Generation")
    print("="*60)
    
    report_html = generate_filtering_report_html(sample_filtering_stats)
    
    # Check that report contains key elements
    assert "EnglishLearning" in report_html, "Report missing EnglishLearning subreddit"
    assert "languagelearning" in report_html, "Report missing languagelearning subreddit"
    assert "100%" in report_html, "Report missing starting percentage"
    assert "Examples filtered:" in report_html, "Report missing example samples"
    
    print("\nGenerated Filtering Report HTML (first 500 chars):")
    print(report_html[:500] + "...")
    
    print("\n✅ Filtering report generation test passed!")
    return report_html

def test_full_digest_email():
    """Test full digest email generation with all features"""
    print("\n" + "="*60)
    print("Testing Full Digest Email Generation")
    print("="*60)
    
    date_str = "2025-12-15"
    html_content, text_content = generate_digest_email(sample_leads, date_str, sample_filtering_stats)
    
    # Verify HTML contains all expected elements
    assert "Daily Lead Digest" in html_content, "Missing title"
    assert "test_user_1" in html_content, "Missing lead 1"
    assert "test_user_2" in html_content, "Missing lead 2"
    assert "Filtering Performance Report" in html_content, "Missing filtering report section"
    assert "CSV file attached" in html_content, "Missing CSV attachment mention"
    
    print("\nGenerated HTML Email (first 1000 chars):")
    print(html_content[:1000] + "...")
    
    print("\n✅ Full digest email generation test passed!")
    return html_content, text_content

def save_sample_data_for_manual_testing():
    """Save sample data files for manual testing"""
    print("\n" + "="*60)
    print("Saving Sample Data Files for Manual Testing")
    print("="*60)
    
    # Save sample leads
    date_str = "2025-12-15"
    leads_file = f"english_leads_{date_str}.json"
    with open(leads_file, 'w', encoding='utf-8') as f:
        json.dump(sample_leads, f, indent=2, ensure_ascii=False)
    print(f"✅ Created {leads_file}")
    
    # Save sample filtering stats
    stats_file = f"filtering_stats_{date_str}.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(sample_filtering_stats, f, indent=2, ensure_ascii=False)
    print(f"✅ Created {stats_file}")
    
    print(f"\n📧 To test the full email sending, run:")
    print(f"   python send_daily_digest.py --date {date_str}")
    print(f"\n⚠️ Note: Make sure EMAIL_ADDRESS and SMTP2GO_API_KEY are set in your .env file")

if __name__ == "__main__":
    print("\n🧪 Testing New Digest Features\n")
    
    try:
        # Run tests
        csv_result = test_csv_generation()
        report_result = test_filtering_report()
        html_result, text_result = test_full_digest_email()
        
        # Save sample data
        save_sample_data_for_manual_testing()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nNew Features Implemented:")
        print("1. ✅ CSV generation with name, content, profile_link")
        print("2. ✅ Filtering statistics tracking by subreddit")
        print("3. ✅ Filtering report with percentages at each stage")
        print("4. ✅ Sample filtered content (up to 3 per stage)")
        print("5. ✅ Beautiful HTML email with report and CSV attachment")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        raise

