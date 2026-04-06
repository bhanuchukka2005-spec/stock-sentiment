# test_model.py
# This file is just for testing — we'll delete it after

from model import analyze_sentiment, analyze_batch

# Test 1: single headline
print("Test 1 — single headline")
result = analyze_sentiment("Apple reports record quarterly revenue, beating all estimates")
print(result)
print()

# Test 2: negative headline
print("Test 2 — negative headline")
result = analyze_sentiment("Tesla misses earnings badly, shares tumble 10% after hours")
print(result)
print()

# Test 3: neutral headline
print("Test 3 — neutral headline")
result = analyze_sentiment("Federal Reserve holds interest rates steady at current levels")
print(result)
print()

# Test 4: batch of headlines (what we'll use in real analysis)
print("Test 4 — batch of 3 headlines")
headlines = [
    "Strong job numbers boost market confidence",
    "Inflation fears grip investors as prices rise sharply",
    "Markets remain flat ahead of Fed announcement",
]
results = analyze_batch(headlines)
for headline, result in zip(headlines, results):
    print(f"  '{headline[:50]}...' → {result['label']} ({result['confidence']*100:.1f}%)")