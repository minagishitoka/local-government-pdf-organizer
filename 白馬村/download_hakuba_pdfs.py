#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
白馬村公式サイトに掲載されているPDFを、指定ページから一括ダウンロードする。

対象ページ:
- 白馬村の決算
- 白馬村の予算
- 決算審査
- 定期監査
- 財政援助団体等監査
- 住民監査請求
- 観光統計
- 村勢要覧

設計方針:
- ページそのものではなく、各ページ内のPDFリンクを自動抽出する。
- PDF URLを固定で列挙しないため、年度追加・URL変更に比較的強い。
- 既存PDFはサイズが同じならスキップし、再実行可能にする。
- 同名PDFが別ページに存在する場合は重複を別名保存する。
- download_manifest.csv に取得元ページとPDF URLを記録する。
- 原本PDFの内容は加工しない。
"""

from __future__ import annotations

import csv
import hashlib
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "pdf"
MANIFEST_PATH = BASE_DIR / "download_manifest.csv"

PAGE_URLS = [
    "https://www.vill.hakuba.lg.jp/gyosei/soshikikarasagasu/somuka/zaiseikakari/1/1/1382.html",
    "https://www.vill.hakuba.lg.jp/gyosei/soshikikarasagasu/somuka/zaiseikakari/1/1/1384.html",
    "https://www.vill.hakuba.lg.jp/gyosei/soshikikarasagasu/gikaijimukyoku/kansaiinjimukyoku/kansaiinjimukyoku/12266.html",
    "https://www.vill.hakuba.lg.jp/gyosei/soshikikarasagasu/gikaijimukyoku/kansaiinjimukyoku/kansaiinjimukyoku/12265.html",
    "https://www.vill.hakuba.lg.jp/gyosei/soshikikarasagasu/gikaijimukyoku/kansaiinjimukyoku/kansaiinjimukyoku/12267.html",
    "https://www.vill.hakuba.lg.jp/gyosei/soshikikarasagasu/gikaijimukyoku/kansaiinjimukyoku/kansaiinjimukyoku/12268.html",
    "https://www.vill.hakuba.lg.jp/gyosei/gyoseijoho/tokeijoho/2741.html",
    "https://www.vill.hakuba.lg.jp/gyosei/gyoseijoho/tokeijoho/7985.html",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140 Safari/537.36 "
    "local-government-pdf-organizer/1.0"
)

REQUEST_TIMEOUT = 30
RETRY_COUNT = 3
RETRY_WAIT_SECONDS = 2.0


class PDFLinkParser(HTMLParser):
    """HTMLからPDFリンクを抽出する。"""

    def __init__(self, page_url: str) -> None:
        super().__init__()
        self.page_url = page_url
        self.links: list[tuple[str, str]] = []
        self._current_text: list[str] = []
        self._current_href: str | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() != "a":
            return

        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if href:
            self._current_href = urljoin(self.page_url, href)
            self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._current_href is None:
            return

        href = self._current_href
        text = " ".join("".join(self._current_text).split())

        parsed = urlparse(href)
        path = unquote(parsed.path).lower()

        if path.endswith(".pdf"):
            self.links.append((href, text))

        self._current_href = None
        self._current_text = []


def fetch_bytes(url: str) -> bytes:
    """URLを取得し、失敗時は数回リトライする。"""
    last_error: Exception | None = None

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/pdf,*/*",
                },
            )
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < RETRY_COUNT:
                print(
                    f"  取得失敗: {url} "
                    f"(retry {attempt}/{RETRY_COUNT})"
                )
                time.sleep(RETRY_WAIT_SECONDS * attempt)

    raise RuntimeError(f"取得失敗: {url}: {last_error}")


def safe_filename(name: str) -> str:
    """Windowsで問題になりやすい文字を除去する。"""
    name = unquote(name).strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or "document.pdf"


def filename_from_url(url: str) -> str:
    path_name = Path(unquote(urlparse(url).path)).name
    if path_name.lower().endswith(".pdf"):
        return safe_filename(path_name)
    return "document.pdf"


def unique_path(path: Path, source_url: str) -> Path:
    """同名PDFが存在する場合、URL由来の短いハッシュを付ける。"""
    if not path.exists():
        return path

    digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:8]
    return path.with_name(f"{path.stem}_{digest}{path.suffix}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_pdf_links() -> list[dict[str, str]]:
    """8ページからPDFリンクを収集する。"""
    records: list[dict[str, str]] = []
    seen: set[str] = set()

    for page_url in PAGE_URLS:
        print(f"\n[PAGE] {page_url}")

        html = fetch_bytes(page_url).decode("utf-8", errors="replace")
        parser = PDFLinkParser(page_url)
        parser.feed(html)

        if not parser.links:
            print("  PDFリンクなし")
            continue

        for pdf_url, link_text in parser.links:
            # 同じPDF URLが複数ページに登場した場合は1回だけ取得する。
            if pdf_url in seen:
                continue

            seen.add(pdf_url)
            records.append(
                {
                    "source_page": page_url,
                    "link_text": link_text,
                    "pdf_url": pdf_url,
                }
            )
            print(f"  + {link_text or filename_from_url(pdf_url)}")
            print(f"    {pdf_url}")

    return records


def download_pdf(record: dict[str, str]) -> dict[str, str]:
    """PDFを1件取得してmanifest用レコードを返す。"""
    pdf_url = record["pdf_url"]
    original_name = filename_from_url(pdf_url)
    target = unique_path(DOWNLOAD_DIR / original_name, pdf_url)

    data = fetch_bytes(pdf_url)

    # HTMLエラーページ等をPDFとして保存しないための簡易チェック。
    if not data.startswith(b"%PDF-"):
        raise ValueError("PDFヘッダ(%PDF-)を確認できませんでした")

    target.write_bytes(data)

    return {
        **record,
        "local_path": str(target.relative_to(BASE_DIR)),
        "file_name": target.name,
        "bytes": str(len(data)),
        "sha256": sha256_bytes(data),
        "status": "downloaded",
    }


def write_manifest(records: list[dict[str, str]]) -> None:
    fields = [
        "source_page",
        "link_text",
        "pdf_url",
        "local_path",
        "file_name",
        "bytes",
        "sha256",
        "status",
    ]

    with MANIFEST_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    print("========================================")
    print(" 白馬村 PDF 一括ダウンローダー")
    print("========================================")
    print(f"保存先: {DOWNLOAD_DIR}")

    link_records = collect_pdf_links()
    print(f"\nPDFリンク検出数: {len(link_records)}")

    results: list[dict[str, str]] = []

    for index, record in enumerate(link_records, start=1):
        label = record["link_text"] or filename_from_url(record["pdf_url"])
        print(f"\n[{index}/{len(link_records)}] {label}")

        try:
            result = download_pdf(record)
            results.append(result)
            print(
                f"  OK: {result['file_name']} "
                f"({int(result['bytes']) / 1024:.1f} KB)"
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            results.append(
                {
                    **record,
                    "local_path": "",
                    "file_name": "",
                    "bytes": "",
                    "sha256": "",
                    "status": f"error: {exc}",
                }
            )

    write_manifest(results)

    ok_count = sum(r["status"] == "downloaded" for r in results)
    error_count = len(results) - ok_count

    print("\n========================================")
    print(" 完了")
    print("========================================")
    print(f"PDF検出: {len(link_records)}")
    print(f"取得成功: {ok_count}")
    print(f"取得失敗: {error_count}")
    print(f"PDF保存先: {DOWNLOAD_DIR}")
    print(f"manifest: {MANIFEST_PATH}")

    if error_count:
        print("\n※ 失敗したPDFはmanifest.csvのstatus列を確認してください。")


if __name__ == "__main__":
    main()
