"""
Quick test to verify the fast path optimization works
Tests the regex patterns without importing heavy dependencies
"""
import time
import re

# Copy the patterns from ask_questions.py
SIMPLE_PATTERNS = [
    r'^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|howdy)(\s+(there|everyone))?[\s!.?]*$',
    r'^(how\s+are\s+you|what\'?s\s+up|sup)[\s!.?]*$',
    r'^(thanks?|thank\s+you|thx)[\s!.?]*$',
    r'^(bye|goodbye|see\s+you|later)[\s!.?]*$',
    r'^(yes|no|ok|okay|sure|alright)[\s!.?]*$',
]

def is_simple_query(query: str) -> bool:
    """Check if query is a simple greeting/conversational phrase"""
    query_lower = query.lower().strip()
    for pattern in SIMPLE_PATTERNS:
        if re.match(pattern, query_lower):
            return True
    return False

# Test queries (query, expected_result)
test_queries = [
    ("hi", True),
    ("hello", True),
    ("Hi!", True),
    ("Hello there", True),
    ("good morning", True),
    ("thank you", True),
    ("thanks", True),
    ("bye", True),
    ("how are you", True),
    ("what is diabetes?", False),
    ("explain my lab results", False),
    ("tell me about my medication", False),
    ("what does this medical term mean", False),
]

print("=" * 70)
print("FAST PATH OPTIMIZATION TEST - Pattern Matching")
print("=" * 70)

total_time = 0
passed = 0
failed = 0

for query, expected_simple in test_queries:
    start = time.time()
    is_simple = is_simple_query(query)
    elapsed_ms = (time.time() - start) * 1000
    total_time += elapsed_ms
    
    if is_simple == expected_simple:
        status = "✓ PASS"
        passed += 1
    else:
        status = "✗ FAIL"
        failed += 1
    
    print(f"{status} | '{query:35s}' | Simple: {str(is_simple):5s} | {elapsed_ms:.3f}ms")

avg_time = total_time / len(test_queries)

print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed")
print(f"Average pattern matching time: {avg_time:.3f}ms")
print("=" * 70)
print("\n✓ Fast path should:")
print("  - Match simple greetings instantly (<1ms)")
print("  - Skip full LLM path for greetings")
print("  - Return immediate lightweight responses")
print("  - Keep chat interaction responsive")
print("=" * 70)
