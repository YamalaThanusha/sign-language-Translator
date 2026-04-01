from PIL import Image, ImageDraw, ImageFont
import os
import json
import shutil

signs_dir = 'static/signs'

# Backup existing files
backup_dir = 'static/signs_backup'
if os.path.exists(signs_dir):
    shutil.rmtree(backup_dir, ignore_errors=True)
    shutil.copytree(signs_dir, backup_dir)
    # Clear the directory but keep it
    for f in os.listdir(signs_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(signs_dir, f))

os.makedirs(signs_dir, exist_ok=True)

# Enhanced mapping with multiple file name variants for each sign
sign_files = {
    # English word -> list of filenames to create
    'hello': ['hello', 'hi'],
    'goodbye': ['goodbye', 'bye'],
    'thank': ['thank', 'thanks', 'thank-you', 'thankyou'],
    'please': ['please'],
    'yes': ['yes'],
    'no': ['no'],
    'help': ['help'],
    'love': ['love'],
    'good': ['good'],
    'bad': ['bad'],
    'water': ['water'],
    'food': ['food'],
    'name': ['name'],
    'friend': ['friend'],
    'family': ['family'],
}

# Keep the JSON mapping
mapping = {
    'hello': 'HELLO',
    'hi': 'HELLO', 
    'goodbye': 'BYE',
    'bye': 'BYE',
    'thank': 'THANK-YOU',
    'thanks': 'THANK-YOU',
    'please': 'PLEASE',
    'yes': 'YES',
    'no': 'NO',
    'help': 'HELP',
    'love': 'LOVE',
    'good': 'GOOD',
    'bad': 'BAD',
    'water': 'WATER',
    'food': 'FOOD',
    'name': 'NAME',
    'friend': 'FRIEND',
    'family': 'FAMILY',
}

with open(f'{signs_dir}/sign_mapping.json', 'w') as f:
    json.dump(mapping, f, indent=2)

created = []
for english, file_variants in sign_files.items():
    gloss = mapping.get(english, english.upper())
    
    for filename in file_variants:
        filepath = os.path.join(signs_dir, f'{filename}.png')
        
        # Create a simple placeholder image
        img = Image.new('RGB', (300, 200), color=(15, 23, 42))  # Dark blue background
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fall back to default
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 40)
            font_small = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 20)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
                font_small = ImageFont.load_default()
        
        # Draw gloss text
        draw.text((150, 60), gloss, fill=(99, 102, 241), font=font, anchor="mm")
        # Draw English text
        draw.text((150, 130), f"({english})", fill=(148, 163, 184), font=font_small, anchor="mm")
        
        # Save as PNG
        img.save(filepath)
        created.append(filename)

print(f'✓ Created {len(created)} sign image files')
print(f'  Examples: {", ".join(created[:8])}')
print(f'\n✓ Total unique sign concepts: {len(sign_files)}')
print(f'\nSign files available:')
for f in sorted(os.listdir(signs_dir)):
    if f.endswith('.png'):
        print(f'  - {f}')
