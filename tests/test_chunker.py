from src.chunker import chunk_pages
from src.document_loader import DocumentPage


def test_chunking_preserves_metadata_and_overlap() -> None:
    page = DocumentPage(text="word " * 500, source="demo.txt", page=3)
    chunks = chunk_pages([page], chunk_size=300, overlap=50)

    assert len(chunks) > 1
    assert all(chunk.source == "demo.txt" for chunk in chunks)
    assert all(chunk.page == 3 for chunk in chunks)
    assert len({chunk.id for chunk in chunks}) == len(chunks)
    assert all(len(chunk.text) <= 300 for chunk in chunks)


def test_invalid_overlap_is_rejected() -> None:
    page = DocumentPage(text="hello", source="demo.txt", page=1)
    try:
        chunk_pages([page], chunk_size=100, overlap=100)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for overlap >= chunk_size")
