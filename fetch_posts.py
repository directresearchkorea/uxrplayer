import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

urls = [
    "https://www.uxrplayer.com/post/how-ux-research-transforms-products-a-case-study-in-user-experience-improvement",
    "https://www.uxrplayer.com/post/aion2-data-analysis-what-role-do-live-streams-play",
    "https://www.uxrplayer.com/post/how-koreans-prepare-for-international-travel-the-structure-of-travel-planning-revealed-through-app",
    "https://www.uxrplayer.com/post/why-korean-gamers-choose-and-continue-playing-games-a-motivational-analysis",
    "https://www.uxrplayer.com/post/where-do-korean-gamers-play-an-analysis-of-primary-platform-choice-and-spending-behavior-in-the-ko",
    "https://www.uxrplayer.com/post/game-genre-preferences-in-the-korean-market-age-based-play-patterns-and-popular-genre-statistics"
]

os.makedirs('_posts', exist_ok=True)

for url in urls:
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Title
        title_tag = soup.find('title')
        title = title_tag.text.split('|')[0].strip() if title_tag else "Untitled"
        
        # Meta descriptions
        desc_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', property='og:description')
        desc = desc_tag['content'] if desc_tag else ""
        
        # Meta image
        img_tag = soup.find('meta', property='og:image')
        img = img_tag['content'] if img_tag else ""
        
        # Article content
        # Wix usually puts content in something with 'post-content' or similar
        article = soup.find('article') or soup.find('main')
        
        # Convert simple tags to markdown
        content_md = ""
        if article:
            # Very basic extraction
            for el in article.find_all(['h1', 'h2', 'h3', 'p', 'img']):
                if el.name in ['h1', 'h2', 'h3']:
                    level = int(el.name[1])
                    content_md += f"{'#' * level} {el.text.strip()}\n\n"
                elif el.name == 'p':
                    if el.text.strip():
                        content_md += f"{el.text.strip()}\n\n"
                elif el.name == 'img':
                    src = el.get('src')
                    if src and not src.startswith('data:'):
                        content_md += f"![image]({src})\n\n"
        
        # Fallback if extraction is empty
        if not content_md.strip():
            content_md = "Content could not be automatically extracted. Please review the original post."

        slug = url.split('/')[-1]
        
        # Write to file
        with open(f"_posts/{slug}.md", 'w', encoding='utf-8') as f:
            f.write("---\n")
            f.write(f"title: \"{title}\"\n")
            f.write(f"date: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}\n")
            # Escape quotes in description
            safe_desc = desc.replace('"', '\\"')
            f.write(f"description: \"{safe_desc}\"\n")
            f.write(f"thumbnail: \"{img}\"\n")
            f.write("---\n\n")
            f.write(content_md)
            
        print(f"Successfully fetched {slug}")
        
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")

