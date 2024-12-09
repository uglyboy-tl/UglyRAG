# url: https://gist.github.com/hanxiao/3f60354cf6dc5ac698bc9154163b4e6a
# Updated: Aug. 20, 2024
# Run: node testRegex.js whatever.txt
# Live demo: https://jina.ai/tokenizer
# LICENSE: Apache-2.0 (https://www.apache.org/licenses/LICENSE-2.0)
# COPYRIGHT: Jina AI

import re

# Define variables for magic numbers
MAX_HEADING_LENGTH = 6
MAX_HEADING_CONTENT_LENGTH = 200
MAX_HEADING_UNDERLINE_LENGTH = 200
MAX_HTML_HEADING_ATTRIBUTES_LENGTH = 100
MAX_LIST_ITEM_LENGTH = 200
MAX_NESTED_LIST_ITEMS = 6
MAX_LIST_INDENT_SPACES = 7
MAX_BLOCKQUOTE_LINE_LENGTH = 200
MAX_BLOCKQUOTE_LINES = 15
MAX_CODE_BLOCK_LENGTH = 1500
MAX_CODE_LANGUAGE_LENGTH = 20
MAX_INDENTED_CODE_LINES = 20
MAX_TABLE_CELL_LENGTH = 200
MAX_TABLE_ROWS = 20
MAX_HTML_TABLE_LENGTH = 2000
MIN_HORIZONTAL_RULE_LENGTH = 3
MAX_SENTENCE_LENGTH = 400
MAX_QUOTED_TEXT_LENGTH = 300
MAX_PARENTHETICAL_CONTENT_LENGTH = 200
MAX_NESTED_PARENTHESES = 5
MAX_MATH_INLINE_LENGTH = 100
MAX_MATH_BLOCK_LENGTH = 500
MAX_PARAGRAPH_LENGTH = 1000
MAX_STANDALONE_LINE_LENGTH = 800
MAX_HTML_TAG_ATTRIBUTES_LENGTH = 100
MAX_HTML_TAG_CONTENT_LENGTH = 1000
LOOKAHEAD_RANGE = 100  # Number of characters to look ahead for a sentence boundary

# 定义整体的句子分词模式，结合各种子模式
# 定义句子开头应避免的字符模式
AVOID_AT_START = r"[\s\]})>,'\uff09\u3011\u3009\u300B\u300D\u300F\u3001\uFF0C\u2019\u201D]"
# 定义常见的句子结束的标点符号
PUNCTUATION = r"(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\u3002\uFF1F\uFF01\uFF1B])"
# 定义引号结束的模式
QUOTE_END = r"(?:'(?=`)|''(?=``)|\u2019(?=\u2018)|\u201D(?=\u201C)|[\"'`\u2019\u201D](?=\s*$))"
# 定义句子通常结束的模式，考虑标点符号和引号结束
SENTENCE_END = rf"(?:{PUNCTUATION}(?!{AVOID_AT_START})|{QUOTE_END})(?=\S|$)"
# 定义句子边界的模式，包括换行符
SENTENCE_BOUNDARY = rf"(?:{SENTENCE_END}|(?=[\r\n]|$))"
# 定义向前查找模式，匹配句子结束周围的字符，不超过一定范围
LOOKAHEAD_PATTERN = rf"(?:(?!{SENTENCE_END}).){{1,{LOOKAHEAD_RANGE}}}{SENTENCE_END}"
# 定义模式以确保当前位置不是标点符号和空格
NOT_PUNCTUATION_SPACE = rf"(?!{PUNCTUATION}\s)"

# 该模式避免在标点符号或空格处开始，匹配句子内容直到最大长度，并识别句子边界
SENTENCE_PATTERN = rf"{NOT_PUNCTUATION_SPACE}(?:[^\r\n]{{1,{{MAX_LENGTH}}}}{SENTENCE_BOUNDARY}|[^\r\n]{{1,{{MAX_LENGTH}}}}(?={PUNCTUATION}|{QUOTE_END})(?:{LOOKAHEAD_PATTERN})?){AVOID_AT_START}*"


def get_sentence_pattern(max_length: int) -> str:
    return f"(?!{AVOID_AT_START}){NOT_PUNCTUATION_SPACE}(?:[^\\r\\n]{{1,{max_length}}}{SENTENCE_BOUNDARY}|[^\\r\\n]{{1,{max_length}}}(?={PUNCTUATION}|{QUOTE_END})(?:{LOOKAHEAD_PATTERN})?){AVOID_AT_START}*"


# FrontMatter
FRONTMATTER_PATTERN = "(?:\\A\\s*(?:---[\\s\\S]+?---))"

# 6. Horizontal rules (Markdown and HTML hr tag)
HORIZONTAL_RULE_PATTERN = f"(?:^(?:[-*_]){{{MIN_HORIZONTAL_RULE_LENGTH},}}\\s*$|(?:^|\\s+)[=]{{5,}}\\s*$|<hr\\s*/?>)"

# 1. Headings (Setext-style, Markdown, and HTML-style, with length constraints)
HEADING_PATTERN = f"(?:^(?:[#*=-]{{1,{MAX_HEADING_LENGTH}}}\\s+|<h[1-6][^>]{{0,{MAX_HTML_HEADING_ATTRIBUTES_LENGTH}}}>)[^\\r\\n]{{1,{MAX_HEADING_CONTENT_LENGTH}}}(?:</h[1-6]>)?(?:\\r?\\n|$)|\\w[^\\r\\n]{{0,{MAX_HEADING_CONTENT_LENGTH}}}\\r?\\n[-=]{{2,{MAX_HEADING_UNDERLINE_LENGTH}}})"

# New pattern for citations
CITATION_PATTERN = f"(?:(?:\\[[0-9]+\\]|\\[\\^[0-9]+\\]:)\\s+{get_sentence_pattern(MAX_BLOCKQUOTE_LINE_LENGTH)})"

# 2. Tables (Markdown, grid tables, and HTML tables, with length constraints)
TABLE_PATTERN = f"(?:(?:^|\\r?\\n)(?:\\|[^\\r\\n]{{0,{MAX_TABLE_CELL_LENGTH}}}\\|(?:\\r?\\n(?:\\|[-:]{{1,{MAX_TABLE_CELL_LENGTH}}})*\\|){{0,1}}(?:\\r?\\n\\|[^\\r\\n]{{0,{MAX_TABLE_CELL_LENGTH}}}\\|){{0,{MAX_TABLE_ROWS}}}|<table>[\\s\\S]{{0,{MAX_HTML_TABLE_LENGTH}}}?</table>))"

# 3. Block quotes (including nested quotes and citations, up to three levels, with length constraints)
BLOCK_QUOTES_PATTERN = (
    f"(?:^(?:>(?:>){{0,2}}\\s+{get_sentence_pattern(MAX_BLOCKQUOTE_LINE_LENGTH)}\\r?\\n){{1,{MAX_BLOCKQUOTE_LINES}}})"
)

# 4. List items (bulleted, numbered, lettered, or task lists, including nested, up to three levels, with length constraints)
LIST_PATTERN = f"(?:(?:^|\\r?\\n)[ \\t]{{0,3}}(?:[-*+•]|\\d{{1,3}}\\.|\\w\\.|\\[[ xX]\\])[ \\t]+{get_sentence_pattern(MAX_LIST_ITEM_LENGTH)}\\r?\\n(?:(?:\\r?\\n[ \\t]{{2,5}}(?:[-*+•]|\\d{{1,3}}\\.|\\w\\.|\\[[ xX]\\])[ \\t]+{get_sentence_pattern(MAX_LIST_ITEM_LENGTH)}){{0,{MAX_NESTED_LIST_ITEMS}}}(?:\\r?\\n[ \\t]{{4,{MAX_LIST_INDENT_SPACES}}}(?:[-*+•]|\\d{{1,3}}\\.|\\w\\.|\\[[ xX]\\])[ \\t]+{get_sentence_pattern(MAX_LIST_ITEM_LENGTH)}){{0,{MAX_NESTED_LIST_ITEMS}}}))+"
# LIST_PATTERN = f"(?:(?:(?:^|\\r?\\n)[ \\t]{{0,3}}(?:[-*+•]|\\d{{1,3}}\\.|\\w\\.|\\[[ xX]\\])[ \\t]+{get_sentence_pattern(MAX_LIST_ITEM_LENGTH)}\\r?\\n))+"

# 5. Code blocks (fenced, indented, or HTML pre/code tags, with length constraints)
CODE_BLOCK_PATTERN = f"(?:^(?:|\\r?\\n)(?:```|~~~)(?:\\w{{0,{MAX_CODE_LANGUAGE_LENGTH}}})?\\r?\\n[\\s\\S]{{0,{MAX_CODE_BLOCK_LENGTH}}}?(?:```|~~~)\\r?\\n?|(?:(?:^|\\r?\\n)(?: {{4}}|\\t)[^\\r\\n]{{0,{MAX_LIST_ITEM_LENGTH}}}(?:\\r?\\n(?: {{4}}|\\t)[^\\r\\n]{{0,{MAX_LIST_ITEM_LENGTH}}}){{0,{MAX_INDENTED_CODE_LINES}}}\\r?\\n?)|(?:<pre>(?:<code>)?[\\s\\S]{{0,{MAX_CODE_BLOCK_LENGTH}}}?(?:</code>)?</pre>))"

# 10. Standalone lines or phrases (including single-line blocks and HTML elements, with length constraints)
STANDALONE_LINE_PATTERN = f"(?!{AVOID_AT_START})(?:^(?:<[a-zA-Z][^>]{{0,{MAX_HTML_TAG_ATTRIBUTES_LENGTH}}}>)\\s*{get_sentence_pattern(MAX_STANDALONE_LINE_LENGTH)}(?:</[a-zA-Z]+>)?(?:\r?\n|$))"

# 9. Paragraphs (with length constraints) 前有有换行的是段落，字数可以比较多。
PARAGRAPH_PATTERN = f"(?:(?:^|\\r?\\n)(?:<p>)?\\s*{get_sentence_pattern(MAX_PARAGRAPH_LENGTH)}(?:</p>)?(?=\\r?\\n|$))"

# 7. Sentences or phrases ending with punctuation (including ellipsis and Unicode punctuation) 非段落的句子，可能是格式不符合的一些内容，也可能是段落因为字数太多，导致无法识别。
SENTENCE_PATTERN = get_sentence_pattern(MAX_SENTENCE_LENGTH)

# 8. Quoted text, parenthetical phrases, or bracketed content (with length constraints)
QUOTED_TEXT_PATTERN = (
    r"(?:"
    rf'(?<!\w)"""[^"]{{0,{MAX_QUOTED_TEXT_LENGTH}}}"""(?!\w)'
    rf'|(?<!\w)"[^"\r\n]{{0,{MAX_QUOTED_TEXT_LENGTH}}}"(?!\w)'
    rf"|(?<!\w)'[^'\r\n]{{0,{MAX_QUOTED_TEXT_LENGTH}}}'(?!\w)"
    rf"|(?<!\w)`[^`\r\n]{{0,{MAX_QUOTED_TEXT_LENGTH}}}`(?!\w)"
    rf"|(?<!\w)`[^\r\n]{{0,{MAX_QUOTED_TEXT_LENGTH}}}'(?!\w)"
    rf"|(?<!\w)``[^\r\n]{{0,{MAX_QUOTED_TEXT_LENGTH}}}''(?!\w)"
    r"|\([^\r\n()]"
    rf"{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}(?:\([^\r\n()]{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}\)[^\r\n()]{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}){{0,{MAX_NESTED_PARENTHESES}}}\)"
    r"|\[[^\r\n\[\]]"
    rf"{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}(?:\[[^\r\n\[\]]{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}\][^\r\n\[\]]{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}){{0,{MAX_NESTED_PARENTHESES}}}\]"
    r"|\$[^\r\n$]" + rf"{{0,{MAX_MATH_INLINE_LENGTH}}}\$"
    r"|`[^`\r\n]" + rf"{{0,{MAX_MATH_INLINE_LENGTH}}}`"
    r")"
)

# 11. HTML-like tags and their content (including self-closing tags and attributes, with length constraints)
HTML_TAG_PATTERN = f"(?:<[a-zA-Z][^>]{{0,{MAX_HTML_TAG_ATTRIBUTES_LENGTH}}}(?:>[\\s\\S]{{0,{MAX_HTML_TAG_CONTENT_LENGTH}}}</[a-zA-Z]+>|\\s*/>))"

# 12. LaTeX-style math expressions (inline and block, with length constraints)
LATEX_PATTERN = f"(?:(?:\\$\\$[\\s\\S]{{0,{MAX_MATH_BLOCK_LENGTH}}}?\\$\\$)|(?:^\\s*\\$[^\\$\\r\\n]{{1,{MAX_MATH_INLINE_LENGTH}}}\\$\\s*$))"

# 14. Fallback for any remaining content (with length constraints)
FALLBACK_REMAINING_PATTERN = get_sentence_pattern(MAX_STANDALONE_LINE_LENGTH)

# 生成正则表达式的字符串
FULL_PATTERN = f"({FRONTMATTER_PATTERN}|{HORIZONTAL_RULE_PATTERN}|{HEADING_PATTERN}|{CITATION_PATTERN}|{TABLE_PATTERN}|{BLOCK_QUOTES_PATTERN}|{LIST_PATTERN}|{CODE_BLOCK_PATTERN}|{LATEX_PATTERN}|{STANDALONE_LINE_PATTERN}|{PARAGRAPH_PATTERN}|{QUOTED_TEXT_PATTERN}|{SENTENCE_PATTERN}?|{HTML_TAG_PATTERN}|{FALLBACK_REMAINING_PATTERN})"


# 使用 re 进行编译
regex = re.compile(FULL_PATTERN, re.DOTALL | re.MULTILINE | re.UNICODE)


def split_text(text: str) -> list[str]:
    # Apply the regex
    chunks = regex.findall(text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]
