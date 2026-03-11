import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_service import split_text_into_blocks


def test_split_double_newline():
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    blocks = split_text_into_blocks(text)
    assert blocks == ["Paragraph one.", "Paragraph two.", "Paragraph three."]


def test_split_multiple_newlines():
    text = "Block A.\n\n\n\nBlock B."
    blocks = split_text_into_blocks(text)
    assert blocks == ["Block A.", "Block B."]


def test_split_strips_whitespace():
    text = "  Block A.  \n\n  Block B.  "
    blocks = split_text_into_blocks(text)
    assert blocks == ["Block A.", "Block B."]


def test_split_single_block():
    text = "Just one block with no double newlines."
    blocks = split_text_into_blocks(text)
    assert blocks == ["Just one block with no double newlines."]


def test_split_empty_string():
    assert split_text_into_blocks("") == []
    assert split_text_into_blocks("   ") == []


def test_split_filters_empty_blocks():
    text = "Block A.\n\n\n\n\n\nBlock B."
    blocks = split_text_into_blocks(text)
    assert len(blocks) == 2
