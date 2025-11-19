from webscraping.ingest_shared.shared import chunk as chunk_mod
from webscraping.ingest_shared.shared import parse_html


def test_clean_text_normalizes_whitespace():
    assert parse_html._clean_text(" Hello   world \n  test ") == "Hello world test"


def test_extract_main_html_filters_elements():
    html = """
    <html>
      <head><title>Example</title></head>
      <body>
        <nav>nav content</nav>
        <main>
          <h1>Main Heading</h1>
          <p> Paragraph 1 </p>
          <footer>footer</footer>
          <p>Paragraph 2</p>
        </main>
      </body>
    </html>
    """
    title, blocks = parse_html.extract_main_html(html)
    assert title == "Example"
    assert [b.text for b in blocks] == ["Main Heading", "Paragraph 1", "Paragraph 2"]
    assert blocks[0].tag == "h1"


def test_iter_text_yields_in_order():
    blocks = [parse_html.HtmlBlock(tag="p", text="one"), parse_html.HtmlBlock(tag="p", text="two")]
    assert list(parse_html.iter_text(blocks)) == ["one", "two"]


def test_chunk_blocks_respects_sections_and_pages():
    blocks = [
        {"text": "Intro text", "tag": "p", "page": 1},
        {"text": "Section A", "tag": "h2", "page": 1},
        {"text": "Detail 1", "tag": "p", "page": 2},
        {"text": "Detail 2", "tag": "p", "page": 3},
        {"text": "Long text here", "tag": "p", "page": 4},
    ]
    chunks = chunk_mod.chunk_blocks(blocks, max_chars=20)
    assert len(chunks) >= 2
    assert chunks[0].section is None
    assert chunks[1].section == "Section A"
    assert chunks[1].start_page == 2
    assert all(isinstance(chunk.text, str) and chunk.text for chunk in chunks)
