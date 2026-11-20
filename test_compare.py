import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from scripts.compare_book import compare

class BookTest(unittest.TestCase):
    def test_spine_html_links_images_and_math(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            html=folder/"book.html"
            html.write_text('<h1>A</h1><h1>B</h1><math><mi>x</mi></math><img src="pic.png">',encoding="utf8")
            (folder/"pic.png").write_bytes(b"original")
            for broken in (False,True):
                epub=folder/"book.epub"
                with ZipFile(epub,"w") as z:
                    z.writestr("META-INF/container.xml",'<container><rootfile full-path="O/book.opf"/></container>')
                    z.writestr("O/book.opf",'<package><manifest><item id="a" href="a.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="a"/></spine></package>')
                    content='<h1>B</h1><h1>A</h1><math><mi>y</mi></math><a href="#gone"/>' if broken else '<h1>A</h1><h1>B</h1><math><mi>x</mi></math><a href="#ok"/>'
                    z.writestr("O/a.xhtml",'<html><body id="ok">'+content+'<img src="p.png"/></body></html>')
                    z.writestr("O/p.png",b"changed" if broken else b"original")
                result=compare(html,epub)
                self.assertEqual(result["result"],"review" if broken else "pass")
                if broken:
                    self.assertEqual({k for i in result["issues"] for k in i if k!="in"},
                        {"missing_fragment","missing_or_reordered_heading","math_tokens_changed","source_image_bytes_not_matched"})
