with open('static/img/logo-mec-horizontal-cropped.svg', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print('viewBox in svg:', re.findall(r'viewBox="[^"]+"', text))
print('width/height:', re.findall(r'(?:width|height)="[^"]+"', text))
print('Total text length:', len(text))
