import os
import sys
import io
import re
import yaml
import urllib.request
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

POSTS_DIR = r'c:\Users\ggamy\OneDrive\Desktop\H_uxrplayer.com\_posts'

def fetch_og_image(slug):
    import urllib.parse
    encoded_slug = urllib.parse.quote(slug)
    url = f"https://www.uxrplayer.com/post/{encoded_slug}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        og_img = soup.find('meta', property='og:image')
        if og_img and og_img.get('content'):
            return og_img.get('content')
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    files = [f for f in os.listdir(POSTS_DIR) if f.endswith('.md')]
    fixed_count = 0
    
    for filename in files:
        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content.startswith('---'):
            continue
            
        parts = content.split('---', 2)
        if len(parts) < 3:
            continue
            
        frontmatter = parts[1]
        body = parts[2]
        
        try:
            meta = yaml.safe_load(frontmatter)
        except Exception:
            continue
            
        if not meta:
            continue
            
        thumbnail = meta.get('thumbnail', '').strip()
        
        if not thumbnail:
            slug = filename.replace('.md', '')
            print(f"[{slug}] Missing thumbnail. Fetching...")
            new_thumb = fetch_og_image(slug)
            
            if new_thumb:
                print(f"  -> Found: {new_thumb}")
                # Update frontmatter
                # We use regex to replace thumbnail: "" with the new one
                new_frontmatter = re.sub(
                    r'thumbnail:\s*".*?"',
                    f'thumbnail: "{new_thumb}"',
                    frontmatter
                )
                
                # If regex didn't replace because there were no quotes
                if new_frontmatter == frontmatter:
                    new_frontmatter = re.sub(
                        r'thumbnail:\s*.*',
                        f'thumbnail: "{new_thumb}"',
                        frontmatter
                    )
                
                new_content = f"---{new_frontmatter}---{body}"
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                fixed_count += 1
            else:
                print(f"  -> No og:image found.")
                
    print(f"\nDone! Fixed {fixed_count} files.")

if __name__ == '__main__':
    main()
