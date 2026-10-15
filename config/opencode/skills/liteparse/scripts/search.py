#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "bm25s>=0.3.9,<1",
#   "aiofiles>=25.1.0,<26",
# ]
# ///
import argparse
import asyncio
from typing import TypedDict

import aiofiles
import bm25s


# number of lines searched together as one BM25 corpus
CHUNK_LINES = 1000


class LineRecord(TypedDict):
    index: int  # position within the chunk
    lineno: int  # line number within the file
    content: str


def _chunk(lines: list[str], offset: int) -> list[LineRecord]:
    return [
        {"index": i, "lineno": offset + i, "content": c} for (i, c) in enumerate(lines)
    ]


def _expand(corpus: list[LineRecord], match: LineRecord, n: int) -> str:
    idx = match["index"]
    start = max(0, idx - n)
    end = min(len(corpus) - 1, idx + n)
    return (
        f"Lines {corpus[start]['lineno']} - {corpus[end]['lineno']}\n\n\n"
        + "\n".join([c["content"] for c in corpus[start : end + 1]])
    )


def _retrieve(
    corpus: list[LineRecord], query: str, top_k: int | None, expand: int = 0
) -> list[tuple[str, float]]:
    corpus_tokens = bm25s.tokenize([c["content"] for c in corpus])
    retriever = bm25s.BM25(corpus=corpus)
    retriever.index(corpus_tokens)
    query_tokens = bm25s.tokenize(query)
    k = min(top_k or 10, len(corpus))
    docs, scores = retriever.retrieve(query_tokens, k=k)

    results: list[tuple[str, float]] = []
    for doc, score in zip(docs[0].tolist(), scores[0].tolist()):
        if expand > 0:
            window = _expand(corpus, doc, expand)
        else:
            window = f"Line {doc['lineno']}\n\n\n{doc['content']}"
        results.append((window, score))
    return results


def _chunk_and_retrieve(
    lines: list[str], offset: int, query: str, top_k: int | None, expand_n: int
) -> list[tuple[str, float]]:
    corpus = _chunk(lines, offset)
    return _retrieve(corpus, query, top_k, expand_n)


async def process_chunk(
    lines: list[str], offset: int, query: str, top_k: int | None, expand_n: int
) -> list[tuple[str, float]]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _chunk_and_retrieve, lines, offset, query, top_k, expand_n
    )


async def read_and_process(
    file_path: str, query: str, top_k: int | None, expand_n: int | None
) -> list[str]:
    async with aiofiles.open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = (await f.read()).splitlines()
    expand = 5 if expand_n is None else expand_n

    tasks: list[asyncio.Task[list[tuple[str, float]]]] = []
    async with asyncio.TaskGroup() as tg:
        for offset in range(0, len(lines), CHUNK_LINES):
            chunk = lines[offset : offset + CHUNK_LINES]
            tasks.append(
                tg.create_task(process_chunk(chunk, offset, query, top_k, expand))
            )
    results = [task.result() for task in tasks]
    flattened = [r for result in results for r in result if r[1] >= 0.5]
    flattened.sort(key=lambda x: x[1], reverse=True)
    n = top_k or 10
    return [f[0] for f in flattened][:n]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", help="Path to the text file to search")
    parser.add_argument(
        "-q", "--query", help="Keyword-based query to search for", required=True
    )
    parser.add_argument(
        "-k",
        "--top-k",
        help="Top K matches to retrieve. Defaults to 10.",
        required=False,
        type=int,
        default=None,
    )
    parser.add_argument(
        "-e",
        "--expand",
        help="Expand the matched content by N lines (before and after). Defaults to 5",
        required=False,
        type=int,
        default=None,
    )
    args = parser.parse_args()
    results = asyncio.run(
        read_and_process(args.file_path, args.query, args.top_k, args.expand)
    )
    if results:
        separator = "\n" + "─" * 60 + "\n"
        for i, r in enumerate(results):
            print(f"Match #{i}")
            print(r.rstrip("\n").lstrip("\n"))
            if i < len(results) - 1:
                print(separator)
    else:
        print("No relevant matches found")


if __name__ == "__main__":
    main()
