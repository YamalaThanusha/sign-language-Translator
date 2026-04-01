from PIL import Image, ImageDraw, ImageFont
import os
import json

signs_dir = 'static/signs'
os.makedirs(signs_dir, exist_ok=True)

# Complete mapping based on lexicon
mapping = {
    'hello': 'HELLO',
    'hi': 'HELLO',
    'hey': 'HELLO',
    'yes': 'YES',
    'no': 'NO',
    'please': 'PLEASE',
    'sorry': 'SORRY',
    'help': 'HELP',
    'thanks': 'THANK-YOU',
    'thank': 'THANK-YOU',
    'deaf': 'DEAF',
    'hearing': 'HEARING',
    'learn': 'LEARN',
    'sign': 'SIGN',
    'language': 'LANGUAGE',
    'good': 'GOOD',
    'bad': 'BAD',
    'morning': 'MORNING',
    'afternoon': 'AFTERNOON',
    'night': 'NIGHT',
    'bye': 'BYE',
    'goodbye': 'BYE',
    'water': 'WATER',
    'food': 'FOOD',
    'eat': 'EAT',
    'drink': 'DRINK',
    'friend': 'FRIEND',
    'family': 'FAMILY',
    'name': 'NAME',
    'my': 'MY',
    'your': 'YOUR',
    'i': 'I',
    'you': 'YOU',
    'we': 'WE',
    'they': 'THEY',
    'what': 'WHAT',
    'where': 'WHERE',
    'when': 'WHEN',
    'why': 'WHY',
    'how': 'HOW',
    'who': 'WHO',
    'love': 'LOVE',
}

# Keep only PNG files from previous run
for f in os.listdir(signs_dir):
    if not f.endswith('.png'):
        continue
    base = f.replace('.png', '')
    # Remove if it's not in our mapping
    if base not in mapping and base not in ['thank-you', 'thankyou', 'good-bye']:
        # Keep it
        pass

created = []
for english, gloss in mapping.items():
    filepath = os.path.join(signs_dir, f'{english}.png')
    if os.path.exists(filepath):
        continue
    
    # Create a simple placeholder image
    img = Image.new('RGB', (300, 200), color=(15, 23, 42))  # Dark blue background
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fall back to default
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 40)
        font_small = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 18)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
    
    # Draw gloss text
    draw.text((150, 60), gloss, fill=(99, 102, 241), font=font, anchor="mm")
    # Draw English text
    draw.text((150, 130), f"({english})", fill=(148, 163, 184), font=font_small, anchor="mm")
    
    # Save as PNG
    img.save(filepath)
    created.append(english)

# Create variants for common phrases
variants = {
    'thank-you': 'THANK-YOU',
    'good-morning': 'GOOD MORNING',
    'good-night': 'GOOD NIGHT',
}

for variantname, gloss in variants.items():
    filepath = os.path.join(signs_dir, f'{variantname}.png')
    if os.path.exists(filepath):
        continue
    
    img = Image.new('RGB', (300, 200), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 32)
        font_small = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 16)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
    
    draw.text((150, 60), gloss, fill=(99, 102, 241), font=font, anchor="mm")
    draw.text((150, 130), f"({variantname})", fill=(148, 163, 184), font=font_small, anchor="mm")
    img.save(filepath)
    created.append(variantname)

# Save mapping
with open(f'{signs_dir}/sign_mapping.json', 'w') as f:
    json.dump(mapping, f, indent=2)

print(f'✓ Created {len(created)} new sign image files')
print(f'✓ Total unique signs in database: {len(mapping)}')
print(f'\nSample signs available:')
for fname in sorted(os.listdir(signs_dir))[:15]:
    if fname.endswith('.png'):
        print(f'  - {fname}')
print(f'  ... and {len([f for f in os.listdir(signs_dir) if f.endswith(".png")]) - 15} more')
