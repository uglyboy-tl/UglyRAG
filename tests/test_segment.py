import re

import pytest

from uglyrag._segment import (
    BLOCK_QUOTES_PATTERN,
    CODE_BLOCK_PATTERN,
    FRONTMATTER_PATTERN,
    HEADING_PATTERN,
    HORIZONTAL_RULE_PATTERN,
    LATEX_PATTERN,
    LIST_PATTERN,
    MAX_HEADING_CONTENT_LENGTH,
    MAX_HEADING_UNDERLINE_LENGTH,
    MAX_HTML_TABLE_LENGTH,
    MAX_LIST_ITEM_LENGTH,
    MAX_MATH_BLOCK_LENGTH,
    MAX_MATH_INLINE_LENGTH,
    MAX_TABLE_CELL_LENGTH,
    TABLE_PATTERN,
    get_sentence_pattern,
)


def find(text: str, pattern):
    text = f"{text}\n"
    matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE | re.UNICODE)
    if matches and len(matches) == 1 and matches[0].strip() == text.strip():
        return True
    return False


@pytest.mark.parametrize(
    "text, expected",
    [
        ("This is a test sentence.", True),
        ("Another example, with a comma!", True),
        ("A sentence with a quote at the end'", True),
        ("A very long sentence that exceeds the maximum length and should not match" * 10, False),
        ("A sentence without any boundary or punctuation", True),
        ("A sentence with a newline\nin it", False),
        ("A sentence with three dots...", True),
        ("?", False),
    ],
)
def test_sentence_pattern(text, expected):
    assert find(text, get_sentence_pattern(100)) == expected

@pytest.mark.parametrize("text, expected", [
    ("", False),  # 空字符串，不匹配
    ("---\nfront matter\n---", True),  # 有效的front matter，匹配
    ("no front matter", False),  # 没有front matter，不匹配
    ("---\nonly part of front matter", False),  # front matter未闭合，不匹配
    ("some text\n---\nfront matter\n---", False),  # front matter在文本中间，不匹配
    ("---\nfront matter\n---\nsome text", False),  # front matter在文本末尾，匹配
    ("front matter\n---\n", False),  # front matter为空，不匹配
    ("---\n---", True),  # 空的front matter，匹配
    ("some text\n---\n", False),  # 文本后跟未闭合的front matter，不匹配
    ("---\nsome text\n---", True),  # front matter在文本前后，匹配
    ("", False),  # 空字符串，不匹配
    ("some text", False),  # 没有front matter的文本，不匹配
    ("---\nfront matter", False),  # 未闭合的front matter，不匹配
    ("front matter\n---", False),  # 未闭合的front matter，不匹配
    ("---\nfront\nmatter\n---", True),  # 多行front matter，匹配
    ("some text\n---\nfront\nmatter\n---", False),  # 文本中包含多行front matter，匹配
    ("---\nsome text\nfront\nmatter\n---", True),  # 文本末尾包含多行front matter，匹配
])
def test_frontmatter(text, expected):
    assert find(text, FRONTMATTER_PATTERN) == expected

@pytest.mark.parametrize(
    "text, expected",
    [
        ("# Heading 1", True),
        ("## Heading 2", True),
        ("### Heading 3", True),
        ("#### Heading 4", True),
        ("##### Heading 5", True),
        ("###### Heading 6", True),
        ("####### Heading 7", False),  # 超过最大长度
        ("Heading 1\n=======", True),
        ("Heading 2\n-------", True),
        ("Heading 2\n" + "-" * (MAX_HEADING_UNDERLINE_LENGTH + 1), False),  # 超过最大长度
        ("<h1>Heading 1</h1>", True),
        ("<h2>Heading 2</h2>", True),
        ("<h3>Heading 3</h3>", True),
        ("<h4>Heading 4</h4>", True),
        ("<h5>Heading 5</h5>", True),
        ("<h6>Heading 6</h6>", True),
        ("<h7>Heading 7</h7>", False),  # 无效的 HTML 标签
        ("<h1 class='test'>Heading 1</h1>", True),
        ("<h2 id='test'>Heading 2</h2>", True),
        ("<h3 style='color: red;'>Heading 3</h3>", True),
        ("<h4 data-test='value'>Heading 4</h4>", True),
        ("<h5 class='test' id='test'>Heading 5</h5>", True),
        ("<h6 data-test='value' class='test'>Heading 6</h6>", True),
        ("<h7 data-test='value' class='test'>Heading 7</h7>", False),
        ("<h1 class='test' id='test' style='color: red;'>Heading 1</h1>", True),
        ("<h1 class='test' id='test' style='color: red;' data-test='value'>Heading 1</h1>", True),
        ("<h1 class='test' id='test' style='color: red;' data-test='value' data-test2='value2'>Heading 1</h1>", True),
        (
            "<h1 class='test' id='test' style='color: red;' data-test='value' data-test2='value2' data-test3='value3'>Heading 1</h1>",
            False,
        ),  # 超过最大属性长度
        (
            "A very long heading `"
            + "h" * MAX_HEADING_CONTENT_LENGTH
            + "` that exceeds the maximum allowed content length for headings in this regex pattern\n---",
            False,
        ),  # 超过最大内容长度
    ],
)
def test_heading_pattern(text, expected):
    assert find(text, HEADING_PATTERN) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("> This is a simple blockquote.", True),
        ("> This is a\n>\n> multi-line blockquote.", True),
        (
            "> This is a very long line that exceeds the maximum length of 200 characters(such as xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx), so it should not match the pattern because it is too long and does not fit within the constraints of the regex.",
            False,
        ),
        (
            "> This is a valid blockquote."
            + "\n> line" * 20
            + "> But this line is on the 16th line, which exceeds the max lines allowed.",
            False,
        ),
        ("This is not a blockquote because it does not start with >", False),
        (">> This is a valid blockquote with two spaces after the >", True),
        (">>> This is a valid blockquote with three spaces after the >", True),
        (">>>>> This is a valid blockquote with more than three spaces after the >", False),
    ],
)
def test_is_block_quote(text, expected):
    assert find(text, BLOCK_QUOTES_PATTERN) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("```python\n" + "print('Hello World!')" * 20 + "```", True),
        ("```\nprint('Hello, World!')\nprint('Hello, World!')```", True),
        ("```python\n    def hello_world():\n        print('Hello, World!')\n```", True),
        ("This is a test sentence.", False),
        ("    - item 1\n    - item 2", True),
        ("<pre><code>print('Hello World!')\nprint('Hello World!')</code></pre>", True),
    ],
)
def test_is_code_block(text, expected):
    assert find(text, CODE_BLOCK_PATTERN) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |", True),
        ("<table><tr><th>Header 1</th><th>Header 2</th></tr>\n<tr><td>Cell 1</td><td>Cell 2</td></tr></table>", True),
        ("| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Some else without close", False),
        ("<table><tr><th>Header 1</th><th>Header 2</th></tr><tr><td>Cell 1</td>", False),
        (f"| {'a' * (MAX_TABLE_CELL_LENGTH + 1)} |", False),
        ("<table><tr><td>" + "a" * (MAX_HTML_TABLE_LENGTH + 1) + "</td></tr></table>", False),
    ],
)
def test_table_pattern(text, expected):
    assert find(text, TABLE_PATTERN) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("- item 1\n- item 2\n- item 3", True),
        ("1. item 1\n2. item 2\n3. item 3", True),
        ("- item 1\n  - nested item 1\n  - nested item 2\n- item 2", True),
        ("a. " + "x" * (MAX_LIST_ITEM_LENGTH + 1), False),
    ],
)
def test_list_pattern(text, expected):
    assert find(text, LIST_PATTERN) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("___", True),
        ("---", True),
        ("*****", True),
        ("<hr>", True),
        ("<hr />", True),
        ("__", False),
        ("=====", True),
        ("====", False),
        ("----==", False),
        ("****==", False),
        ("<hrr>", False),
        ("<hr a />", False),
        ("not a horizontal rule", False),
        ("", False),
    ],
)
def test_horizontal_rule(text, expected):
    assert find(text, HORIZONTAL_RULE_PATTERN) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("$$" + "a" * MAX_MATH_BLOCK_LENGTH + "$$", True),
        ("$$" + "a" * (MAX_MATH_BLOCK_LENGTH + 1) + "$$", False),
        ("$$" + "a\nb" + "$$", True),
        ("$" + "a\nb" + "$", False),
        ("$" + "a" * MAX_MATH_INLINE_LENGTH + "$", True),
        ("$" + "a" * (MAX_MATH_INLINE_LENGTH + 1) + "$", False),
        ("This is some text without math.", False),
    ],
)
def test_latex_pattern(text, expected):
    assert find(text, LATEX_PATTERN) == expected
