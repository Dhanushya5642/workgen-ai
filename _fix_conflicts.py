import sys

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '<<<<<<<' not in content:
        print(f'{path} is clean')
        return
    
    lines = content.split('\n')
    cleaned = []
    skip_block = False
    for line in lines:
        if line.startswith('<<<<<<<'):
            skip_block = True
            continue
        if line.startswith('======='):
            skip_block = True
            continue
        if line.startswith('>>>>>>>'):
            skip_block = False
            continue
        if not skip_block:
            cleaned.append(line)
    
    new_content = '\n'.join(cleaned)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'Fixed {path}')

fix_file('agentx-frontend/src/pages/EmailIntelligence.jsx')
fix_file('backend/api.py')
print('Done')
``