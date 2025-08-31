# --- Fact-Flow Backend: AI-Powered Fact Checker with Gemini ---
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
import os
import re
from datetime import datetime
from . import db

load_dotenv()

client = genai.Client()

# Thresholds for Green/Yellow/Red labels based on analysis confidence
CONFIDENCE_THRESHOLDS = {
    "high": 0.80,    # Score > 0.80 = very confident
    "medium": 0.65   # Score between 0.65-0.80 = moderately confident
}


def clean_content(raw_content: str) -> str:
    """
    Clean and extract main content from raw text (inner text from web pages)
    Remove navigation, ads, footers, and other irrelevant content
    """
    try:
        # Clean up extra whitespace first
        content = re.sub(r'\s+', ' ', raw_content).strip()

        # Common patterns to remove (navigation, ads, etc.)
        patterns_to_remove = [
            # Navigation patterns
            r'Accueil.*?Contact',
            r'Menu.*?Rechercher',
            r'Navigation.*?principal',

            # Footer patterns
            r'Tous droits réservés.*?$',
            r'Copyright.*?$',
            r'©.*?\d{4}.*?$',

            # Ad patterns
            r'Publicité.*?',
            r'Annonce.*?',
            r'Sponsorisé.*?',

            # Cookie/GDPR patterns
            r'Nous utilisons des cookies.*?Accepter',
            r'Ce site utilise.*?cookies.*?',
            r'Politique de confidentialité.*?',

            # Social media patterns
            r'Partager sur.*?Facebook.*?Twitter.*?',
            r'Suivez-nous.*?',
            r'Abonnez-vous.*?',

            # Newsletter patterns
            r'S\'abonner.*?newsletter.*?',
            r'Recevez.*?actualités.*?',

            # Comment patterns
            r'Commentaires.*?Laisser.*?commentaire',
            r'\d+\s+commentaires?.*?',
        ]

        # Remove common unwanted patterns
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content,
                             flags=re.IGNORECASE | re.DOTALL)

        # Remove lines that are likely navigation or boilerplate
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if len(line) < 10:  # Skip very short lines
                continue

            # Skip lines that look like navigation
            nav_indicators = [
                'menu', 'navigation', 'accueil', 'contact', 'recherche',
                'connexion', 'inscription', 'mon compte'
            ]
            if any(indicator in line.lower() for indicator in nav_indicators) and len(line) < 50:
                continue

            # Skip lines that are likely timestamps without content
            if re.match(r'^\d{1,2}[:/]\d{1,2}[:/]\d{2,4}.*?$', line) and len(line) < 30:
                continue

            # Skip lines with only social media or sharing text
            social_patterns = ['partager', 'twitter',
                               'facebook', 'linkedin', 'whatsapp']
            if any(pattern in line.lower() for pattern in social_patterns) and len(line) < 30:
                continue

            cleaned_lines.append(line)

        # Rejoin and clean up
        cleaned_content = ' '.join(cleaned_lines)
        cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()

        # If content is too short after cleaning, return original (might be too aggressive)
        if len(cleaned_content) < len(content) * 0.3:
            return content

        return cleaned_content

    except Exception as e:
        print(f"Error cleaning content: {e}")
        return raw_content


async def analyze_with_gemini(content: str) -> Dict[str, Any]:
    """
    Analyze content using Gemini AI model for fact-checking
    Handles raw text content from web pages
    """
    try:
        # Clean the raw content to focus on main information
        cleaned_content = clean_content(content)

        # Get current date for context
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Build comprehensive prompt for fact-checking analysis
        prompt = f"""Tu es un expert en vérification des faits (fact-checker) professionnel. Tu dois analyser le contenu suivant et déterminer sa fiabilité.

CONTEXTE IMPORTANT:
- Date d'aujourd'hui: {current_date} (Ce n'est pas la date de l'article)
- Tu reçois le contenu textuel complet d'une page web qui peut contenir des éléments inutiles (menus, publicités, etc.)
- Concentre-toi sur l'article ou l'information principale
- Ignore les éléments de navigation, publicités, commentaires, etc.

CONTENU À ANALYSER:
{cleaned_content}

INSTRUCTIONS:
1. Identifie l'article ou information principale dans ce contenu
2. Évalue la fiabilité de cette information en analysant:
   - Sources citées et leur crédibilité
   - Cohérence des faits présentés
   - Présence de biais ou manipulation
   - Véracité des affirmations factuelles
   - Qualité du journalisme/rédaction
   - Contexte temporel et pertinence

3. Attribue un score de fiabilité de 0 à 1:
   - 0.0-0.39: Information probablement fausse/trompeuse (Rouge)
   - 0.4-0.74: Information incertaine, nécessite vérification (Jaune)  
   - 0.75-1.0: Information probablement fiable (Vert)

4. Fournis une explication claire et concise (2-3 phrases) justifiant ton évaluation

RÉPONSE REQUISE (format JSON):
{{
    "score": [score numérique entre 0 et 1],
    "label": "[Green/Yellow/Red]",
    "explanation": "[explication de 2-3 phrases]",
    "main_topic": "[sujet principal identifié]"
}}

Réponds uniquement avec le JSON, sans autres commentaires."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        print(f"🤖 Gemini analysis: {response.text}")

        # Parse JSON response
        import json
        try:
            # Clean the response text before parsing
            raw_response = response.text.strip()

            # Remove potential markdown code blocks if present
            if raw_response.startswith('```json'):
                raw_response = raw_response.replace(
                    '```json', '').replace('```', '').strip()
            elif raw_response.startswith('```'):
                raw_response = raw_response.replace('```', '').strip()

            # Try to extract JSON if it's embedded in other text
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_text = raw_response[json_start:json_end]
            else:
                json_text = raw_response

            print(f"🔍 Attempting to parse JSON: {json_text}")

            # Parse the JSON
            result = json.loads(json_text)

            # Validate and normalize the response
            score = float(result.get('score', 0.5))
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))

            label = result.get('label', 'Yellow')
            if label not in ['Green', 'Yellow', 'Red']:
                label = 'Yellow'

            explanation = result.get(
                'explanation', 'Analyse effectuée avec succès')
            main_topic = result.get('main_topic', 'Non spécifié')

            # Determine confidence based on score
            if score >= CONFIDENCE_THRESHOLDS["high"] or score <= (1 - CONFIDENCE_THRESHOLDS["high"]):
                confidence = "high"
            elif score >= CONFIDENCE_THRESHOLDS["medium"] or score <= (1 - CONFIDENCE_THRESHOLDS["medium"]):
                confidence = "medium"
            else:
                confidence = "low"

            print(f"✅ JSON parsing successful!")
            return {
                "score": round(score, 2),
                "label": label,
                "explanation": explanation,
                "confidence": confidence,
                "main_topic": main_topic,
                "api_available": True
            }

        except json.JSONDecodeError as e:
            print(f"❌ Error parsing Gemini JSON response: {e}")
            print(f"Raw response length: {len(response.text)}")
            print(f"Raw response (first 500 chars): {response.text[:500]}")
            print(f"Raw response (last 200 chars): {response.text[-200:]}")

            # Try alternative parsing approaches
            try:
                # Method 1: Try to fix common JSON issues
                fixed_text = response.text.strip()

                # Fix potential issues with quotes
                fixed_text = re.sub(
                    r'(?<!\\)"([^"]*)"(?=\s*:)', r'"\1"', fixed_text)

                # Try parsing again
                result = json.loads(fixed_text)

                score = float(result.get('score', 0.5))
                score = max(0.0, min(1.0, score))
                label = result.get('label', 'Yellow')
                explanation = result.get(
                    'explanation', 'Analyse effectuée avec parsing alternatif')

                print(f"✅ Alternative JSON parsing successful!")
                return {
                    "score": round(score, 2),
                    "label": label,
                    "explanation": explanation,
                    "confidence": "medium",
                    "api_available": True
                }

            except:
                print("❌ Alternative parsing also failed")

            # Fallback: try to extract information manually using regex
            print("🔄 Falling back to regex extraction...")
            text_response = response.text

            try:
                # Extract score using regex
                score_match = re.search(r'"score":\s*([0-9.]+)', text_response)
                score = float(score_match.group(1)) if score_match else 0.5

                # Extract label using regex
                label_match = re.search(
                    r'"label":\s*"(Green|Yellow|Red)"', text_response)
                label = label_match.group(1) if label_match else 'Yellow'

                # Extract explanation using regex
                explanation_match = re.search(
                    r'"explanation":\s*"([^"]+)"', text_response)
                explanation = explanation_match.group(
                    1) if explanation_match else "Analyse effectuée avec extraction regex"

                print(
                    f"✅ Regex extraction successful: score={score}, label={label}")
                return {
                    "score": round(score, 2),
                    "label": label,
                    "explanation": explanation,
                    "confidence": "medium",
                    "api_available": True
                }

            except Exception as regex_error:
                print(f"❌ Regex extraction failed: {regex_error}")

            # Final fallback: analyze text content
            text_lower = response.text.lower()

            if any(word in text_lower for word in ['fiable', 'vrai', 'green', 'crédible']):
                return {
                    "score": 0.8,
                    "label": "Green",
                    "explanation": "L'analyse Gemini suggère que le contenu est fiable (analyse textuelle).",
                    "confidence": "medium",
                    "api_available": True
                }
            elif any(word in text_lower for word in ['faux', 'trompeur', 'red', 'suspect']):
                return {
                    "score": 0.2,
                    "label": "Red",
                    "explanation": "L'analyse Gemini suggère que le contenu est suspect (analyse textuelle).",
                    "confidence": "medium",
                    "api_available": True
                }
            else:
                return {
                    "score": 0.5,
                    "label": "Yellow",
                    "explanation": "L'analyse Gemini nécessite une vérification supplémentaire (analyse textuelle).",
                    "confidence": "low",
                    "api_available": True
                }

    except Exception as e:
        print(f"⚠️ Erreur lors de l'analyse Gemini: {e}")
        return {
            "score": 0.5,
            "label": "Yellow",
            "explanation": "Erreur lors de l'analyse IA - vérification manuelle recommandée",
            "confidence": "low",
            "api_available": False
        }


async def analyze_text(content: str) -> Dict[str, Any]:
    """
    Main text analysis function
    Uses Gemini AI to analyze content for fact-checking
    Handles both HTML pages and plain text
    """
    # Basic verification
    if not content or len(content.strip()) < 10:
        return {
            "score": 0.5,
            "label": "Yellow",
            "explanation": "Contenu trop court pour une analyse fiable",
            "confidence": "low",
            "api_available": False
        }

    # Analysis with Gemini AI
    result = await analyze_with_gemini(content)

    return result


def get_article_with_community_data(article_id: str) -> Dict[str, Any]:
    """
    Get article analysis with community data (votes and scores)
    Returns None if article doesn't exist
    """
    # Get AI analysis
    ai_analysis = db.get_article_analysis(article_id)
    if not ai_analysis:
        return None

    # Get community votes
    votes_data = db.get_article_votes(article_id)

    # Calculate community score (None if no votes)
    community_score = None
    if votes_data['total'] > 0:
        community_score = calculate_community_score(votes_data)

    return {
        "article_id": article_id,
        "score": ai_analysis['score'],
        "label": ai_analysis['label'],
        "explanation": ai_analysis['explanation'],
        "community_score": community_score,
        "positive_votes": votes_data['positive'],
        "negative_votes": votes_data['negative'],
        "total_votes": votes_data['total']
    }


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
