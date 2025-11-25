"""
Unit tests for the heuristic classifier.
Tests with labeled examples to ensure classification accuracy.
"""

import pytest
from app.classifier import classify_text, classify_post_heuristic


class TestHeuristicClassifier:
    """Test suite for heuristic-based buyer classification."""
    
    # Test cases with expected classifications
    # Format: (text, expected_is_buyer, description)
    LABELED_EXAMPLES = [
        # Clear buyer intent - should be TRUE
        (
            "Looking for a web developer to build my e-commerce site. Budget is $5000.",
            True,
            "Explicit hiring request with budget"
        ),
        (
            "Need help finding a good CRM software for my small business. Any recommendations?",
            True,
            "Seeking recommendations"
        ),
        (
            "Where can I find affordable logo design services?",
            True,
            "Question about finding services"
        ),
        (
            "I want to buy a used MacBook Pro. What's the best place to look?",
            True,
            "Buying intent with question"
        ),
        (
            "Searching for a reliable SEO consultant for long-term engagement.",
            True,
            "Searching for service provider"
        ),
        (
            "Can anyone recommend a good project management tool? We need something for 10-15 people.",
            True,
            "Recommendation request with context"
        ),
        (
            "Hiring: Looking for Python developer with Django experience for 3-month contract",
            True,
            "Job posting/hiring"
        ),
        
        # Clear promotional/seller intent - should be FALSE
        (
            "I'm offering web development services at competitive prices. DM me for portfolio!",
            False,
            "Explicit service promotion"
        ),
        (
            "Check out my new SaaS product! 50% off for the first 100 customers. Link in bio.",
            False,
            "Promotional with discount"
        ),
        (
            "We are launching our new marketing agency. Visit our website for a free consultation.",
            False,
            "Business launch promotion"
        ),
        (
            "My company provides SEO services. PM me if interested in boosting your rankings!",
            False,
            "Direct sales pitch"
        ),
        (
            "Affiliate opportunity: Earn 30% commission selling our software. Click here to join!",
            False,
            "Affiliate/referral promotion"
        ),
        
        # Neutral/ambiguous - likely FALSE (no clear buyer signals)
        (
            "Just wanted to share my experience with Product X. It's been great!",
            False,
            "Neutral review/testimonial"
        ),
        (
            "Has anyone tried Service Y? I'm curious about it.",
            True,  # This could be buyer intent (researching before purchase)
            "Curiosity/research question"
        ),
        (
            "What do you think about the new pricing model for Z?",
            False,
            "Discussion question without clear intent"
        ),
    ]
    
    @pytest.mark.parametrize("text,expected_is_buyer,description", LABELED_EXAMPLES)
    def test_labeled_examples(self, text, expected_is_buyer, description):
        """Test classifier against labeled examples."""
        is_buyer, score, reason = classify_text(text)
        
        assert is_buyer == expected_is_buyer, (
            f"Failed on: {description}\n"
            f"Text: {text}\n"
            f"Expected: {expected_is_buyer}, Got: {is_buyer}\n"
            f"Score: {score}, Reason: {reason}"
        )
    
    def test_empty_text(self):
        """Test that empty text is classified as not buyer."""
        is_buyer, score, reason = classify_text("")
        assert is_buyer == False
        assert score == 0.0
    
    def test_short_text(self):
        """Test that very short text is classified as not buyer."""
        is_buyer, score, reason = classify_text("Hello")
        assert is_buyer == False
    
    def test_buyer_patterns(self):
        """Test that buyer keywords increase classification score."""
        buyer_text = "I need to hire someone for this project"
        is_buyer, score, reason = classify_text(buyer_text)
        assert is_buyer == True
        assert score > 0.2
    
    def test_promotional_patterns(self):
        """Test that promotional keywords decrease classification score."""
        promo_text = "I'm selling my services. Check out my website for 20% discount!"
        is_buyer, score, reason = classify_text(promo_text)
        assert is_buyer == False
    
    def test_mixed_signals(self):
        """Test text with both buyer and promotional signals."""
        # Promotional signals should dominate
        mixed_text = "Looking for clients! I'm offering web design services at great prices. DM me!"
        is_buyer, score, reason = classify_text(mixed_text)
        assert is_buyer == False  # Promotional signals should prevent buyer classification
    
    def test_metadata_link_penalty(self):
        """Test that excessive links reduce buyer score."""
        text = "Where can I find good hosting?"
        metadata_no_links = {"num_links": 0}
        metadata_many_links = {"num_links": 5}
        
        is_buyer_1, score_1, _ = classify_text(text, metadata_no_links)
        is_buyer_2, score_2, _ = classify_text(text, metadata_many_links)
        
        # Score should be lower with more links (spam indicator)
        assert score_2 < score_1
    
    def test_classify_post_heuristic(self):
        """Test the classify_post_heuristic function with title and body."""
        title = "Looking for a freelance designer"
        body = "I need someone to create a logo and brand identity. Budget: $500-1000"
        
        is_buyer, score, reason = classify_post_heuristic(title, body)
        
        assert is_buyer == True
        assert score > 0.3  # Should have high confidence
    
    def test_title_weighted_more(self):
        """Test that title is weighted more heavily than body."""
        # Title has buyer intent
        title1 = "Hiring web developer"
        body1 = "Some general text here"
        
        # Body has buyer intent but title doesn't
        title2 = "General discussion"
        body2 = "I'm looking to hire a web developer"
        
        _, score1, _ = classify_post_heuristic(title1, body1)
        _, score2, _ = classify_post_heuristic(title2, body2)
        
        # Title-based should score higher (title is repeated in combined text)
        assert score1 >= score2


class TestClassifierEdgeCases:
    """Test edge cases and error handling."""
    
    def test_none_title_and_body(self):
        """Test handling of None values."""
        is_buyer, score, reason = classify_post_heuristic(None, None)
        assert is_buyer == False
        assert score == 0.0
    
    def test_unicode_text(self):
        """Test that unicode text is handled correctly."""
        text = "Looking for développeur web 开发者 मदद"
        is_buyer, score, reason = classify_text(text)
        # Should not crash and should detect "looking for"
        assert is_buyer == True
    
    def test_case_insensitivity(self):
        """Test that classification is case-insensitive."""
        text1 = "LOOKING FOR WEB DEVELOPER"
        text2 = "looking for web developer"
        
        is_buyer1, score1, _ = classify_text(text1)
        is_buyer2, score2, _ = classify_text(text2)
        
        assert is_buyer1 == is_buyer2
        assert abs(score1 - score2) < 0.01  # Scores should be very similar


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
