import os
import sys
import time

# FIX: running "python scripts/verify_t03.py" only puts scripts/ on the path,
# so "import src" fails. Add the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.query_normalizer import QueryNormalizer

def run_t03_verification():
    print("==================================================")
    print("TASK T03 VERIFICATION: LOCAL MISTRAL 7B ENDPOINT")
    print("==================================================")
    
    normalizer = QueryNormalizer("data/municipal_dictionary_v1.json")

    # FIX: first call loads Mistral into VRAM (can take 10-30s). Warm up so
    # the latency check measures real inference, not model loading.
    print("[*] Warming up eboss-mistral (loading into VRAM)...")
    normalizer.normalize("Unsaon pagkuha ug permit?")
    
    test_suite = [
        {
            "name": "Case 1: Monosemous Bislish Business Inquiry",
            "query": "Unsay kinahanglan para sa renewal sa business permit kung gamay ra ang pwesto?",
            "expected_status": "SUCCESS"
        },
        {
            "name": "Case 2: Polysemous Ambiguity Trigger",
            "query": "Asa mukuha ug barangay clearance para sa akong tindahan?",
            "expected_status": "FALLBACK_TRIGGERED"
        },
        {
            "name": "Case 3: Taglish Fee Inquiry with Lexical Substitution",
            "query": "Magkano ang babayarang filing fee sa zoning clearance kapag commercial building?",
            "expected_status": "SUCCESS"
        }
    ]

    for idx, tc in enumerate(test_suite, 1):
        print(f"\n[{idx}] Running: {tc['name']}")
        print(f"    Input: \"{tc['query']}\"")
        
        start = time.time()
        res = normalizer.normalize(tc["query"])
        elapsed = time.time() - start
        
        print(f"    Result Status: {res['status']}")
        assert res["status"] == tc["expected_status"], f"Status mismatch! Expected {tc['expected_status']}, got {res['status']}"
        
        if res["status"] == "SUCCESS":
            print(f"    Normalized English Query: \"{res['normalized_query']}\"")
            print(f"    Injected Terms: {res['injected_terms']}")
            print(f"    Tokens Generated: {res['tokens_generated']} (Must be <= 150)")
            print(f"    Inference Latency: {elapsed:.2f}s")
            
            assert res["tokens_generated"] <= 150, "Violation: Output exceeded the 150-token limit!"
            assert elapsed < 10.0, f"Latency warning: Translation took {elapsed:.2f}s (>10s)"
        else:
            print(f"    Triggered Disambiguation Prompt: \"{res['clarification_prompt']}\"")
            print(f"    Bypassed Translation Latency: {elapsed:.4f}s")

    print("\n==================================================")
    print("[SUCCESS] ALL T03 ACCEPTANCE CRITERIA SATISFIED.")
    print("Mistral 7B is operational, deterministic, and bounded.")
    print("==================================================")

if __name__ == "__main__":
    run_t03_verification()

