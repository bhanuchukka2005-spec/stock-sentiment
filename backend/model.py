# model.py

# pipeline is a HuggingFace helper that bundles the tokenizer + model together
# so we don't have to manage them separately
from transformers import pipeline

# torch is the engine that actually runs the math inside the model
import torch

# We'll use this to cache the model so we don't reload it on every request
_sentiment_pipeline = None

def get_model():
    """
    Load FinBERT model. 
    
    The first time this runs, it downloads the model from HuggingFace (~500MB).
    After that it's cached on your computer — instant load.
    
    We use a global variable so the model loads ONCE when the server starts,
    not on every single API request. Loading a model takes ~3 seconds.
    Inference (using it) takes ~0.1 seconds.
    """
    global _sentiment_pipeline
    
    # If already loaded, just return it — don't reload
    if _sentiment_pipeline is not None:
        return _sentiment_pipeline
    
    print("Loading FinBERT model... (first time takes ~30 seconds)")
    
    # "ProsusAI/finbert" is the model ID on HuggingFace
    # task = "text-classification" means: given text, return a label
    # top_k=None means: return scores for ALL labels (negative/neutral/positive)
    #   not just the top one — we want all three scores
    _sentiment_pipeline = pipeline(
        task="text-classification",
        model="ProsusAI/finbert",
        top_k=None,
        # Use GPU if available, otherwise CPU
        # For now your laptop CPU is fine
        device=0 if torch.cuda.is_available() else -1,
    )
    
    print("FinBERT loaded successfully")
    return _sentiment_pipeline


def analyze_sentiment(text: str) -> dict:
    """
    Run sentiment analysis on a single piece of text.
    
    Input:  "Apple reports record quarterly revenue"
    Output: {
        "label": "positive",
        "scores": {
            "positive": 0.94,
            "negative": 0.02,
            "neutral": 0.04
        },
        "confidence": 0.94
    }
    """
    model = get_model()
    
    # Run the model — this is the actual inference step
    # results is a list of lists because pipeline can handle batches
    # results[0] = scores for our single input
    results = model(text)[0]
    
    # results looks like:
    # [
    #   {"label": "positive", "score": 0.94},
    #   {"label": "negative", "score": 0.02},
    #   {"label": "neutral",  "score": 0.04}
    # ]
    
    # Convert to a cleaner dictionary format
    scores = {item["label"]: round(item["score"], 4) for item in results}
    
    # Find which label has the highest score
    best_label = max(scores, key=scores.get)
    
    return {
        "label": best_label,
        "scores": scores,
        "confidence": scores[best_label],
    }


def analyze_batch(texts: list[str]) -> list[dict]:
    """
    Analyze multiple headlines at once.
    Batch processing is faster than calling analyze_sentiment() in a loop
    because the model processes them in parallel internally.
    """
    model = get_model()
    
    # Run all texts through the model at once
    batch_results = model(texts)
    
    output = []
    for results in batch_results:
        scores = {item["label"]: round(item["score"], 4) for item in results}
        best_label = max(scores, key=scores.get)
        output.append({
            "label": best_label,
            "scores": scores,
            "confidence": scores[best_label],
        })
    
    return output