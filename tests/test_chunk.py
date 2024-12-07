import re

import pytest

from uglyrag._loader._chunk import (
    BLOCK_QUOTES_PATTERN,
    CITATION_PATTERN,
    CODE_BLOCK_PATTERN,
    FRONTMATTER_PATTERN,
    HEADING_PATTERN,
    HORIZONTAL_RULE_PATTERN,
    HTML_TAG_PATTERN,
    LATEX_PATTERN,
    LIST_PATTERN,
    MAX_HEADING_CONTENT_LENGTH,
    MAX_HEADING_UNDERLINE_LENGTH,
    MAX_HTML_TABLE_LENGTH,
    MAX_HTML_TAG_ATTRIBUTES_LENGTH,
    MAX_LIST_ITEM_LENGTH,
    MAX_MATH_BLOCK_LENGTH,
    MAX_MATH_INLINE_LENGTH,
    MAX_TABLE_CELL_LENGTH,
    QUOTE_END,
    SENTENCE_END,
    SENTENCE_PATTERN,
    STANDALONE_LINE_PATTERN,
    TABLE_PATTERN,
)


def match(text: str, pattern):
    return re.search(pattern, text) is not None


def find(text: str, pattern):
    text = f"{text}\n"
    matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE | re.UNICODE)
    if matches and len(matches) == 1 and matches[0].strip() == text.strip():
        return True
    return False


@pytest.mark.parametrize(
    "text, expected",
    [
        ("It's a test.", False),
        ("It's a test.'`", True),
        ("It''s a test.", False),
        ("It's a test.''``", True),
        ("It's a test.’", True),
        ("It's a test.” ", True),
        ("It's a test.’‘", True),
        ("It's a test.”“", True),
        ("It is a test.", False),
    ],
)
def test_quote_end(text, expected):
    assert match(text, QUOTE_END) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hello.", True),
        ("What is your name?", True),
        ("She said, 'Hello!'", True),
        ("你好。", True),
        ("e.g.", True),
        ("It's a test.'`", True),
        ("It's a test.''``", True),
        ("It's a test.’‘", True),
        ("It's a test.”“", True),
        ("Hello", False),
        ("She said, 'Hello' and then", False),
        ("“Hello”", True),
        ("Hello?>", False),
        ("Hello。》", False),
    ],
)
def test_sentence_end(text, expected):
    assert match(text, SENTENCE_END) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("This is a test sentence.", True),
        ("这是另一句中文句子。", True),
        (
            "这篇文章探讨了大型语言模型（LLMs）在隐式推理中的表现，发现尽管隐式推理理论上更为高效，但实际上并不等同于显式推理链（CoT）。研究表明，LLMs在进行隐式推理时并未真正进行逐步计算，而是依赖于经验和直觉，这使得其推理过程不稳定且不可靠。文章通过实验验证了这一点，并强调了显式CoT方法在处理复杂任务时的必要性。",
            True,
        ),
        ("Sentence with Unicode punctuation：", True),
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
    assert find(text, SENTENCE_PATTERN) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
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
    ],
)
def test_frontmatter_pattern(text, expected):
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
        ("[1] This is a citation.", True),
        ("[2] Another citation with more text that exceeds the MAX_STANDALONE_LINE_LENGTH if necessary.", True),
        (
            "[^1]: 这里的本质是映射 $\\theta\\rightarrow\\phi$ 的逆映射 $\\phi\\rightarrow\\theta$ 会将尺度 $\\frac{1}{\\lambda}$ 变成 $\\lambda$",
            True,
        ),
        (
            "[1] This is a citation.\n[2] Another citation with more text that exceeds the MAX_STANDALONE_LINE_LENGTH if necessary.",
            False,
        ),
        ("[1] This is a citation.[2] This is a citation.", True),
        ("This is not a citation.", False),
        ("Another example without citation format.", False),
    ],
)
def test_citation_pattern(text, expected):
    assert find(text, CITATION_PATTERN) == expected


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
def test_block_quote(text, expected):
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
def test_code_block(text, expected):
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
        ("$" + "ab" + "$", True),
        ("This is some text without math.", False),
        ("$" + "ab" + "$ kkkkkkk", False),
        ("$" + "a" * MAX_MATH_INLINE_LENGTH + "$", True),
        ("$" + "a" * (MAX_MATH_INLINE_LENGTH + 1) + "$", False),
    ],
)
def test_latex_pattern(text, expected):
    assert find(text, LATEX_PATTERN) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("<header>This is a standalone line with HTML tags.</header>", True),
        (
            "<test>This is a standalone line with HTML tags.</test>\n<test>This is a standalone line with HTML tags.</test>",
            False,
        ),
        (
            "<"
            + "a" * (MAX_HTML_TAG_ATTRIBUTES_LENGTH + 2)
            + ">This line is way too long to be considered a standalone line.</"
            + "a" * (MAX_HTML_TAG_ATTRIBUTES_LENGTH + 2)
            + ">",
            False,
        ),
        ("avoid this line", False),
    ],
)
def test_standalone_line(text, expected):
    assert find(text, STANDALONE_LINE_PATTERN) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("<div> Hello World </div>", True),
        ("<p> Short paragraph.\n</p>", True),
        ("<img src='example.jpg' alt='Example' />", True),
        ("<br />", True),
        ("<a href='http://example.com'>Link</a>", True),
        ("<div>Hello World", False),  # 缺少关闭标签
        ("<p>Short paragraph", False),  # 缺少关闭标签
        ("<img src='example.jpg' alt='Example", False),  # 缺少关闭标签
        ("<br", False),  # 缺少关闭标签
        ("<a href='http://example.com'>Link</", False),  # 缺少关闭标签
        ("Not even close", False),  # 不是HTML标签
        ("<div>Invalid<div>", False),  # 未闭合的标签
    ],
)
def test_html_tag(text, expected):
    assert find(text, HTML_TAG_PATTERN) == expected
