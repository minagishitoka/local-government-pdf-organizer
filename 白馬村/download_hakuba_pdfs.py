#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
白馬村公式サイトに掲載されているPDFを、指定ページから一括ダウンロードする。

出力:
  白馬村/
    pdf/                     ← 取得したPDFをすべてこの1フォルダに格納
    取得書類一覧.csv         ← 正常取得したPDF一覧
    エラーリスト.csv         ← 通信・HTTP・PDF判定などで取得できなかったもの
    要確認リスト.csv         ← PDFリンクなし、重複、その他の人手確認候補
    download_manifest.csv    ← 全件の詳細な処理記録

設計方針:
- 指定ページ内のPDFリンクを自動抽出する。
- PDF URLを固定で列挙しないため、年度追加・URL変更に比較的強い。
- 取得したPDFはすべて同じ pdf/ フォルダへ保存する。
- 同名ファイルはURL由来のハッシュを付けて衝突を回避する。
- 原本PDFの内容は加工しない。
- CSVはUTF-8 BOM付きで、Excelでそのまま開けるようにする。
"""

from __future__ import annotations

import csv
import hashlib
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "pdf"

SUCCESS_CSV = BASE_DIR / "取得書類一覧.csv"
ERROR_CSV = BASE_DIR / "エラーリスト.csv"
REVIEW_CSV = BASE_DIR / "要確認リスト.csv"
MANIFEST_CSV = BASE_DIR / "download_manifest.csv"

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
    "local-government-pdf-organizer/1.1"
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

        if urlparse(href).path.lower().endswith(".pdf"):
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
    candidate = path.with_name(f"{path.stem}_{digest}{path.suffix}")

    if not candidate.exists():
        return candidate

    # 同一URLを再実行した場合などの最終衝突回避。
    counter = 2
    while True:
        candidate = path.with_name(
            f"{path.stem}_{digest}_{counter}{path.suffix}"
        )
        if not candidate.exists():
            return candidate
        counter += 1


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_pdf_links() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """
    8ページからPDFリンクを収集する。

    戻り値:
      (PDF候補, 要確認)
    """
    records: list[dict[str, str]] = []
    reviews: list[dict[str, str]] = []
    seen: set[str] = set()

    for page_url in PAGE_URLS:
        print(f"\n[PAGE] {page_url}")

        try:
            html = fetch_bytes(page_url).decode("utf-8", errors="replace")
        except Exception as exc:
            reviews.append(
                {
                    "source_page": page_url,
                    "pdf_url": "",
                    "link_text": "",
                    "reason": "ページ取得失敗",
                    "detail": str(exc),
                }
            )
            print(f"  REVIEW: ページ取得失敗: {exc}")
            continue

        parser = PDFLinkParser(page_url)
        parser.feed(html)

        if not parser.links:
            reviews.append(
                {
                    "source_page": page_url,
                    "pdf_url": "",
                    "link_text": "",
                    "reason": "PDFリンクなし",
                    "detail": "ページ内に .pdf へのリンクを検出できませんでした",
                }
            )
            print("  REVIEW: PDFリンクなし")
            continue

        for pdf_url, link_text in parser.links:
            if pdf_url in seen:
                reviews.append(
                    {
                        "source_page": page_url,
                        "pdf_url": pdf_url,
                        "link_text": link_text,
                        "reason": "重複リンク",
                        "detail": "同一PDF URLは既に別ページから取得対象になっています",
                    }
                )
                print(f"  REVIEW: 重複 {pdf_url}")
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

    return records, reviews


def download_pdf(
    record: dict[str, str],
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    """
    PDFを1件取得する。

    戻り値:
      (成功レコード, エラーレコード)
    """
    pdf_url = record["pdf_url"]
    original_name = filename_from_url(pdf_url)
    target = unique_path(DOWNLOAD_DIR / original_name, pdf_url)

    try:
        data = fetch_bytes(pdf_url)
    except Exception as exc:
        return None, {
            **record,
            "reason": "ダウンロード失敗",
            "detail": str(exc),
        }

    # HTMLエラーページ等をPDFとして保存しない。
    if not data.startswith(b"%PDF-"):
        return None, {
            **record,
            "reason": "PDF判定失敗",
            "detail": "取得データの先頭に %PDF- がありません",
        }

    target.write_bytes(data)

    success = {
        **record,
        "local_path": str(target.relative_to(BASE_DIR)),
        "file_name": target.name,
        "bytes": str(len(data)),
        "sha256": sha256_bytes(data),
        "status": "downloaded",
    }
    return success, None


def write_csv(path: Path, records: list[dict[str, str]], fields: list[str]) -> None:
    """Excelで開きやすいUTF-8 BOM付きCSVを書き出す。"""
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def write_reports(
    successes: list[dict[str, str]],
    errors: list[dict[str, str]],
    reviews: list[dict[str, str]],
) -> None:
    write_csv(
        SUCCESS_CSV,
        successes,
        [
            "source_page",
            "link_text",
            "pdf_url",
            "local_path",
            "file_name",
            "bytes",
            "sha256",
            "status",
        ],
    )

    write_csv(
        ERROR_CSV,
        errors,
        [
            "source_page",
            "link_text",
            "pdf_url",
            "reason",
            "detail",
        ],
    )

    write_csv(
        REVIEW_CSV,
        reviews,
        [
            "source_page",
            "pdf_url",
            "link_text",
            "reason",
            "detail",
        ],
    )

    # 全件を1つにまとめた技術用manifestも維持する。
    manifest: list[dict[str, str]] = []

    for row in successes:
        manifest.append(
            {
                **row,
                "result_type": "success",
                "reason": "",
                "detail": "",
            }
        )

    for row in errors:
        manifest.append(
            {
                **row,
                "local_path": "",
                "file_name": "",
                "bytes": "",
                "sha256": "",
                "status": "error",
                "result_type": "error",
            }
        )

    for row in reviews:
        manifest.append(
            {
                **row,
                "local_path": "",
                "file_name": "",
                "bytes": "",
                "sha256": "",
                "status": "review",
                "result_type": "review",
            }
        )

    write_csv(
        MANIFEST_CSV,
        manifest,
        [
            "source_page",
            "link_text",
            "pdf_url",
            "local_path",
            "file_name",
            "bytes",
            "sha256",
            "status",
            "result_type",
            "reason",
            "detail",
        ],
    )


def main() -> None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    print("========================================")
    print(" 白馬村 PDF 一括ダウンローダー")
    print("========================================")
    print(f"PDF保存先: {DOWNLOAD_DIR}")

    link_records, reviews = collect_pdf_links()
    print(f"\nPDFリンク検出数: {len(link_records)}")

    successes: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for index, record in enumerate(link_records, start=1):
        label = record["link_text"] or filename_from_url(record["pdf_url"])
        print(f"\n[{index}/{len(link_records)}] {label}")

        success, error = download_pdf(record)

        if success:
            successes.append(success)
            print(
                f"  OK: {success['file_name']} "
                f"({int(success['bytes']) / 1024:.1f} KB)"
            )
        else:
            assert error is not None
            errors.append(error)
            print(f"  ERROR: {error['detail']}")

    write_reports(successes, errors, reviews)

    print("\n========================================")
    print(" 完了")
    print("========================================")
    print(f"PDFリンク検出: {len(link_records)}")
    print(f"取得成功: {len(successes)}")
    print(f"エラー: {len(errors)}")
    print(f"要確認: {len(reviews)}")
    print(f"\nPDFフォルダ: {DOWNLOAD_DIR}")
    print(f"取得書類一覧: {SUCCESS_CSV}")
    print(f"エラーリスト: {ERROR_CSV}")
    print(f"要確認リスト: {REVIEW_CSV}")
    print(f"詳細manifest: {MANIFEST_CSV}")

    if errors:
        print("\n[!] エラーがあります。エラーリスト.csvを確認してください。")
    if reviews:
        print("[!] 人手確認候補があります。要確認リスト.csvを確認してください。")


if __name__ == "__main__":
    main()
