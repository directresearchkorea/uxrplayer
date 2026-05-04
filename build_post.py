import os
import re
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import urllib.parse
from bs4 import BeautifulSoup

POSTS_DIR = '_posts'
PAGES_DIR = '_pages'
OUTPUT_DIR = '.'
TEMPLATES_DIR = 'templates'
SITE_URL = 'https://uxrplayer.com'

def extract_youtube_id(url):
    if not url:
        return None
    # Matches various YouTube URL formats
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|i\.ytimg\.com\/vi\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def extract_youtube_id_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for a in soup.find_all('a', href=True):
        yt_id = extract_youtube_id(a['href'])
        if yt_id:
            return yt_id
    for iframe in soup.find_all('iframe', src=True):
        yt_id = extract_youtube_id(iframe['src'])
        if yt_id:
            return yt_id
    return None

def build():
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    post_template = env.get_template('post.html')
    index_template = env.get_template('index.html')
    insights_template = env.get_template('insights.html')

    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)
    if not os.path.exists(PAGES_DIR):
        os.makedirs(PAGES_DIR)

    posts = []
    all_pages = []
    
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith('.md'):
            continue
            
        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML frontmatter
        if content.startswith('---'):
            _, frontmatter, md_content = content.split('---', 2)
            meta = yaml.safe_load(frontmatter)
        else:
            meta = {}
            md_content = content

        html_content = markdown.markdown(md_content)
        
        # Determine slug and URL
        slug = filename.replace('.md', '')
        post_url = f"/posts/{slug}/"
        
        # Handle Thumbnail
        thumbnail = meta.get('thumbnail')
        youtube_url = meta.get('youtube_url')
        yt_id = extract_youtube_id(youtube_url)
        
        if not yt_id and thumbnail:
            yt_id = extract_youtube_id(thumbnail)
        
        if not yt_id:
            yt_id = extract_youtube_id_from_html(html_content)
            
        if yt_id:
            # Embed the video at the top of the post if it has a youtube ID
            iframe_html = f'''
            <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin: 2rem 0; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
              <iframe src="https://www.youtube.com/embed/{yt_id}?feature=oembed" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
            </div>
            '''
            html_content = iframe_html + html_content
            
        if not thumbnail and yt_id:
            thumbnail = f"https://img.youtube.com/vi/{yt_id}/maxresdefault.jpg"
        elif not thumbnail:
            thumbnail = "/assets/images/default-thumbnail.jpg" # Fallback image
            
        meta['thumbnail'] = thumbnail
        meta['url'] = post_url + "index.html"
        meta['date_parsed'] = meta.get('date', datetime.now())
        if isinstance(meta['date_parsed'], str):
            try:
                # Handle YYYY-MM-DD
                meta['date_parsed'] = datetime.strptime(meta['date_parsed'].split('T')[0], '%Y-%m-%d')
            except:
                meta['date_parsed'] = datetime.now()
        
        # Create a string representation for templates
        meta['formatted_date'] = meta['date_parsed'].strftime('%Y-%m-%d') if isinstance(meta['date_parsed'], datetime) else str(meta['date_parsed'])[:10]

        # Render Post HTML
        post_html = post_template.render(
            title=meta.get('title', 'Untitled'),
            description=meta.get('description', ''),
            content=html_content,
            meta=meta,
            site_url=SITE_URL
        )

        # Output to /posts/<slug>/index.html
        post_out_dir = os.path.join(OUTPUT_DIR, 'posts', slug)
        os.makedirs(post_out_dir, exist_ok=True)
        with open(os.path.join(post_out_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(post_html)

        posts.append(meta)

    # Sort posts by date descending
    posts.sort(key=lambda x: x.get('date_parsed', datetime.min), reverse=True)

    # Update index.html
    index_html = index_template.render(posts=posts, site_url=SITE_URL)
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

    # Generate insights page
    insights_out_dir = os.path.join(OUTPUT_DIR, 'insights')
    os.makedirs(insights_out_dir, exist_ok=True)
    insights_html = insights_template.render(posts=posts, site_url=SITE_URL)
    with open(os.path.join(insights_out_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(insights_html)

    # Process Pages
    for filename in os.listdir(PAGES_DIR):
        if not filename.endswith('.md'):
            continue
            
        filepath = os.path.join(PAGES_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if content.startswith('---'):
            _, frontmatter, md_content = content.split('---', 2)
            meta = yaml.safe_load(frontmatter)
        else:
            meta = {}
            md_content = content

        html_content = markdown.markdown(md_content)
        slug = filename.replace('.md', '')
        meta['url'] = f"/{slug}/index.html"
        
        page_html = post_template.render(
            title=meta.get('title', 'Untitled'),
            description=meta.get('description', ''),
            content=html_content,
            meta=meta,
            site_url=SITE_URL
        )

        page_out_dir = os.path.join(OUTPUT_DIR, slug)
        os.makedirs(page_out_dir, exist_ok=True)
        # Update relative paths to be 1 level up instead of 2 levels up
        page_html = page_html.replace('href="../../', 'href="../')
        page_html = page_html.replace('src="../../', 'src="../')
        
        with open(os.path.join(page_out_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(page_html)
            
        all_pages.append(meta)

    # Generate sitemap.xml
    generate_sitemap(posts + all_pages)

def generate_sitemap(posts):
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Add homepage
    sitemap += '  <url>\n'
    sitemap += f'    <loc>{SITE_URL}/</loc>\n'
    sitemap += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
    sitemap += '    <priority>1.0</priority>\n'
    sitemap += '  </url>\n'

    # Add posts
    for post in posts:
        sitemap += '  <url>\n'
        sitemap += f'    <loc>{SITE_URL}{post["url"]}</loc>\n'
        if isinstance(post.get('date_parsed'), datetime):
            sitemap += f'    <lastmod>{post["date_parsed"].strftime("%Y-%m-%d")}</lastmod>\n'
        sitemap += '    <priority>0.8</priority>\n'
        sitemap += '  </url>\n'

    sitemap += '</urlset>'
    
    with open(os.path.join(OUTPUT_DIR, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap)

if __name__ == '__main__':
    build()
