"""
Classification logic for identifying buyer/prospect posts on Reddit.
Implements both heuristic (regex-based) and optional LLM-based classification.
"""

import re
import json
from typing import Tuple, Dict, Any, Optional
from datetime import datetime

from app.deps import get_settings


# ============================================================================
# HEURISTIC CLASSIFIER
# ============================================================================

# Positive patterns that indicate buyer/prospect intent
BUYER_PATTERNS = [
    r'\b(looking for|need|want|seeking|search(?:ing)? for|in need of|require)\b',
    r'\b(hire|hiring|recruit(?:ing)?|find (?:a|an|someone))\b',
    r'\b(buy(?:ing)?|purchase|purchas(?:ing)|shop(?:ping)? for)\b',
    r'\b(recommend(?:ation)?|suggest(?:ion)?|advice on)\b',
    r'\b(where (?:can|do|to)|how (?:can|do|to))\b.*\b(find|get|buy|hire)\b',
    r'\b(budget|price|cost|afford|pay(?:ing)?)\b',
    r'\b(help me|assist me|guide me)\b.*\b(find|choose|select)\b',
    r'\b(best|top|good|quality).*\b(service|product|provider|solution)\b',
]

# Negative patterns that indicate promotional/selling intent
PROMOTIONAL_PATTERNS = [
    r'\b(I am|I\'m|we are|we\'re)\b.*\b(sell(?:ing)?|offer(?:ing)?|provid(?:ing|e)|launch(?:ing)?)\b',
    r'\b(check out|visit|click|link in bio|DM me|PM me)\b',
    r'\b(discount|sale|promo|coupon|limited time|special offer)\b',
    r'\b(my (business|service|product|company|website|store))\b',
    r'\b(affiliate|referral|commission)\b',
    r'\b(\d+% off|free shipping|money back)\b',
]

# Compile regex patterns for performance
BUYER_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in BUYER_PATTERNS]
PROMOTIONAL_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in PROMOTIONAL_PATTERNS]


def classify_text(text: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, str]:
    """
    Heuristic classifier that analyzes text to determine if it's a buyer/prospect post.
    
    Args:
        text: Combined title and body text to analyze
        metadata: Optional metadata (e.g., author account age, link count)
    
    Returns:
        Tuple of (is_buyer: bool, confidence_score: float, reason: str)
    """
    if not text or len(text.strip()) < 10:
        return False, 0.0, "Text too short to classify"
    
    text = text.lower()
    
    # Count matches for buyer patterns
    buyer_matches = sum(1 for pattern in BUYER_REGEX if pattern.search(text))
    
    # Count matches for promotional patterns
    promo_matches = sum(1 for pattern in PROMOTIONAL_REGEX if pattern.search(text))
    
    # Base score from pattern matches
    buyer_score = buyer_matches * 0.15
    promo_penalty = promo_matches * 0.25
    
    # Metadata-based adjustments (if available)
    # NOTE: These are placeholder heuristics - extend based on your domain
    if metadata:
        # Check for excessive links (spam indicator)
        link_count = metadata.get('num_links', 0)
        if link_count > 3:
            promo_penalty += 0.2
        
        # Account age heuristic (newer accounts more likely to be promotional)
        # This would require fetching author info from Reddit API
        account_age_days = metadata.get('author_account_age_days', 365)
        if account_age_days < 30 and promo_matches > 0:
            promo_penalty += 0.15
    
    # Calculate final score
    final_score = max(0.0, min(1.0, buyer_score - promo_penalty))
    
    # Decision threshold
    THRESHOLD = 0.25
    is_buyer = final_score >= THRESHOLD and buyer_matches > 0 and promo_matches == 0
    
    # Generate reason string
    reason_parts = []
    if buyer_matches > 0:
        reason_parts.append(f"{buyer_matches} buyer signal(s)")
    if promo_matches > 0:
        reason_parts.append(f"{promo_matches} promotional signal(s)")
    if not reason_parts:
        reason_parts.append("No clear signals detected")
    
    reason = "; ".join(reason_parts)
    
    return is_buyer, final_score, reason


def classify_post_heuristic(title: str, body: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, str]:
    """
    Classify a Reddit post using heuristic rules.
    
    Args:
        title: Post title
        body: Post body/selftext
        metadata: Optional metadata dict
    
    Returns:
        Tuple of (is_buyer: bool, confidence_score: float, reason: str)
    """
    # Combine title and body for analysis (title weighted more heavily)
    combined_text = f"{title or ''} {title or ''} {body or ''}"
    
    return classify_text(combined_text, metadata)


# ============================================================================
# LLM CLASSIFIER (Optional)
# ============================================================================

def llm_classify(title: str, body: str) -> Tuple[bool, float, str]:
    """
    Classify a post using LLM (OpenAI GPT).
    Only called when USE_LLM=true and for low-confidence heuristic results.
    
    Args:
        title: Post title
        body: Post body/selftext
    
    Returns:
        Tuple of (is_buyer: bool, confidence_score: float, reason: str)
    """
    settings = get_settings()
    
    if not settings.USE_LLM or not settings.OPENAI_API_KEY:
        return False, 0.0, "LLM disabled or API key missing"
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Construct deterministic prompt
        prompt = f"""You are a classifier that identifies buyer/prospect intent in Reddit posts.

Analyze the following Reddit post and determine if the author is looking to BUY, HIRE, or FIND a product/service (buyer intent), or if they are SELLING, PROMOTING, or ADVERTISING (not buyer intent).

Title: {title or 'N/A'}

Body: {body or 'N/A'}

Respond ONLY with valid JSON in this exact format:
{{
  "is_buyer": true or false,
  "confidence": 0.0 to 1.0,
  "reason": "brief explanation"
}}

Rules:
- is_buyer=true if the post shows intent to buy, hire, find, or seek recommendations
- is_buyer=false if the post is promotional, selling, or advertising
- confidence should reflect how certain you are (1.0 = very certain)
- reason should be a brief one-sentence explanation
"""
        
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise JSON-only classifier. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=settings.LLM_MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        is_buyer = result.get('is_buyer', False)
        confidence = float(result.get('confidence', 0.5))
        reason = result.get('reason', 'LLM classification')
        
        return is_buyer, confidence, f"LLM: {reason}"
        
    except Exception as e:
        # Fallback to heuristic on LLM error
        print(f"LLM classification error: {e}")
        return False, 0.0, f"LLM error: {str(e)}"


def classify_post(
    title: str, 
    body: str, 
    metadata: Optional[Dict[str, Any]] = None,
    force_llm: bool = False
) -> Tuple[bool, float, str, str]:
    """
    Main classification function with fallback logic.
    
    Strategy:
    1. Always run heuristic classifier first (fast, free)
    2. If USE_LLM=true and confidence is low (< 0.4), use LLM for final decision
    3. If force_llm=True, use LLM regardless of heuristic confidence
    
    Args:
        title: Post title
        body: Post body
        metadata: Optional metadata
        force_llm: Force LLM classification
    
    Returns:
        Tuple of (is_buyer: bool, confidence: float, reason: str, source: str)
        source will be 'heuristic', 'llm', or 'heuristic+llm'
    """
    settings = get_settings()
    
    # Step 1: Heuristic classification
    is_buyer_h, confidence_h, reason_h = classify_post_heuristic(title, body, metadata)
    
    # Step 2: Decide if LLM is needed
    use_llm = (
        settings.USE_LLM and 
        (force_llm or confidence_h < 0.4)  # Low confidence threshold
    )
    
    if not use_llm:
        return is_buyer_h, confidence_h, reason_h, "heuristic"
    
    # Step 3: LLM classification
    is_buyer_llm, confidence_llm, reason_llm = llm_classify(title, body)
    
    # If LLM succeeds, use its result
    if confidence_llm > 0.0:
        return is_buyer_llm, confidence_llm, reason_llm, "llm"
    
    # LLM failed, fall back to heuristic
    return is_buyer_h, confidence_h, f"{reason_h} (LLM unavailable)", "heuristic"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_metadata_from_submission(submission) -> Dict[str, Any]:
    """
    Extract useful metadata from a PRAW submission object.
    
    Args:
        submission: PRAW Submission object
    
    Returns:
        Dictionary with metadata fields
    """
    # Count URLs in the post
    url_pattern = re.compile(r'https?://\S+')
    body_text = submission.selftext or ""
    num_links = len(url_pattern.findall(body_text))
    
    metadata = {
        "score": submission.score,
        "num_comments": submission.num_comments,
        "num_links": num_links,
        "is_self": submission.is_self,
        "permalink": submission.permalink,
    }
    
    # TODO: Add author account age if needed
    # This requires an additional API call: submission.author.created_utc
    # For now, we'll skip it to avoid rate limits
    
    return metadata
