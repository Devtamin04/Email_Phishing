#!/usr/bin/env python3
"""Small, dependency-free Markdown to DOCX converter for project reports."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def xtext(value: str) -> str:
    return escape(value, {'"': "&quot;"})


def inline_runs(text: str, size: int | None = None) -> str:
    """Convert the inline Markdown used by the report into Word runs."""
    token_re = re.compile(r"(\*\*.+?\*\*|(?<!\*)\*[^*]+?\*(?!\*)|`[^`]+`)")
    parts = token_re.split(text)
    runs: list[str] = []
    for part in parts:
        if not part:
            continue
        props: list[str] = []
        value = part
        if part.startswith("**") and part.endswith("**"):
            value = part[2:-2]
            props.append("<w:b/>")
        elif part.startswith("*") and part.endswith("*"):
            value = part[1:-1]
            props.append("<w:i/>")
        elif part.startswith("`") and part.endswith("`"):
            value = part[1:-1]
            props.extend((
                '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>',
                '<w:shd w:fill="EDEDED"/>',
            ))
        if size:
            props.extend((f'<w:sz w:val="{size}"/>', f'<w:szCs w:val="{size}"/>'))
        rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
        preserve = ' xml:space="preserve"' if value[:1].isspace() or value[-1:].isspace() else ""
        runs.append(f"<w:r>{rpr}<w:t{preserve}>{xtext(value)}</w:t></w:r>")
    return "".join(runs)


def paragraph(text: str = "", style: str | None = None, *, num_id: int | None = None,
              level: int = 0, before: int | None = None, after: int | None = None,
              keep_next: bool = False, size: int | None = None) -> str:
    ppr: list[str] = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if num_id is not None:
        ppr.append(
            f'<w:numPr><w:ilvl w:val="{level}"/><w:numId w:val="{num_id}"/></w:numPr>'
        )
    spacing = []
    if before is not None:
        spacing.append(f'w:before="{before}"')
    if after is not None:
        spacing.append(f'w:after="{after}"')
    if spacing:
        ppr.append(f"<w:spacing {' '.join(spacing)}/>")
    if keep_next:
        ppr.append("<w:keepNext/>")
    props = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    return f"<w:p>{props}{inline_runs(text, size)}</w:p>"


def table(rows: list[list[str]]) -> str:
    cols = max(len(row) for row in rows)
    grid = "".join(f'<w:gridCol w:w="{9000 // cols}"/>' for _ in range(cols))
    out = [
        "<w:tbl>",
        "<w:tblPr>",
        '<w:tblW w:w="5000" w:type="pct"/>',
        '<w:tblLayout w:type="autofit"/>',
        '<w:tblBorders><w:top w:val="single" w:sz="6" w:color="808080"/>'
        '<w:left w:val="single" w:sz="6" w:color="808080"/>'
        '<w:bottom w:val="single" w:sz="6" w:color="808080"/>'
        '<w:right w:val="single" w:sz="6" w:color="808080"/>'
        '<w:insideH w:val="single" w:sz="4" w:color="B7B7B7"/>'
        '<w:insideV w:val="single" w:sz="4" w:color="B7B7B7"/></w:tblBorders>',
        '<w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
        '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar>',
        "</w:tblPr>",
        f"<w:tblGrid>{grid}</w:tblGrid>",
    ]
    for row_index, row in enumerate(rows):
        out.append("<w:tr>")
        if row_index == 0:
            out.append("<w:trPr><w:tblHeader/></w:trPr>")
        for value in row + [""] * (cols - len(row)):
            shade = '<w:shd w:fill="D9EAF7"/>' if row_index == 0 else ""
            out.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{5000 // cols}" w:type="pct"/>{shade}'
                f'<w:vAlign w:val="center"/></w:tcPr>'
                f'{paragraph(value, after=0, keep_next=row_index == 0, size=19)}'
                '</w:tc>'
            )
        out.append("</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def parse_table(lines: list[str]) -> list[list[str]]:
    return [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]


def markdown_body(source: str) -> str:
    lines = source.splitlines()
    body: list[str] = []
    i = 0
    pending: list[str] = []

    def flush_paragraph() -> None:
        if pending:
            body.append(paragraph(" ".join(part.strip() for part in pending), after=120))
            pending.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            i += 1
            continue
        if stripped == "---":
            flush_paragraph()
            body.append(
                '<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="8" '
                'w:space="1" w:color="9E9E9E"/></w:pBdr><w:spacing w:after="160"/></w:pPr></w:p>'
            )
            i += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            style = "Title" if level == 1 else f"Heading{min(level - 1, 3)}"
            body.append(paragraph(heading.group(2), style, keep_next=True))
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(
            r"^\s*\|?\s*:?-{3,}", lines[i + 1]
        ):
            flush_paragraph()
            table_lines = [line]
            i += 2  # Skip Markdown's separator row.
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            body.append(table(parse_table(table_lines)))
            body.append(paragraph("", after=60))
            continue
        item = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
        ordered = re.match(r"^(\s*)\d+[.)]\s+(.+)$", line)
        if item or ordered:
            flush_paragraph()
            match = item or ordered
            assert match is not None
            level = min(len(match.group(1).replace("\t", "  ")) // 2, 8)
            body.append(paragraph(match.group(2), num_id=1 if item else 2, level=level, after=40))
            i += 1
            continue
        pending.append(stripped)
        i += 1
    flush_paragraph()
    return "".join(body)


def styles_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}">
  <w:docDefaults><w:rPrDefault><w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/>
    <w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="vi-VN"/>
  </w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>
    <w:spacing w:after="120" w:line="276" w:lineRule="auto"/><w:jc w:val="both"/>
  </w:pPr></w:pPrDefault></w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="center"/><w:spacing w:before="0" w:after="280"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="17365D"/><w:sz w:val="36"/><w:szCs w:val="36"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="280" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="1F4E79"/><w:sz w:val="30"/><w:szCs w:val="30"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="220" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="2F75B5"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="180" w:after="80"/><w:outlineLvl w:val="2"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="404040"/><w:sz w:val="23"/><w:szCs w:val="23"/></w:rPr></w:style>
</w:styles>'''


def numbering_xml() -> str:
    levels = []
    for i in range(9):
        bullet = ("•", "–", "○")[i % 3]
        levels.append(
            f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
            f'<w:lvlText w:val="{bullet}"/><w:lvlJc w:val="left"/><w:pPr>'
            f'<w:tabs><w:tab w:val="num" w:pos="{720 + i*360}"/></w:tabs>'
            f'<w:ind w:left="{720 + i*360}" w:hanging="360"/></w:pPr></w:lvl>'
        )
    ordered_levels = []
    for i in range(9):
        ordered_levels.append(
            f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="decimal"/>'
            f'<w:lvlText w:val="%{i+1}."/><w:lvlJc w:val="left"/><w:pPr>'
            f'<w:tabs><w:tab w:val="num" w:pos="{720 + i*360}"/></w:tabs>'
            f'<w:ind w:left="{720 + i*360}" w:hanging="360"/></w:pPr></w:lvl>'
        )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="{W}">
  <w:abstractNum w:abstractNumId="0">{''.join(levels)}</w:abstractNum>
  <w:abstractNum w:abstractNumId="1">{''.join(ordered_levels)}</w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
  <w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>
</w:numbering>'''


def make_docx(markdown: Path, output: Path) -> None:
    content = markdown.read_text(encoding="utf-8")
    body = markdown_body(content)
    document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>{body}
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="567" w:footer="567" w:gutter="0"/></w:sectPr>
</w:body></w:document>'''
    types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="xml" ContentType="application/xml"/>
 <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
 <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
 <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
 <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
 <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''
    root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
 <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
 <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''
    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
 <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>'''
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    core = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <dc:title>Báo cáo paper KD-BiLSTM</dc:title><dc:creator>Devtamin</dc:creator>
 <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''
    app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Markdown to DOCX</Application></Properties>'''

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in {
            "[Content_Types].xml": types,
            "_rels/.rels": root_rels,
            "word/document.xml": document,
            "word/styles.xml": styles_xml(),
            "word/numbering.xml": numbering_xml(),
            "word/_rels/document.xml.rels": doc_rels,
            "docProps/core.xml": core,
            "docProps/app.xml": app,
        }.items():
            archive.writestr(name, data.encode("utf-8"))


def validate_docx(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        required = {"[Content_Types].xml", "word/document.xml", "word/styles.xml"}
        missing = required.difference(archive.namelist())
        if missing:
            raise ValueError(f"DOCX thiếu thành phần: {', '.join(sorted(missing))}")
        for name in archive.namelist():
            if name.endswith((".xml", ".rels")):
                ET.fromstring(archive.read(name))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args()
    output = args.output or args.input.with_suffix(".docx")
    make_docx(args.input, output)
    validate_docx(output)
    print(output)


if __name__ == "__main__":
    main()
