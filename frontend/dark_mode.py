import re
import glob

files = [
    "c:/Users/PRATIK/OneDrive/Desktop/deep-agent-swarm/frontend/src/App.jsx",
    "c:/Users/PRATIK/OneDrive/Desktop/deep-agent-swarm/frontend/src/components/ResearchBoard.jsx"
]

replacements = {
    'bg-white': 'bg-black',
    'bg-slate-50': 'bg-black',
    'bg-slate-100': 'bg-neutral-900',
    'bg-slate-900': 'bg-neutral-900',
    'bg-neutral-100': 'bg-neutral-900',
    'border-slate-100': 'border-neutral-800',
    'border-slate-200': 'border-neutral-800',
    'text-slate-500': 'text-neutral-400',
    'text-slate-600': 'text-neutral-300',
    'text-slate-700': 'text-white',
    'text-slate-800': 'text-white',
    'text-black': 'text-white',
    'bg-black': 'bg-white',
    'text-white': 'text-black', 
}

def safe_replace(match):
    return replacements[match.group(0)]

pattern = re.compile(r'\b(' + '|'.join(re.escape(k) for k in replacements.keys()) + r')\b')

for filepath in files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = pattern.sub(safe_replace, content)
        
        # Additional manual fixes for inverted buttons
        new_content = new_content.replace('bg-white hover:bg-neutral-800 text-black', 'bg-white hover:bg-neutral-200 text-black')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
