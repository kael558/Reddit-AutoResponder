#!/usr/bin/env python3
"""
Test script to verify the improved filtering logic
"""

# Test cases - should be REJECTED
test_cases_reject = [
    "Which is totally representative of an entire population and 100% not an isolated case of one person being an asshole.",
    "I heard something recently that if you get stuck it's generally due to two things. 1) you're too deep in the story and need to step back. You can't see the forest for the trees, so your mind is too...",
    "In my opinion, English grammar is quite complex compared to other languages.",
    "You should try watching movies with subtitles to improve your listening skills.",
    "Research shows that immersion is the best way to learn a language.",
    "From a linguistic perspective, English has many irregularities."
]

# Test cases - should be ACCEPTED
test_cases_accept = [
    "I need someone to practice speaking English with. Anyone interested?",
    "I'm looking for a conversation partner to improve my English speaking skills.",
    "How can I practice English speaking? I'm too shy to talk to people.",
    "Looking for English discord server where I can practice speaking.",
    "Does anyone know good apps for English speaking practice?",
    "I want to practice English conversation but I'm nervous about it.",
    "Anyone want to be my English study buddy? I need speaking practice.",
    "Where can I find English conversation partners online?",
    "Help me find ways to practice speaking English confidently.",
    "I am looking for English practice group to join."
]

def test_filtering_logic():
    """Test the filtering logic"""
    
    # Simulate the keyword filtering logic
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
    
    seeking_indicators = [
        'i need', 'i want', 'i am looking', 'i\'m looking', 'looking for',
        'how can i', 'where can i', 'how do i', 'where do i', 'help me',
        'anyone know', 'does anyone', 'can someone', 'recommendations for',
        'suggestions for', 'advice on', 'tips for'
    ]
    
    def should_accept(text):
        """Test if text should be accepted"""
        text_lower = text.lower()
        
        # First check: has practice-seeking keywords
        has_practice_keywords = any(keyword in text_lower for keyword in practice_seeking_keywords)
        if not has_practice_keywords:
            return False, "No practice keywords"
        
        # Second check: no negative keywords
        has_negative = any(neg_keyword in text_lower for neg_keyword in negative_keywords)
        if has_negative:
            return False, "Has negative keywords"
        
        # Third check: has seeking language
        has_seeking = any(indicator in text_lower for indicator in seeking_indicators)
        if not has_seeking:
            return False, "No seeking language"
        
        return True, "Accepted"
    
    print("=== TESTING FILTERING LOGIC ===\n")
    
    print("📋 Testing REJECT cases (should all be rejected):")
    reject_correct = 0
    for i, text in enumerate(test_cases_reject, 1):
        should_accept_result, reason = should_accept(text)
        status = "❌ REJECTED" if not should_accept_result else "✅ ACCEPTED (ERROR!)"
        print(f"{i}. {status} - {reason}")
        print(f"   Text: {text[:80]}{'...' if len(text) > 80 else ''}")
        if not should_accept_result:
            reject_correct += 1
        print()
    
    print(f"Reject accuracy: {reject_correct}/{len(test_cases_reject)} ({reject_correct/len(test_cases_reject)*100:.1f}%)\n")
    
    print("📋 Testing ACCEPT cases (should all be accepted):")
    accept_correct = 0
    for i, text in enumerate(test_cases_accept, 1):
        should_accept_result, reason = should_accept(text)
        status = "✅ ACCEPTED" if should_accept_result else "❌ REJECTED (ERROR!)"
        print(f"{i}. {status} - {reason}")
        print(f"   Text: {text[:80]}{'...' if len(text) > 80 else ''}")
        if should_accept_result:
            accept_correct += 1
        print()
    
    print(f"Accept accuracy: {accept_correct}/{len(test_cases_accept)} ({accept_correct/len(test_cases_accept)*100:.1f}%)")
    
    total_correct = reject_correct + accept_correct
    total_cases = len(test_cases_reject) + len(test_cases_accept)
    print(f"\n🎯 OVERALL ACCURACY: {total_correct}/{total_cases} ({total_correct/total_cases*100:.1f}%)")

if __name__ == "__main__":
    test_filtering_logic()
