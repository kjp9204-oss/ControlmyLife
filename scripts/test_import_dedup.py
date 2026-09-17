"""Offline regression tests for public post identity and RSS coverage."""
import unittest
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from import_naver_posts import select_new_items, image_extension, article_excerpt


def feed(*ids):
    root = ET.Element('rss')
    channel = ET.SubElement(root, 'channel')
    for post_id in ids:
        node = ET.SubElement(channel, 'item')
        for key, value in {'link': f'https://blog.naver.com/kjp9204/{post_id}?fromRss=true',
                           'pubDate': 'Thu, 17 Sep 2026 10:00:00 +0900',
                           'title': 'A public article', 'description': 'Public content'}.items():
            ET.SubElement(node, key).text = value
    old = ET.SubElement(channel, 'item')
    ET.SubElement(old, 'pubDate').text = 'Sun, 06 Sep 2026 10:00:00 +0900'
    ET.SubElement(old, 'link').text = 'https://blog.naver.com/kjp9204/999'
    ET.SubElement(old, 'title').text = 'Older article'
    ET.SubElement(old, 'description').text = 'Older public content'
    return root


class SelectionTests(unittest.TestCase):
    def test_existing_id_is_not_reimported(self):
        self.assertEqual(select_new_items(feed('123'), [{'id': '123'}], '2026-09-07'), [])

    def test_repeated_feed_item_appears_once(self):
        self.assertEqual(len(select_new_items(feed('123', '123'), [], '2026-09-07')), 1)

    def test_new_id_survives(self):
        self.assertEqual(select_new_items(feed('123', '456'), [{'id': '123'}], '2026-09-07')[0]['id'], '456')

    def test_corrupt_manifest_is_rejected(self):
        with self.assertRaises(ValueError):
            select_new_items(feed(), [{'id': '123'}, {'id': '123'}], '2026-09-07')

    def test_incomplete_date_coverage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'does not cover'):
            select_new_items(feed('123'), [], '2026-08-01')

    def test_generic_binary_jpeg_is_supported(self):
        self.assertEqual(image_extension(b'\xff\xd8\xffsample', 'application/octet-stream'), '.jpg')

    def test_jpg_mime_alias_is_supported(self):
        self.assertEqual(image_extension(b'\xff\xd8\xffsample', 'image/jpg'), '.jpg')

    def test_generic_html_is_not_an_image(self):
        self.assertIsNone(image_extension(b'<html>denied</html>', 'application/octet-stream'))

    def test_error_page_with_html_mime_is_rejected(self):
        self.assertIsNone(image_extension(b'<html>denied</html>', 'text/html'))

    def test_excerpt_skips_tags_and_links(self):
        prose = 'This is the original opening paragraph with enough useful detail.'
        body = BeautifulSoup('<p class="se-text-paragraph">https://example.com/' + 'x'*60 + '</p><p class="se-text-paragraph">#' + 'tag '*30 + '</p><p class="se-text-paragraph">' + prose + '</p>', 'html.parser')
        self.assertEqual(article_excerpt(body, 'fallback'), prose)

    def test_excerpt_keeps_inline_word_boundaries(self):
        prose = 'This is a sentence with inline formatting and sufficient length.'
        body = BeautifulSoup('<p class="se-text-paragraph">This is a <b>sentence</b> with inline formatting and sufficient length.</p>', 'html.parser')
        self.assertEqual(article_excerpt(body, 'fallback'), prose)

    def test_excerpt_fallback_when_no_prose_exists(self):
        self.assertEqual(article_excerpt(BeautifulSoup('<p>Short</p>', 'html.parser'), 'RSS'), 'RSS')


if __name__ == '__main__':
    unittest.main()
