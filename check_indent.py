
import sys

def check_indent(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped: continue
        indent = len(line) - len(stripped)
        if indent % 4 != 0:
            print(f"Line {i+1} has irregular indentation ({indent} spaces): {stripped.strip()}")
            # print(f"  Line content: {repr(line)}")

if __name__ == "__main__":
    check_indent("crawler/database/db_sqlite.py")
