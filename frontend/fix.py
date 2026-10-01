import re
with open('src/theme/colormaps.ts', 'r') as f:
    content = f.read()

content = content.replace('export type ColorStop = { stop: number; hex: string; rgba: string };', 'export type ColorStop = { stop: number; hex: string; rgba: [number, number, number, number] };')

def repl(m):
    return f"rgba: [{m.group(1)}, {m.group(2)}, {m.group(3)}, {255 if m.group(4) == '1' else 0}]"

content = re.sub(r"rgba:\s*'rgba\((\d+),(\d+),(\d+),(\d+)\)'", repl, content)

with open('src/theme/colormaps.ts', 'w') as f:
    f.write(content)
