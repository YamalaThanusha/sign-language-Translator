from PIL import Image, ImageDraw, ImageFont
import os
import json

signs_dir = 'static/signs'
os.makedirs(signs_dir, exist_ok=True)

# Load or create mapping
mapping_file = os.path.join(signs_dir, 'sign_mapping.json')
if os.path.exists(mapping_file):
    with open(mapping_file) as f:
        mapping = json.load(f)
else:
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
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, indent=2)

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
    created.append(english)

print(f'✓ Created {len(created)} placeholder sign images')
if created:
    print(f'  Examples: {", ".join(created[:5])}')
print(f'\n✓ Total signs available: {len(mapping)}')
print(f'\nSign files are saved in: {os.path.abspath(signs_dir)}')
