"""Verify published text parity, local assets, metadata, and archive coverage."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://kjp9204-oss.github.io/ControlmyLife/'


def normalized(text):
    return re.sub(r'\s+', '', text).replace('\u200b', '').replace('\ufeff', '')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--update-sitemap', action='store_true')
    parser.add_argument('--baseline-ref', help='Immutable pre-sync Git commit; verify old pages unchanged and report source drift separately')
    args = parser.parse_args()
    posts = json.loads((ROOT / 'data/naver-posts.json').read_text(encoding='utf-8'))
    baseline = {}
    if args.baseline_ref:
        if not re.fullmatch(r'[0-9a-f]{40}', args.baseline_ref):
            parser.error('--baseline-ref must be a full immutable commit SHA')
        snapshot = subprocess.check_output(['git', 'show', args.baseline_ref + ':data/naver-posts.json'], cwd=ROOT)
        baseline = {p['id']: p for p in json.loads(snapshot)}
        assert set(baseline) <= {p['id'] for p in posts}, 'Existing posts removed'
    assert len({post['id'] for post in posts}) == len(posts)
    archive = BeautifulSoup((ROOT/'hobby-blog.html').read_text(encoding='utf-8'), 'html.parser')
    cards = archive.select('.compact-grid .archive-card')
    assert len(cards) == len(list((ROOT/'posts').glob('*.html')))
    assert cards[0]['href'] == posts[0]['href']
    local_images = set()
    source_drift = []
    for post in posts:
        path = ROOT / post['href']
        if post['id'] in baseline:
            assert post == baseline[post['id']], post['id'] + ': existing metadata changed'
            # Git applies its checkout newline filters on Windows. Compare
            # against the immutable tree, not raw CRLF/LF file bytes.
            subprocess.run(['git', 'diff', '--quiet', args.baseline_ref, '--', post['href']], cwd=ROOT, check=True)
        raw = path.read_text(encoding='utf-8')
        page = BeautifulSoup(raw, 'html.parser')
        source = BeautifulSoup((args.cache/(post['id']+'.html')).read_text(encoding='utf-8'), 'html.parser').select_one('.se-main-container')
        for control in source.select('button,input,form'):
            control.decompose()
        body = BeautifulSoup(str(page.select_one('.naver-body')), 'html.parser')
        for fallback in body.select('.source-video,.source-image'):
            fallback.decompose()
        if normalized(source.get_text()) != normalized(body.get_text()):
            assert post['id'] in baseline, post['id'] + ': text mismatch'
            source_drift.append(post['id'])
        assert page.h1.get_text() == post['title']
        assert page.select_one('link[rel="canonical"]')['href'] == SITE + post['href']
        assert len(page.select('.source-video')) >= post['video_links']
        assert len(page.select('.source-image')) == len(post['external_image_fallbacks'])
        assert len(page.select('.naver-body img')) == post['local_images']
        assert page.select_one('time')['datetime'] == post['published']
        assert post['href'] in {a['href'] for a in cards}
        assert not re.search(r'\binkey\b|data-module|onclick=|javascript:', raw, re.I)
        for script in page.select('script'):
            assert script.get('type') == 'application/ld+json'
            json.loads(script.string)
        for node in page.select('[src],link[href],a[href]'):
            url = node.get('src') or node.get('href')
            if urllib.parse.urlsplit(url).scheme or url.startswith('#'):
                continue
            target = (path.parent / urllib.parse.unquote(url.split('#')[0])).resolve()
            assert target.is_file(), f'{path.name}: missing {url}'
            if node.name == 'img':
                local_images.add(target)
                assert target.stat().st_size > 100
    if args.update_sitemap:
        sitemap_path = ROOT/'sitemap.xml'
        sitemap = sitemap_path.read_text(encoding='utf-8')
        for post in posts:
            url = SITE + post['href']
            if f'<loc>{url}</loc>' not in sitemap:
                entry = f'  <url><loc>{url}</loc><lastmod>{post["published"][:10]}</lastmod></url>\n'
                sitemap = sitemap.replace('</urlset>', entry+'</urlset>')
        for url in [SITE, SITE+'hobby-blog.html']:
            sitemap = re.sub(r'(<loc>'+re.escape(url)+r'</loc><lastmod>)[^<]+', lambda match: match.group(1)+datetime.now().astimezone().date().isoformat(), sitemap)
        sitemap_path.write_text(sitemap, encoding='utf-8')
    ET.fromstring((ROOT/'sitemap.xml').read_text(encoding='utf-8'))
    report = {'verified_posts': len(posts), 'archive_posts':len(cards),
              'local_image_placements':sum(p['local_images'] for p in posts),
              'unique_local_image_files':len(local_images),
              'asset_megabytes':round(sum(p.stat().st_size for p in local_images)/1024/1024, 2),
              'naver_video_links':sum(p['video_links'] for p in posts),
              'external_image_links':sum(len(p['external_image_fallbacks']) for p in posts),
              'current_source_text_matches': len(posts) - len(source_drift),
              'new_post_text_parity':'PASS',
              'baseline_pages_unchanged':len(baseline),
              'existing_source_changed_ids':source_drift,
              'local_links':'PASS', 'metadata':'PASS'}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
