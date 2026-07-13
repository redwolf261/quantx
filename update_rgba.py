import os
import re

CSS_FILE = r"c:\Users\Rivan\Downloads\FutureLens\frontend\src\app\globals.css"

REPLACEMENTS = {
    r"139,\s*92,\s*246": "20, 184, 166",   # violet-500 -> teal-500
    r"109,\s*40,\s*217": "15, 118, 110",   # violet-700 -> teal-700
    r"%238b5cf6": "%23f97316",             # violet-500 hex in SVG -> orange-500
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    for pattern, replacement in REPLACEMENTS.items():
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

process_file(CSS_FILE)
print("RGBA color update complete!")
