"""Compare a reference HTML document with the linear reading order of an EPUB 3 archive."""
import argparse
import hashlib
import json
import posixpath
import re
import unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile, BadZipFile


def clean(s):
    return " ".join(s.split())


class Inventory(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headings=[]
        self.equations=[]
        self.images=0
        self.image_sources=[]
        self.heading=None
        self.in_math=False
        self.ignored=0
        self.math_tokens=[]

    def handle_starttag(self,tag,attrs):
        tag=tag.split(":")[-1]
        if re.fullmatch(r"h[1-6]",tag):
            self.heading=[]
        elif tag=="math":
            self.in_math=True
            self.math_tokens=[]
        elif self.in_math and tag in ("annotation","annotation-xml"):
            self.ignored+=1
        elif tag=="img":
            self.images+=1
            self.image_sources.append(dict(attrs).get("src",""))

    def handle_endtag(self,tag):
        tag=tag.split(":")[-1]
        if re.fullmatch(r"h[1-6]",tag) and self.heading is not None:
            self.headings.append(clean("".join(self.heading)))
            self.heading=None
        elif self.in_math and tag in ("annotation","annotation-xml"):
            self.ignored-=1
        elif tag=="math":
            self.equations.append("".join(self.math_tokens))
            self.in_math=False

    def handle_data(self,data):
        if self.heading is not None and not self.ignored:
            self.heading.append(data)
        if self.in_math and not self.ignored:
            self.math_tokens.append(unicodedata.normalize("NFKC","".join(data.split())))


def resolve(base, ref):
    url=urlsplit(ref)
    if url.scheme or url.netloc:
        return None
    path=unquote(url.path)
    target=posixpath.normpath(posixpath.join(posixpath.dirname(base),path)) if path else base
    return target,unquote(url.fragment)


def compare(html, epub):
    source=Inventory()
    source.feed(html.read_text(encoding="utf-8-sig"))
    book=Inventory()
    issues=[]
    with ZipFile(epub) as z:
        names=set(z.namelist())
        container=ET.fromstring(z.read("META-INF/container.xml"))
        rootfile=container.find(".//{*}rootfile")
        if rootfile is None:
            raise ValueError("No rootfile in container")
        opf=rootfile.attrib["full-path"]
        package=ET.fromstring(z.read(opf))
        manifest={n.attrib["id"]:n for n in package.findall("./{*}manifest/{*}item")}
        spine=package.findall("./{*}spine/{*}itemref")
        if not spine:
            raise ValueError("No reading-order spine")
        identities={}
        links=[]
        image_hashes=set()
        for ref in spine:
            if ref.get("linear")=="no":
                continue
            item=manifest[ref.attrib["idref"]]
            path=resolve(opf,item.attrib["href"])
            if not path or item.get("media-type")!="application/xhtml+xml":
                issues.append({"unsupported_spine_item":item.get("href")})
                continue
            file=path[0]
            raw=z.read(file)
            root=ET.fromstring(raw)
            # XHTML namespaces may use prefixes. Feed element local names to the same inventory.
            def walk(n):
                tag=n.tag.rsplit("}",1)[-1].lower()
                book.handle_starttag(tag,list(n.attrib.items()))
                if n.text: book.handle_data(n.text)
                for child in n:
                    walk(child)
                    if child.tail: book.handle_data(child.tail)
                book.handle_endtag(tag)
            walk(root)
            identities[file]={n.get("id") for n in root.iter() if n.get("id")}
            for n in root.iter():
                tag=n.tag.rsplit("}",1)[-1]
                attr={"a":"href","img":"src","image":"href"}.get(tag)
                if attr:
                    value=n.get(attr) or n.get("{http://www.w3.org/1999/xlink}href")
                    if value:
                        target=resolve(file,value)
                        if target: links.append((file,value,*target))
                        if tag in ("img","image") and target and target[0] in names:
                            image_hashes.add(hashlib.sha256(z.read(target[0])).digest())
        for origin,ref,path,fragment in links:
            if path not in names:
                issues.append({"missing_file":ref,"in":origin})
            elif fragment and path.lower().endswith((".xhtml",".html",".svg")):
                if path not in identities:
                    identities[path]={n.get("id") for n in ET.fromstring(z.read(path)).iter()}
                if fragment not in identities[path]:
                    issues.append({"missing_fragment":ref,"in":origin})
        base=html.resolve().parent
        for src in source.image_sources:
            url=urlsplit(src)
            if url.scheme or url.netloc or not url.path:
                issues.append({"image_needs_manual_comparison":src[:120]})
                continue
            local=(base/unquote(url.path)).resolve()
            if base not in local.parents or not local.is_file():
                issues.append({"reference_image_unavailable":src})
            elif hashlib.sha256(local.read_bytes()).digest() not in image_hashes:
                issues.append({"source_image_bytes_not_matched":src})
    # Converters may add cover or title headings; source headings must survive in order.
    pos=0
    for h in source.headings:
        try:
            pos=book.headings.index(h,pos)+1
        except ValueError:
            issues.append({"missing_or_reordered_heading":h})
    if source.equations!=book.equations:
        issues.append({"math_tokens_changed":{"source":source.equations,"epub":book.equations}})
    if book.images<source.images:
        issues.append({"fewer_img_elements":{"source":source.images,"epub":book.images}})
    return {"result":"review" if issues else "pass","reference_headings":len(source.headings),
            "reference_equations":len(source.equations),"reference_images":source.images,"issues":issues}


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html",type=Path)
    ap.add_argument("epub",type=Path)
    args=ap.parse_args()
    try:
        report=compare(args.html,args.epub)
    except (OSError, BadZipFile, KeyError, ValueError, ET.ParseError) as exc:
        ap.exit(2,f"Input error: {exc}\n")
    print(json.dumps(report,ensure_ascii=True,indent=2))
    raise SystemExit(int(bool(report["issues"])))
