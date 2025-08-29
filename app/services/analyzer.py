# --- Day 2: NLP Analyzer with HuggingFace ---
from transformers import pipeline
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
import os
from openai import OpenAI
from . import db

load_dotenv()

client = genai.Client()


# Thresholds for Green/Yellow/Red labels based on model confidence
CONFIDENCE_THRESHOLDS = {
    "high": 0.80,    # Score > 0.80 = very confident
    "medium": 0.65   # Score between 0.65-0.80 = moderately confident
}

MODEL = "jy46604790/Fake-News-Bert-Detect"
clf = pipeline("text-classification", model=MODEL, tokenizer=MODEL)


async def get_detailed_explanation(text: str, label: str) -> str:
    """
    Get a detailed explanation from the external LLM on why the text 
    might be reliable or not
    """

    try:
        # Build the prompt according to the label
        if label == "Green":
            prompt = f"""Analyze this text and explain why it appears to be reliable/true information. 
            Identify elements that reinforce its credibility (sources, structure, coherence, etc.).
            
            Text: "{text}"
            
            Provide a short and precise explanation (2-3 sentences max) on the reasons for reliability."""

        elif label == "Red":
            prompt = f"""Analyze this text and explain why it could be disinformation or fake news.
            Identify warning signs (unsourced claims, excessive emotional language, inconsistencies, etc.).
            
            Text: "{text}"
            
            Provide a short and precise explanation (2-3 sentences max) on the reasons for suspicion."""

        else:  # Yellow
            prompt = f"""Analyze this text and explain why its authenticity is difficult to determine.
            Identify ambiguous elements that require additional verification.
            
            Text: "{text}"
            
            Provide a short and precise explanation (2-3 sentences max) on why we should remain cautious."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"You are a fact-checking expert. Respond concisely and factually. {prompt}",
        )

        print(response.text)
        return response.text

    except Exception as e:
        print(f"⚠️ Error during LLM call: {e}")
        return ""


def interpret_model_result(result: list) -> Dict[str, Any]:
    """
    Interpret the HuggingFace model result
    LABEL_0: Fake news, LABEL_1: Real news
    The score represents the model's CONFIDENCE in its prediction (0-1)
    Expected format: [{'label': 'LABEL_1', 'score': 0.9994995594024658}]
    """
    if not result or len(result) == 0:
        return {
            "score": 0.5,
            "label": "Yellow",
            "explanation": "Analysis error",
            "confidence": "low"
        }

    prediction = result[0]
    model_label = prediction['label']
    model_confidence = prediction['score']  # Model confidence (0-1)

    # Determine the model's prediction
    is_fake_prediction = (model_label == "LABEL_0")
    is_real_prediction = (model_label == "LABEL_1")

    # Calculate the final score for our system (0 = fake, 1 = real)
    if is_real_prediction:
        # The model thinks it's real with X% confidence
        final_score = 0.5 + (model_confidence - 0.5)  # Scale from 0.5 to 1
    else:  # is_fake_prediction
        # The model thinks it's fake with X% confidence
        final_score = 0.5 - (model_confidence - 0.5)  # Scale from 0.5 to 0

    # Ensure the score stays between 0 and 1
    final_score = max(0.0, min(1.0, final_score))

    # Determine the overall confidence level
    if model_confidence >= CONFIDENCE_THRESHOLDS["high"]:
        confidence = "high"
    elif model_confidence >= CONFIDENCE_THRESHOLDS["medium"]:
        confidence = "medium"
    else:
        confidence = "low"

    # Determine the label based on the final score
    if final_score >= 0.75:
        label = "Green"
    elif final_score >= 0.4:
        label = "Yellow"
    else:
        label = "Red"

    return {
        "score": round(final_score, 2),
        "label": label,
        "confidence": confidence,
        "model_details": {
            "model_label": model_label,
            "model_confidence": round(model_confidence, 3),
            "prediction": "fake_news" if is_fake_prediction else "real_news"
        }
    }


async def analyze_with_huggingface(text: str) -> Dict[str, Any]:
    """Analyze text with the HuggingFace model (fake news detection)"""
    try:
        # Analysis with the local model
        result = clf(text)
        print(text)
        print(f"🔍 Model result: {result}")

        # Interpret the result
        interpreted_result = interpret_model_result(result)

        detailed_explanation = await get_detailed_explanation(
            text,
            interpreted_result["label"],
        )

        return {
            **interpreted_result,
            "explanation": detailed_explanation,
            "api_available": True
        }

    except Exception as e:
        print(f"⚠️  Model error: {e}")
        return {
            "score": 0.5,
            "label": "Yellow",
            "explanation": "Error during AI analysis",
            "confidence": "low",
            "api_available": False
        }


async def analyze_text(text: str) -> Dict[str, Any]:
    """
    Main text analysis function
    Uses the HuggingFace model to detect fake news
    """
    # Basic verification
    if not text or len(text.strip()) < 10:
        return {
            "score": 0.5,
            "label": "Yellow",
            "explanation": "Text too short for reliable analysis",
            "confidence": "low",
            "model_details": None
        }

    # Analysis with the AI model
    result = await analyze_with_huggingface(text)

    return result


def calculate_community_score(votes_data: Dict[str, int]) -> float:
    """Calculate community score from votes (0-1 scale)"""
    total = votes_data.get('total', 0)
    positive = votes_data.get('positive', 0)

    if total == 0:
        return 0.5  # Neutral if no votes

    return positive / total


def get_user_reputation_weight(user_id: str) -> float:
    """Simple reputation based on number of votes made (0.5-1.0 scale)"""
    user_votes = db.get_user_vote_count(user_id)

    # Simple formula: more votes = higher weight (max 1.0, min 0.5)
    weight = 0.5 + min(user_votes * 0.05, 0.5)
    return weight


def calculate_combined_score(ai_score: float, community_score: float, vote_count: int) -> Dict[str, Any]:
    """Combine AI and community scores with simple weighting"""

    # Weight based on number of community votes
    if vote_count == 0:
        # Only AI score
        final_score = ai_score
        weight_ai = 1.0
        weight_community = 0.0
    elif vote_count < 5:
        # Mostly AI, some community
        weight_ai = 0.7
        weight_community = 0.3
    elif vote_count < 20:
        # Balanced
        weight_ai = 0.5
        weight_community = 0.5
    else:
        # More community weight for popular articles
        weight_ai = 0.3
        weight_community = 0.7

    final_score = (ai_score * weight_ai) + (community_score * weight_community)

    # Determine final label
    if final_score >= 0.7:
        label = "Green"
    elif final_score >= 0.4:
        label = "Yellow"
    else:
        label = "Red"

    return {
        "combined_score": round(final_score, 2),
        "combined_label": label,
        "weights": {
            "ai": weight_ai,
            "community": weight_community
        },
        "vote_count": vote_count
    }
