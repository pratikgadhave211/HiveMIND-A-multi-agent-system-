import re

files = [
    "c:/Users/PRATIK/OneDrive/Desktop/deep-agent-swarm/frontend/src/App.jsx",
    "c:/Users/PRATIK/OneDrive/Desktop/deep-agent-swarm/frontend/src/components/ResearchBoard.jsx"
]

def fix_content(content):
    # Force backgrounds to black/dark
    content = re.sub(r'\bbg-white\b', 'bg-black', content)
    content = re.sub(r'\bbg-slate-\d+\b', 'bg-neutral-900', content)
    content = re.sub(r'\bbg-neutral-\d+\b', 'bg-neutral-900', content)
    
    # Force text to white
    content = re.sub(r'\btext-black\b', 'text-white', content)
    content = re.sub(r'\btext-slate-\d+\b', 'text-white', content)
    content = re.sub(r'\btext-neutral-\d+\b', 'text-gray-300', content)
    
    # Force borders to dark
    content = re.sub(r'\bborder-slate-\d+\b', 'border-neutral-800', content)
    content = re.sub(r'\bborder-neutral-\d+\b', 'border-neutral-800', content)
    
    return content

for filepath in files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = fix_content(content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
