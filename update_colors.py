import os
import re

FRONTEND_DIR = r"c:\Users\Rivan\Downloads\FutureLens\frontend\src"

REPLACEMENTS = {
    # Tailwind classes
    r"violet-([0-9]+)": r"teal-\1",
    r"indigo-([0-9]+)": r"teal-\1",
    r"purple-([0-9]+)": r"teal-\1",
    r"badge-violet": "badge-teal",
    r"text-gradient-violet": "text-gradient-teal",
    
    # Specific gradients used often
    r"linear-gradient\(135deg,\s*#6d28d9,\s*#8b5cf6\)": r"linear-gradient(135deg, #0f766e, #f97316)",
    r"linear-gradient\(135deg,#6d28d9,#8b5cf6\)": r"linear-gradient(135deg,#0f766e,#f97316)",
    r"linear-gradient\(135deg,\s*#6d28d9,\s*#10b981\)": r"linear-gradient(135deg, #0f766e, #10b981)",
    r"linear-gradient\(135deg,#6d28d9,#10b981\)": r"linear-gradient(135deg,#0f766e,#10b981)",
    r"linear-gradient\(135deg,\s*#6d28d9,\s*#7c3aed\)": r"linear-gradient(135deg, #0f766e, #0d9488)",
    r"linear-gradient\(135deg,#6d28d9,#7c3aed\)": r"linear-gradient(135deg,#0f766e,#0d9488)",

    r"linear-gradient\(90deg,\s*#8b5cf6,\s*#6d28d9\)": r"linear-gradient(90deg, #f97316, #0f766e)",
    r"linear-gradient\(90deg,#8b5cf6,#6d28d9\)": r"linear-gradient(90deg,#f97316,#0f766e)",

    r"linear-gradient\(90deg,\s*#8b5cf6,\s*#10b981\)": r"linear-gradient(90deg, #f97316, #10b981)",
    
    r"from-violet-([0-9]+)": r"from-teal-\1",
    r"to-violet-([0-9]+)": r"to-teal-\1",
    r"from-indigo-([0-9]+)": r"from-teal-\1",
    r"to-indigo-([0-9]+)": r"to-teal-\1",
    r"via-indigo-([0-9]+)": r"via-teal-\1",
    
    # Hex codes
    r"#6d28d9": r"#0f766e", # teal-700
    r"#8b5cf6": r"#f97316", # orange-500
    r"#7c3aed": r"#0d9488", # teal-600
    r"#4f46e5": r"#0d9488", # teal-600
    r"#6366f1": r"#14b8a6", # teal-500
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

for root, _, files in os.walk(FRONTEND_DIR):
    for file in files:
        if file.endswith(('.tsx', '.ts', '.css')):
            process_file(os.path.join(root, file))

print("Color update complete!")
