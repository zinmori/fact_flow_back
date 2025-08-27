# --- Jour 2 : NLP Analyzer avec HuggingFace ---
from transformers import pipeline
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Seuils pour les labels Green/Yellow/Red basés sur la confiance du modèle
CONFIDENCE_THRESHOLDS = {
    "high": 0.85,    # Score > 0.85 = très confiant
    "medium": 0.65   # Score entre 0.65-0.85 = moyennement confiant
}

MODEL = "jy46604790/Fake-News-Bert-Detect"
clf = pipeline("text-classification", model=MODEL, tokenizer=MODEL)


def interpret_model_result(result: list) -> Dict[str, Any]:
    """
    Interpréter le résultat du modèle HuggingFace
    LABEL_0: Fake news, LABEL_1: Real news
    Le score représente la CONFIANCE du modèle en sa prédiction (0-1)
    Format attendu: [{'label': 'LABEL_1', 'score': 0.9994995594024658}]
    """
    if not result or len(result) == 0:
        return {
            "score": 0.5,
            "label": "Yellow",
            "explanation": "Erreur d'analyse",
            "confidence": "low"
        }

    prediction = result[0]
    model_label = prediction['label']
    model_confidence = prediction['score']  # Confiance du modèle (0-1)

    # Déterminer la prédiction du modèle
    is_fake_prediction = (model_label == "LABEL_0")
    is_real_prediction = (model_label == "LABEL_1")

    # Calculer le score final pour notre système (0 = fake, 1 = real)
    if is_real_prediction:
        # Le modèle pense que c'est real avec X% de confiance
        final_score = 0.5 + (model_confidence - 0.5)  # Scale de 0.5 à 1
    else:  # is_fake_prediction
        # Le modèle pense que c'est fake avec X% de confiance
        final_score = 0.5 - (model_confidence - 0.5)  # Scale de 0.5 à 0

    # S'assurer que le score reste entre 0 et 1
    final_score = max(0.0, min(1.0, final_score))

    # Déterminer le niveau de confiance global
    if model_confidence >= CONFIDENCE_THRESHOLDS["high"]:
        confidence = "high"
    elif model_confidence >= CONFIDENCE_THRESHOLDS["medium"]:
        confidence = "medium"
    else:
        confidence = "low"

    # Déterminer le label et l'explication basés sur le score final et la confiance
    if final_score >= 0.75:
        label = "Green"
        if confidence == "high":
            explanation = f"Source très fiable (confiance: {model_confidence:.0%})"
        else:
            explanation = f"Source probablement fiable (confiance: {model_confidence:.0%})"
    elif final_score >= 0.4:
        label = "Yellow"
        if confidence == "low":
            explanation = f"Résultat incertain, confiance faible ({model_confidence:.0%})"
        else:
            explanation = f"Source à vérifier (confiance: {model_confidence:.0%})"
    else:
        label = "Red"
        if confidence == "high":
            explanation = f"Contenu très probablement faux (confiance: {model_confidence:.0%})"
        else:
            explanation = f"Source douteuse (confiance: {model_confidence:.0%})"

    return {
        "score": round(final_score, 2),
        "label": label,
        "explanation": explanation,
        "confidence": confidence,
        "model_details": {
            "model_label": model_label,
            "model_confidence": round(model_confidence, 3),
            "prediction": "fake_news" if is_fake_prediction else "real_news"
        }
    }


async def analyze_with_huggingface(text: str) -> Dict[str, Any]:
    """Analyser le texte avec le modèle HuggingFace (fake news detection)"""
    try:
        # Analyse avec le modèle local
        result = clf(text)
        print(text)
        print(f"🔍 Résultat modèle: {result}")

        # Interpréter le résultat
        interpreted_result = interpret_model_result(result)

        return {
            **interpreted_result,
            "api_available": True
        }

    except Exception as e:
        print(f"⚠️  Erreur modèle: {e}")
        return {
            "score": 0.5,
            "label": "Yellow",
            "explanation": "Erreur lors de l'analyse IA",
            "confidence": "low",
            "api_available": False
        }


async def analyze_text(text: str) -> Dict[str, Any]:
    """
    Fonction principale d'analyse de texte
    Utilise le modèle HuggingFace pour détecter les fake news
    """
    # Vérification de base
    if not text or len(text.strip()) < 10:
        return {
            "score": 0.5,
            "label": "Yellow",
            "explanation": "Texte trop court pour une analyse fiable",
            "confidence": "low",
            "model_details": None
        }

    # Analyse avec le modèle IA
    result = await analyze_with_huggingface(text)

    return result
