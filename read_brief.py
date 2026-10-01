import json

path = r'C:\Users\ANVESH\.gemini\antigravity-ide\brain\665ae209-ed15-4639-93f5-eaf0f10d8eec\.system_generated\logs\transcript_full.jsonl'
for line in open(path, encoding='utf-8'):
    if "ROLE" in line and "senior full-stack" in line:
        d = json.loads(line)
        content = d.get('content', '')
        idx = content.find("PHASE 3")
        if idx != -1:
            print("FOUND PHASE 3:")
            print(content[idx:idx+1500])
            break
