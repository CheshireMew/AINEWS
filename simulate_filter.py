
import sys
import os
import logging

sys.path.insert(0, os.path.abspath('crawler'))
from filters.keyword_filter import KeywordFilter

def simulate_filter():
    input_file = 'titles.txt'
    output_file = 'filter_simulation_report.txt'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return

    # Load filter (uses updated filters.yaml)
    kf = KeywordFilter()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        titles = [line.strip() for line in f if line.strip()]

    blocked = []
    passed = []

    print(f"Loaded {len(titles)} titles. Applying filters...")

    for title in titles:
        # Mock news item
        news = {'title': title, 'content': ''}
        result = kf.filter_news(news)
        
        if result['passed']:
            passed.append((title, result['reason']))
        else:
            blocked.append((title, result['reason']))

    # Write report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"=== Filter Simulation Report ===\n")
        f.write(f"Total: {len(titles)}\n")
        f.write(f"Passed: {len(passed)}\n")
        f.write(f"Blocked: {len(blocked)}\n\n")
        
        f.write("--- BLOCKED TITLES (Check for False Positives) ---\n")
        for t, r in blocked:
            f.write(f"[×] {t}\n    Reason: {r}\n")
            
        f.write("\n--- PASSED TITLES ---\n")
        for t, r in passed:
            f.write(f"[√] {t}\n    Reason: {r}\n")

    print(f"Simulation done. Blocked {len(blocked)} titles.")
    print(f"Check {output_file} for details.")

if __name__ == "__main__":
    simulate_filter()
