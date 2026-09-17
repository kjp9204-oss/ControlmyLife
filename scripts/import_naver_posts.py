"""Import the author's public Naver posts since a verified synchronization date.

Requires beautifulsoup4. Downloads only article-body images, never comments,
profile data or Naver scripts. Existing unrelated posts are left untouched.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.utils import parsedate_to_datetime
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://kjp9204-oss.github.io/ControlmyLife/'
BLOG = 'https://m.blog.naver.com/kjp9204/'
STYLE_PROPERTIES = {'color', 'background-color', 'text-align', 'font-weight',
                    'font-style', 'text-decoration', 'border', 'border-color',
                    'border-collapse', 'vertical-align'}
ALLOWED_TAGS = {'div', 'section', 'p', 'span', 'b', 'strong', 'i', 'em', 'u',
                's', 'br', 'a', 'img', 'table', 'tbody', 'thead', 'tr', 'td',
                'th', 'blockquote', 'ul', 'ol', 'li', 'h2', 'h3', 'h4', 'hr',
                'figure', 'figcaption', 'sup', 'sub'}


def fetch(url):
    parsed = urllib.parse.urlsplit(url)
    url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc,
          urllib.parse.quote(urllib.parse.unquote(parsed.path), safe='/@:+'),
          parsed.query, ''))
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read(25 * 1024 * 1024 + 1)
        if len(content) > 25 * 1024 * 1024:
            raise ValueError('Asset exceeds 25 MiB')
        return content, response.headers.get_content_type()


def safe_url(url):
    return urllib.parse.urlsplit(url).scheme in {'https', 'http'}


def normalize(value):
    return re.sub(r'\s+', '', value).replace('\u200b', '').replace('\ufeff', '')


def article_excerpt(body, fallback):
    """Use an unchanged prose excerpt when RSS contains only tags/links."""
    for paragraph in body.select('.se-text-paragraph'):
        text = re.sub(r'\s+', ' ', paragraph.get_text('', strip=False)).strip()
        if len(text) >= 50 and '.' in text and not re.search(r'#|https?://|CONTROL MY LIFE', text):
            return text if len(text) <= 180 else text[:177].rstrip() + '…'
    return fallback


def image_extension(content, mime):
    extension = {'image/jpeg': '.jpg', 'image/jpg': '.jpg', 'image/png': '.png', 'image/gif': '.gif',
                 'image/webp': '.webp', 'image/avif': '.avif'}.get(mime)
    # Some public image CDNs use a generic binary Content-Type. Accept only
    # recognized raster signatures, never HTML/SVG/executable payloads.
    if not extension and mime == 'application/octet-stream':
        if content.startswith(b'\xff\xd8\xff'):
            extension = '.jpg'
        elif content.startswith(b'\x89PNG\r\n\x1a\n'):
            extension = '.png'
        elif content.startswith((b'GIF87a', b'GIF89a')):
            extension = '.gif'
        elif content[:4] == b'RIFF' and content[8:12] == b'WEBP':
            extension = '.webp'
    return extension


def save_image(url):
    if not safe_url(url):
        raise ValueError('Invalid image URL')
    content, mime = fetch(url)
    extension = image_extension(content, mime)
    if not extension:
        raise ValueError(f'Unsupported image response: {mime}')
    relative = 'assets/images/naver/' + hashlib.sha256(content).hexdigest()[:24] + extension
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return relative


def import_post(item, cache):
    post_id = item['id']
    source = BLOG + post_id
    cached = cache / (post_id + '.html')
    if cached.exists():
        raw = cached.read_text(encoding='utf-8')
    else:
        raw = fetch(source)[0].decode('utf-8')
        cached.write_text(raw, encoding='utf-8')
    soup = BeautifulSoup(raw, 'html.parser')
    body = soup.select_one('.se-main-container')
    if body is None:
        raise ValueError(f'No article body: {post_id}')
    item = {**item, 'description': article_excerpt(body, item['description'])}
    # Gallery next/previous controls are platform UI, not the author's prose.
    for control in body.select('button, input, form'):
        control.decompose()
    original_text = normalize(body.get_text())
    original_image_count = len(body.select('img'))
    videos = 0
    for video in body.select('.se-video'):
        videos += 1
        data_node = video.select_one('script[data-module]') or video.select_one('script[data-module-v2]')
        data = json.loads(data_node.get('data-module') or data_node['data-module-v2'])['data'] if data_node else {}
        link = soup.new_tag('a', href=source)
        link['class'] = ['source-video']
        if safe_url(data.get('thumbnail', '')):
            preview = soup.new_tag('img', src=data['thumbnail'], alt='영상 미리보기')
            link.append(preview)
        label = soup.new_tag('span')
        label.string = '▶ ' + data.get('mediaMeta', {}).get('title', '영상') + ' — 네이버 원문에서 재생'
        link.append(label)
        video.replace_with(link)
    # Platform-specific embedded players retain a visible original-page fallback.
    for embed in body.select('.se-oembed'):
        link = soup.new_tag('a', href=source)
        link['class'] = ['source-video']
        link.string = '▶ 외부 영상 — 네이버 원문에서 재생'
        embed.append(link)
    for unwanted in body.select('script, style, iframe, object, embed, button, input, form'):
        unwanted.decompose()
    for comment in body.find_all(string=lambda node: isinstance(node, Comment)):
        comment.extract()

    images = []
    failures = []
    for index, image in enumerate(body.select('img'), 1):
        url = image.get('data-lazy-src') or image.get('src', '')
        try:
            relative = save_image(url)
            images.append(relative)
            image['src'] = '../' + relative
        except Exception as error:
            if not safe_url(url):
                raise
            failures.append({'url': url, 'reason': str(error)})
            fallback = soup.new_tag('a', href=source)
            fallback['class'] = ['source-image']
            fallback.string = '외부 이미지 — 네이버 원문에서 확인'
            parent = image.find_parent('a')
            if parent:
                parent.replace_with(fallback)
            else:
                image.replace_with(fallback)
            print(f'IMAGE LINK {post_id}: {urllib.parse.urlsplit(url).netloc}: {error}', flush=True)
            continue
        image['alt'] = image.get('alt') or f'{item["title"]} — 본문 이미지 {index}'
        image['loading'] = 'lazy'
        image['decoding'] = 'async'
        image['referrerpolicy'] = 'no-referrer'
        parent = image.find_parent('a')
        if parent and parent.get('href') == '#':
            parent['href'] = image['src']

    for tag in list(body.find_all(True)):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
            continue
        kept = {}
        classes = [c for c in tag.get('class', []) if c.startswith('se-') or c in {'source-video', 'source-image'}]
        if classes:
            kept['class'] = classes
        styles = []
        for rule in tag.get('style', '').split(';'):
            if ':' not in rule:
                continue
            key, value = (part.strip() for part in rule.split(':', 1))
            if key in STYLE_PROPERTIES and re.fullmatch(r'[a-zA-Z0-9#(),.%\s-]+', value):
                styles.append(f'{key}:{value}')
        if styles:
            kept['style'] = ';'.join(styles)
        if tag.name == 'a':
            href = tag.get('href', '')
            if safe_url(href) or href.startswith('../assets/images/naver/'):
                kept['href'] = href
                if safe_url(href):
                    kept['target'] = '_blank'
                    kept['rel'] = 'noopener noreferrer'
        if tag.name == 'img':
            for key in ['src', 'alt', 'loading', 'decoding', 'referrerpolicy']:
                if tag.get(key):
                    kept[key] = tag[key]
        if tag.name in {'td', 'th'}:
            for key in ['colspan', 'rowspan']:
                if str(tag.get(key, '')).isdigit():
                    kept[key] = tag[key]
        tag.attrs = kept
    # Wrapping never modifies the text or order of the published article.
    for table in body.select('table'):
        wrapper = soup.new_tag('div', attrs={'class': 'imported-table'})
        table.wrap(wrapper)
    text_check = BeautifulSoup(str(body), 'html.parser')
    for fallback in text_check.select('.source-video,.source-image'):
        fallback.decompose()
    if normalize(text_check.get_text()) != original_text:
        raise ValueError(f'Published text changed during conversion: {post_id}')
    if len(body.select('img')) + len(failures) < original_image_count:
        raise ValueError(f'Images lost during conversion: {post_id}')
    href = 'posts/naver-' + post_id + '.html'
    title = html.escape(item['title'])
    description = html.escape(item['description'], quote=True)
    cover = images[0] if images else ''
    structured = {'@context': 'https://schema.org', '@type': 'BlogPosting',
                  'headline': item['title'], 'datePublished': item['published'],
                  'author': {'@type': 'Person', 'name': '김재필'},
                  'inLanguage': 'ko', 'url': SITE + href, 'isBasedOn': source}
    if cover:
        structured['image'] = SITE + cover
    schema = json.dumps(structured, ensure_ascii=False).replace('<', '\\u003c')
    output = f'''<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Control My Life</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{SITE + href}">
<meta property="og:type" content="article"><meta property="og:title" content="{title}">
<meta property="og:description" content="{description}"><meta property="og:url" content="{SITE + href}">
<meta property="article:published_time" content="{item['published']}">
<meta property="og:image" content="{SITE + cover}">
<link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="../assets/naver-posts.css">
<script type="application/ld+json">{schema}</script>
</head><body>
<header class="site-header"><a class="brand" href="../index.html">Control My Life</a><nav><a href="../hobby-blog.html">전체 글</a></nav></header>
<main><article class="post imported-post">
<p class="eyebrow">PERSONAL MAGAZINE</p><h1>{title}</h1>
<p class="byline">글 · 김재필 · <time datetime="{item['published']}">{item['published'][:10]}</time> · <a href="{source}" target="_blank" rel="noopener noreferrer">네이버 원문</a></p>
<div class="post-body naver-body">{body.decode_contents()}</div>
</article><p class="backhome"><a href="../hobby-blog.html">← 전체 글로 돌아가기</a></p></main>
<footer class="site-footer">© 2026 김재필 · Control My Life</footer>
</body></html>
'''
    (ROOT / href).write_text(output, encoding='utf-8')
    result = {**item, 'href': href, 'source': source, 'cover': cover,
              'images': len(body.select('img')), 'source_images': original_image_count, 'local_images': len(images),
              'video_links': videos, 'text_verified': True, 'external_image_fallbacks': failures}
    print(f'IMPORTED {post_id} images={len(images)} videos={videos} fallbacks={len(failures)}', flush=True)
    return result


def select_new_items(feed, old, since):
    """Use permanent post IDs, not titles/dates, as the idempotency key."""
    known = {item['id'] for item in old}
    if len(known) != len(old):
        raise ValueError('Existing manifest contains duplicate post IDs')
    items = {}
    dates = []
    for node in feed.findall('./channel/item'):
        published = parsedate_to_datetime(node.findtext('pubDate')).isoformat()
        dates.append(published[:10])
        if published[:10] <= since:
            continue
        match = re.search(r'/(\d+)(?:\?|$)', node.findtext('link') or '')
        if not match:
            raise ValueError('Unrecognized public post URL')
        post_id = match.group(1)
        if post_id in known:
            continue
        description = BeautifulSoup(node.findtext('description') or '', 'html.parser').get_text(' ', strip=True)
        item = {'id': post_id, 'title': html.unescape(node.findtext('title')).strip(),
                'published': published, 'description': description[:180]}
        if post_id in items and items[post_id] != item:
            raise ValueError(f'Conflicting RSS entries: {post_id}')
        items[post_id] = item
    if dates and min(dates) > since:
        raise ValueError('RSS does not cover the requested start date; compare the public post list before importing')
    return list(items.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--since', required=True, help='Exclusive ISO date of previous sync')
    parser.add_argument('--cache', required=True, type=Path, help='Cache directory outside the repository')
    parser.add_argument('--dry-run', action='store_true', help='List missing IDs without writing posts or assets')
    args = parser.parse_args()
    datetime.strptime(args.since, '%Y-%m-%d')
    if args.cache.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Raw source cache must remain outside the public repository')
    manifest_path = ROOT / 'data/naver-posts.json'
    old = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else []
    feed_bytes = fetch('https://rss.blog.naver.com/kjp9204.xml')[0]
    items = select_new_items(ET.fromstring(feed_bytes), old, args.since)
    if args.dry_run:
        print(json.dumps({'new_posts': len(items), 'items': items}, ensure_ascii=False, indent=2))
        return
    if not items:
        print('NO NEW POSTS; manifest and existing posts unchanged')
        return
    for item in items:
        if (ROOT / ('posts/naver-' + item['id'] + '.html')).exists():
            raise ValueError(f"Unindexed existing page must be reviewed first: {item['id']}")
    args.cache.mkdir(parents=True, exist_ok=True)
    (args.cache / 'rss-latest.xml').write_bytes(feed_bytes)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda item: import_post(item, args.cache), items))
    merged = {item['id']: item for item in old + results}
    manifest_path.parent.mkdir(exist_ok=True)
    manifest_path.write_text(json.dumps(sorted(merged.values(), key=lambda x:x['published'], reverse=True), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('TOTAL', len(results), 'IMAGES', sum(x['local_images'] for x in results), 'VIDEOS', sum(x['video_links'] for x in results))


if __name__ == '__main__':
    main()
