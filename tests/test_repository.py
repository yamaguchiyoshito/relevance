from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import parse_markdown, render, map_url, build, site_index_text
from validate import validate, svg_errors, walk
from check_html import check, Document
from bibliography import bibliography_text


class RepositoryTests(unittest.TestCase):
    def test_entire_repository(self):
        result, errors = validate()
        self.assertEqual(errors, [])
        self.assertEqual(result.chapters, 24)
        total = 0
        for sf in ['series.json', 'series-2/series.json']:
            total += sum(len(c['figures']) for c in json.loads((ROOT / sf).read_text(encoding='utf-8'))['chapters'])
        self.assertEqual(result.svg_files, 1 + total)
        self.assertGreater(result.footnotes, 20)

    def test_footnotes_render_as_notes(self):
        output = render('本文[^a]。\n\n[^a]: 出典。\n')
        self.assertIn('class="footnotes', output)
        self.assertNotIn('<script', output)

    def test_caption_paragraph_becomes_figcaption(self):
        output = render('![代替テキスト](../assets/illustrations/00-cover.svg)\n\n*図1-1：説明。*\n\n次の段落。\n')
        self.assertEqual(output.count('<figcaption'), 1)
        self.assertIn('<figcaption>図1-1：説明。</figcaption>', output)
        self.assertNotIn('<p><em>図1-1', output)
        self.assertIn('alt="代替テキスト"', output)

    def test_alt_only_figure_has_no_caption(self):
        output = render('![表紙の説明](../assets/illustrations/00-cover.svg)\n')
        self.assertEqual(output.count('<figcaption'), 0)
        self.assertIn('alt="表紙の説明"', output)

    def test_tables_are_wrapped_and_unsized(self):
        output = render('| 回 | 文章 |\n| --- | --- |\n| 01 | 本文 |\n')
        self.assertIn('<div class="table-wrap"><table', output)
        self.assertIn('</table></div>', output)
        self.assertNotIn('<col style', output)

    def test_nav_markers_become_nav_cards(self):
        text = '<!-- NAV:TOP -->\n[← 第4回](a.md) | [連載目次](../README.md) | [第6回 →](b.md)\n<!-- /NAV -->\n\n本文\n\n<!-- NAV:BOTTOM -->\n---\n\n[← 第4回](a.md) | [連載目次](../README.md)\n<!-- /NAV -->\n'
        output = render(text, next_note='次回　第6回「題名」')
        self.assertEqual(output.count('<nav class="chapter-nav'), 2)
        self.assertIn('chapter-nav-next">次回　第6回「題名」', output)
        self.assertNotIn('<!-- NAV:', output)
        self.assertNotIn('<h2', output)
        self.assertIn('class="sep"', output)

    def test_dollar_signs_are_not_math(self):
        ast = parse_markdown('価格は $5 と $7 です。\n')
        self.assertFalse(any(n.get('t') == 'Math' for n in walk(ast)))

    def test_site_index_stops_at_marker(self):
        text = '# T\n\n本文\n\n<!-- SITE-INDEX-END -->\n\n## GitHubで読む\n\n運用\n'
        self.assertEqual(site_index_text(text), '# T\n\n本文\n')
        self.assertEqual(site_index_text('# T\n\n本文\n'), '# T\n\n本文\n')
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('## 全12回の目次', site_index_text(readme))
        self.assertNotIn('## GitHubで読む', site_index_text(readme))

    def test_relative_links(self):
        self.assertEqual(map_url('../README.md'), '../index.html')
        self.assertEqual(map_url('one.md#test'), 'one.html#test')
        self.assertEqual(map_url('https://example.org/a.md'), 'https://example.org/a.md')
        self.assertEqual(map_url('../assets/a.svg'), '../assets/a.svg')

    def test_svg_rejects_executable_content(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.svg'
            p.write_text('<svg viewBox="0 0 10 10" role="img"><title>X</title><desc>Y</desc><script>alert(1)</script></svg>')
            self.assertTrue(any('forbidden SVG' in x for x in svg_errors(p)))

    def test_svg_rejects_external_href(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.svg'
            p.write_text('<svg viewBox="0 0 10 10" role="img"><title>X</title><desc>Y</desc><a href="https://example.org"/></svg>')
            self.assertTrue(any('external href' in x for x in svg_errors(p)))

    def test_svg_allows_internal_gradient(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.svg'
            p.write_text('<svg viewBox="0 0 10 10" role="img" aria-labelledby="t d"><title id="t">X</title><desc id="d">Y</desc><defs><radialGradient id="g"/></defs><circle fill="url(#g)" r="1"/></svg>')
            self.assertEqual(svg_errors(p), [])

    def test_svg_rejects_malformed_xml(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.svg'
            p.write_text('<svg>')
            self.assertTrue(svg_errors(p))

    def test_figures_are_reproducible(self):
        before = {str(p): p.read_bytes() for p in (ROOT / 'assets/illustrations').rglob('*.svg')}
        subprocess.run([sys.executable, str(ROOT / 'scripts/draw_figures.py')], check=True, capture_output=True)
        after = {str(p): p.read_bytes() for p in (ROOT / 'assets/illustrations').rglob('*.svg')}
        self.assertEqual(before, after)

    def test_bibliography_is_in_sync(self):
        sources = json.loads((ROOT / 'references/sources.json').read_text(encoding='utf-8'))
        self.assertEqual((ROOT / 'references/bibliography.md').read_text(encoding='utf-8'), bibliography_text(sources))

    def test_publish_defaults_to_dry_run(self):
        p = subprocess.run([sys.executable, str(ROOT / 'scripts/publish.py'), '--owner', 'example'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertIn('DRY RUN', p.stdout)
        self.assertIn('private', p.stdout)

    def test_publish_rejects_path_injection(self):
        p = subprocess.run([sys.executable, str(ROOT / 'scripts/publish.py'), '--owner', '../bad'], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)

    def test_build_refuses_source_overwrite(self):
        with self.assertRaises(RuntimeError):
            build(ROOT)

    def test_combinatorics_in_chapter_eight(self):
        self.assertEqual(2 ** 3 - 1, 7)
        self.assertEqual(100 * 99 * 98 // 6, 161700)
        self.assertEqual(100 * 99 * 98, 970200)

    def test_second_series_metadata(self):
        data = json.loads((ROOT / 'series-2/series.json').read_text(encoding='utf-8'))
        self.assertEqual([c['number'] for c in data['chapters']], list(range(1, 13)))
        self.assertEqual(data['code'], 'RELATION')
        self.assertTrue((ROOT / data['index']).exists())

    def test_chapter_ids_and_sources_are_unique(self):
        data = json.loads((ROOT / 'series.json').read_text(encoding='utf-8'))
        self.assertEqual(len({c['slug'] for c in data['chapters']}), 12)
        for c in data['chapters']:
            self.assertGreaterEqual(len(c['figures']), 1)
            self.assertEqual(len(c['figures']), len(set(c['figures'])))
        for c in data['chapters']:
            self.assertEqual(len(c['sources']), len(set(c['sources'])))

    def test_complete_reader_links_and_figures(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / 'reader'
            build(output)
            report = check(output)
            self.assertEqual(report['errors'], [])
            self.assertEqual(report['chapter_pages'], 24)
            total = 0
            for sf in ['series.json', 'series-2/series.json']:
                total += sum(len(c['figures']) for c in json.loads((ROOT / sf).read_text(encoding='utf-8'))['chapters'])
            self.assertEqual(report['chapter_images'], total)

    def test_combined_footnote_ids_are_namespaced(self):
        text = 'A[^a].\n\n[^a]: A source.\n'
        doc = Document(render(text, prefix='a-') + render(text, prefix='b-'))
        self.assertEqual(len(doc.ids), len(set(doc.ids)))

    def test_html_checker_detects_missing_target(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)
            (output / 'index.html').write_text('<html><a href="missing.html">Link</a></html>')
            self.assertTrue(any('missing target' in e for e in check(output)['errors']))

    def test_html_checker_rejects_network_images(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)
            (output / 'index.html').write_text('<html><img src="https://example.org/image.svg"></html>')
            self.assertTrue(any('external resource' in e for e in check(output)['errors']))


if __name__ == '__main__':
    unittest.main()
