# UglyRAG

一个基于 [SQLite](https://www.sqlite.org/fts5.html) 和 [sqlite-vec](https://github.com/asg017/sqlite-vec) 搭建的 Retrieval-Augmented Generation (RAG) 搜索引擎，可以方便的嵌入到各种 LLM 的应用场景中。

## 特性

- 轻量：只利用了 SQLite 来实现索引和搜索工作，最小安装（通过网络调用分词器、向量模型等）需求为 22MB 左右。
- 扩展：用户可以方便的引入自定义的分词器、向量模型、或者重排序模型。
- 专注：只关注最基础的索引和搜索工程化方面的工作，跟 LLM 的交互由用户自行完成。
- 离线：可以利用 FastEmbed 在本地进行的向量计算，不需要网络连接。

## 快速开始

### 安装依赖包

```bash
pip install uglyrag
```

如果需要 `FastEmbed` 或 `Jieba` 等模块，可以使用如下命令安装：

```bash
pip install uglyrag[fastembed,jieba]
```

### 构建索引

```python
from uglyrag import SearchEngine
SearchEngine.build(docs)
```

### 搜索

```python
from uglyrag import SearchEngine
query = "如何使用 UglyRAG"
results = SearchEngine.search(query)
for id,result in results:
    print(result)
```

### 使用自定义的各种模块

```python
from uglyrag import SearchEngine
# 自定义分词器
def segment(text:str)-> List[str]:
    ...
SearchEngine.segment = segment

# 自定义向量模型
def embeds(texts:List[str])-> List[List[float]]:
    ...
SearchEngine.embeddings = embeds

# 自定义重排序模型
def ranker(query:str, docs:List[str])-> List[float]:
    ...
SearchEngine.ranker = ranker

# 主流程
SearchEngine.build(docs)
...
```
