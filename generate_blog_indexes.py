from pathlib import Path
import html
import re


ROOT = Path(__file__).resolve().parent


def text_from(pattern: str, data: str) -> str:
    match = re.search(pattern, data, re.S | re.I)
    if not match:
        return ""
    value = re.sub(r"<[^>]+>", "", match.group(1))
    value = re.sub(r"\s+", " ", value).strip()
    return html.unescape(value)


def post_info(path: Path, prefix: str) -> dict[str, str]:
    data = path.read_text(encoding="utf-8")
    title = text_from(r"<h1[^>]*>(.*?)</h1>", data) or path.stem
    subtitle = text_from(r'class="subtitle"[^>]*>(.*?)</', data) or "Control My Life에 기록한 글입니다."
    return {"href": prefix + path.name, "title": title, "subtitle": subtitle}


def card(item: dict[str, str], kicker: str, section: str) -> str:
    title = html.escape(item["title"], quote=True)
    subtitle = html.escape(item["subtitle"], quote=True)
    href = html.escape(item["href"], quote=True)
    return (
        f'<a class="card archive-card" data-section="{section}" href="{href}">'
        f'<div class="card-art" data-kicker="{kicker}"></div>'
        f'<div class="card-content"><h3>{title}</h3>'
        f'<p class="card-desc">{subtitle}</p></div></a>'
    )


def write_hobby(personal: list[dict[str, str]]) -> None:
    featured = "\n".join(card(item, "FEATURE", "문화") for item in personal[:3])
    cards = "\n".join(card(item, "CML", "문화") for item in personal)
    output = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Control My Life 취미·일상·컨텐츠 블로그 - 김재필의 매거진</title>
<meta name="description" content="김재필의 취미·일상·컨텐츠 블로그. 만화, 애니, 영화, 음악, 게임, 전시회와 일상의 감상을 매거진처럼 기록합니다.">
<meta name="keywords" content="Control My Life, 김재필 블로그, 취미 블로그, 일상 블로그, 컨텐츠 블로그, 문화 리뷰, 만화 리뷰, 애니 리뷰, 영화 리뷰, 전시회 후기">
<meta name="author" content="김재필">
<link rel="canonical" href="https://kjp9204-oss.github.io/ControlmyLife/hobby-blog.html">
<meta property="og:type" content="website">
<meta property="og:title" content="Control My Life 취미·일상·컨텐츠 블로그">
<meta property="og:description" content="문화 리뷰와 일상 기록을 모은 개인 매거진 블로그입니다.">
<meta property="og:url" content="https://kjp9204-oss.github.io/ControlmyLife/hobby-blog.html">
<meta property="og:site_name" content="Control My Life">
<meta property="og:locale" content="ko_KR">
<link rel="stylesheet" href="assets/style.css">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Blog","name":"Control My Life 취미·일상·컨텐츠 블로그","description":"김재필의 취미·일상·컨텐츠 매거진 블로그입니다.","inLanguage":"ko","url":"https://kjp9204-oss.github.io/ControlmyLife/hobby-blog.html","author":{{"@type":"Person","name":"김재필"}}}}</script>
</head>
<body>
<header class="site-header"><a class="brand" href="index.html">Control My Life</a><nav><a href="hand-team-blog.html">Hand 팀 블로그</a></nav></header>
<main class="magazine-list-page">
<section class="list-hero personal-list-hero">
<p class="eyebrow">PERSONAL MAGAZINE</p>
<h1>취미·일상·컨텐츠 블로그</h1>
<p>문화 리뷰, 전시회, 애니·만화, 게임, 사건과 일상의 감정선을 김재필의 시선으로 기록합니다.</p>
<div class="archive-meta"><span>전체 {len(personal)}편</span><span>Culture · Daily · Contents</span></div>
</section>
<section class="editorial-block">
<p class="eyebrow">Featured</p>
<div class="grid feature-grid">
{featured}
</div>
</section>
<section class="editorial-block">
<p class="eyebrow">All Stories</p>
<h2>전체 글</h2>
<div class="grid compact-grid">
{cards}
</div>
</section>
</main>
<footer class="site-footer"><p>© 2026 김재필 · Control My Life</p></footer>
</body>
</html>
"""
    (ROOT / "hobby-blog.html").write_text(output, encoding="utf-8")


def write_hand(hand: list[dict[str, str]]) -> None:
    public = [item for item in hand if "public" in item["href"]]
    pro = [item for item in hand if "pro" in item["href"]]
    featured = "\n".join(card(item, "PUBLIC", "손목") for item in public[:6])
    public_cards = "\n".join(card(item, "PUBLIC", "손목") for item in public)
    pro_cards = "\n".join(card(item, "PRO", "손목") for item in pro)
    output = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hand 팀 블로그 - 손·손목 물리치료와 Hand PT</title>
<meta name="description" content="Hand 팀 블로그. 손목 통증, 손목터널증후군, 방아쇠수지, 드퀘르벵, 수부 재활과 운동 복귀 글 전체 아카이브입니다.">
<meta name="keywords" content="Hand 팀 블로그, Hand PT, 손목 통증, 손 통증, 손목터널증후군, 방아쇠수지, 드퀘르벵, 수부 재활, 손목 물리치료, 김재필 물리치료사, 에이온운동센터">
<meta name="author" content="김재필">
<link rel="canonical" href="https://kjp9204-oss.github.io/ControlmyLife/hand-team-blog.html">
<meta property="og:type" content="website">
<meta property="og:title" content="Hand 팀 블로그 - 손·손목 물리치료">
<meta property="og:description" content="손·손목 통증과 재활 글을 전체 아카이브로 정리합니다.">
<meta property="og:url" content="https://kjp9204-oss.github.io/ControlmyLife/hand-team-blog.html">
<meta property="og:site_name" content="Control My Life">
<meta property="og:locale" content="ko_KR">
<link rel="stylesheet" href="assets/style.css">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Blog","name":"Hand 팀 블로그","description":"손·손목 통증, 손목터널증후군, 수부 재활과 운동 복귀를 물리치료 관점에서 정리하는 전문 블로그입니다.","inLanguage":"ko","url":"https://kjp9204-oss.github.io/ControlmyLife/hand-team-blog.html","author":{{"@type":"Person","name":"김재필","jobTitle":"물리치료사","worksFor":{{"@type":"Organization","name":"에이온운동센터"}}}}}}</script>
</head>
<body>
<header class="site-header"><a class="brand" href="index.html">Control My Life</a><nav><a href="hobby-blog.html">취미·일상·컨텐츠</a></nav></header>
<main class="magazine-list-page">
<section class="list-hero hand-list-hero">
<p class="eyebrow">HAND TEAM JOURNAL</p>
<h1>Hand 팀 블로그</h1>
<p>손·손목 통증, 손목터널증후군, 방아쇠수지, 드퀘르벵, 수부 재활과 운동 복귀를 한곳에 모은 전문 아카이브입니다.</p>
<div class="archive-meta"><span>전체 {len(hand)}편</span><span>일반인용 {len(public)}편 · 전문가용 {len(pro)}편</span></div>
</section>
<section class="editorial-block">
<p class="eyebrow">Start Here</p>
<h2>먼저 읽기 좋은 글</h2>
<div class="grid feature-grid">
{featured}
</div>
</section>
<section class="editorial-block">
<p class="eyebrow">Public Archive</p>
<h2>일반인용 글</h2>
<div class="grid compact-grid">
{public_cards}
</div>
</section>
<section class="editorial-block">
<p class="eyebrow">Professional Archive</p>
<h2>전문가용 글</h2>
<div class="grid compact-grid">
{pro_cards}
</div>
</section>
</main>
<footer class="site-footer"><p>© 2026 김재필 · Hand 팀 블로그</p></footer>
</body>
</html>
"""
    (ROOT / "hand-team-blog.html").write_text(output, encoding="utf-8")


def main() -> None:
    personal = [post_info(path, "posts/") for path in sorted((ROOT / "posts").glob("*.html"))]
    hand = [post_info(path, "posts/handpt/") for path in sorted((ROOT / "posts" / "handpt").glob("*.html"))]
    write_hobby(personal)
    write_hand(hand)
    public_count = sum(1 for item in hand if "public" in item["href"])
    pro_count = sum(1 for item in hand if "pro" in item["href"])
    print(f"WROTE hobby={len(personal)} hand={len(hand)} public={public_count} pro={pro_count}")


if __name__ == "__main__":
    main()
