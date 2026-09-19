# -*- coding: utf-8 -*-
"""
============================================================
自治体議会調査 PDF整理・結合システム（統合版 v15・TXT/Word対応＋査読修正版）
============================================================

★★★ このプログラムは何をするもの？ ★★★

  大量のPDFファイル（例:「あ.pdf」「001.pdf」など、中身が分からない名前）
  を、AI(Gemini)に中身を読ませて正式なタイトルを判断させ、

    ・分かりやすい名前に付け替えたコピーを作り
    ・1000ページ・150MBを上限としてグループごとに1つのPDFへ結合し
    ・「どの原本が、結合後の何ページにあたるか」が分かる対応表を先頭に付け

  という作業を自動化するプログラムです。

  v15ではv14の構造を維持したまま、査読で発見された「同名衝突時の二重拡張子再発」と「TXT→Word資料欠落の未検知」を修正します。

  原本のPDFは絶対に書き換えません。すべて「コピー」に対して作業します。


★★★ 準備（最初に1回だけ行うこと） ★★★

  1. パソコンにPythonがインストールされていること
     （インストールされていない場合は、公式サイト python.org からダウンロード）

  2. 必要な部品(ライブラリ)をインストールする
     コマンドプロンプトを開いて、次の1行を貼り付けてEnterキーを押してください。

         pip install pypdf reportlab google-genai pymupdf python-docx

     ※ うまくいかない場合は、先頭に「py -m」を付けて試してください。

         py -m pip install pypdf reportlab google-genai pymupdf python-docx

  3. Gemini APIキーを取得する
     Google AI Studio (https://aistudio.google.com/) でAPIキーを取得し、
     このファイルの下の方にある

         gemini_api_key: str = "ここに取得したAPIキーを貼り付け"

     という行の "" の中に、取得したキーをそのまま貼り付けてください。


★★★ ファイルの置き方 ★★★

  このpdf_organizer.pyファイルと、整理したいPDFファイルを
  「同じフォルダ」に入れてください。サブフォルダを作る必要はありません。

  例：

      PDF整理実験フォルダ/
      ├─ pdf_organizer.py     ← このファイル
      ├─ 001.pdf
      ├─ あ.pdf
      ├─ download.pdf
      └─ 2025資料.pdf

  実行すると、このフォルダの中に自動的に次のフォルダ・ファイルが作られます。

      PDF整理実験フォルダ/
      ├─ pdf_organizer.py
      ├─ 001.pdf 等（原本。このプログラムは一切変更しません）
      ├─ 整理済み/     ← AIが付けた名前でリネームされたコピー
      ├─ 結合PDF/      ← 1000ページ・150MB以内でまとめた完成品
      ├─ レポート/     ← 処理結果のCSV（Excelで開けます）
      ├─ TXT/          ← 結合PDFを資料単位・ページ番号付きでテキスト化
      ├─ Word/         ← TXTだけを読み込んで生成したAI解析用Word
      └─ state.json    ← 途中経過の記録（再実行のためのメモ。消しても再実行可）


★★★ 実行方法 ★★★

  1. コマンドプロンプトを開く
  2. cd コマンドで、pdf_organizer.pyがあるフォルダに移動する
     例： cd C:\\Users\\あなたの名前\\Desktop\\PDF整理実験フォルダ
  3. 次のコマンドを実行する

         python pdf_organizer.py

  4. 画面に処理状況が表示されます。終わると「処理完了」と表示されます。


★★★ 終わったら何を見ればいい？ ★★★

  1. まず「レポート」フォルダの中の「要確認リスト.csv」を開いてください。
     ここに載っているファイルだけ、人間の目で確認してください。
     （「正常」と判定されたファイルは基本的に見なくて大丈夫です）

  2. 「結合PDF」フォルダの中に、完成したPDF（第1巻、第2巻…）があります。


★★★ 最初は少ない件数で試したい場合 ★★★

  下の方にある Config クラスの中の

      test_file_limit: Optional[int] = None

    # 結合PDF→TXT→Wordの後段処理
    create_txt: bool = True
    create_word: bool = True
    include_page_markers: bool = True

  を、例えば

      test_file_limit: Optional[int] = 5

  のように数字に変えると、最初に見つかった5件のPDFだけで試し実行できます。
  慣れてきたら None に戻して、全件処理してください。


★★★ この統合版(v7・Geminiヤジ完成版)で追加した点 ★★★

  11. Geminiは正式タイトルと、資料内容に応じた「反抗期中学生風のリアルタイムヤジ」を
      1回のAPI呼び出しで同時生成するようにした。
      ただし、ヤジは画面表示専用で、原本対応表・CSV・しおり・リネームには一切使わない。
  12. JSON形式で title と teasing を分離し、単純な改行分割に依存しない。
      ヤジが空でもタイトル処理は継続できる。
  13. ヤジは「人や自治体を攻撃する」のではなく、数字や行政用語の重さを
      中学生っぽくツッコむ程度に限定する。

★★★ v15で追加・修正した点 ★★★
  1. 同名ファイル衝突時も clean_title を使い、「.pdf.pdf」の再発を防止。
  2. TXT→Wordで資料数・資料番号・順序・タイトルを対応表（group_records）と照合し、欠落を黙って成功扱いしない。

  1. AIが「目次」だけをタイトルとして返した場合は、正式タイトルとして採用せず要確認にする。
  2. AIが元ファイル名そのものや拡張子付きファイル名を返した場合も、タイトル品質の要確認対象にする。
  3. フォールバックとして元ファイル名を使う場合、ファイル名の拡張子を二重付与しない。
  4. AIプロンプトにも「目次ではなく資料全体を識別する正式タイトルを選ぶ」ルールを明記する。
  5. TXT/Word工程はv12の構造を維持し、資料境界・PDF PAGE・ORIGINAL PDF PAGEを保持する。

★★★ この統合版(v4)で直した点 ★★★

  1. 対応表(TOC)で、タイトルが長い場合に一番大事な「ページ番号」が
     用紙の外にはみ出して消えてしまう問題を修正（幅を計算して自動的に
     「…」で省略するようにした）
  2. 対応表が2ページ以上になっても、毎ページに同じ見出しが表示されるように
     修正（見出しの高さもページ数の計算にきちんと組み込み済み）
  3. AIの回答が「長すぎる」などの理由で要確認になった場合、中途半端に
     切り詰めた文字列を使うのではなく、必ず元のファイル名を使うように変更
  4. Gemini APIのレート制限（429エラー）に備え、失敗するたびに待ち時間を
     延ばしながら再試行するように変更
  5. Windowsのパス長上限（約260文字）に備え、ファイル名が長くなりすぎる
     場合は自動的に短縮するように変更（対応表・しおりの表示はフルのまま）
  6. 事前検査を「ページ数を数えるだけ」から「全ページの中身が読めるか」
     まで確認するように強化（途中のページだけ壊れているPDFの早期発見）
  7. 結合PDFを保存した後、もう一度ファイルを開き直して
     ページ数・しおり数が正しいか最終チェックするようにした

  8. 完成PDFを再読込し、総ページ数・しおり件数だけでなく、各しおりの
     タイトルと遷移先が対応表の開始ページと一致するかまで自動検証
  9. 以前の実行で残った古い結合PDFが、新しい処理失敗時に残存しないよう
     保存前に旧出力を整理
 10. 結合後の最新状態をstate.jsonへ保存し、再実行時の記録を更新

============================================================
"""

import concurrent.futures
import glob
import io
import json
import os
import random
import re
import shutil
import sys
import threading
import time
import unicodedata
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    Document = None
    Pt = None
    WD_ALIGN_PARAGRAPH = None

from google import genai
from google.genai import types
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# Windowsでの文字化け・エンコードエラー防止
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print_lock = threading.Lock()

# 対応表(目次)に日本語タイトルを描画するためのフォントを登録しておく。
# （プログラム起動時に1回だけ実行すればよい）
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

# このファイル自身が置かれているフォルダを取得する。
# → 「どこから実行しても、このファイルと同じ場所にあるPDFを読む」ため。
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 出力先として使うフォルダ名（このフォルダの中身は「入力PDF」としては絶対に読み込まない）
RESERVED_OUTPUT_DIRNAMES = {"整理済み", "結合PDF", "レポート", "TXT", "Word"}


# =====================================================
# 0. 設定（初心者の方はここだけ編集すればOK）
# =====================================================

@dataclass
class Config:
    # ▼▼▼ ここにご自身のGemini APIキーを直接貼り付けてください ▼▼▼
    #
    #   例: gemini_api_key: str = "AIzaSyABCDEFG1234567890abcdefg"
    #
    #   ダブルクォート " " の中に、Google AI Studioで取得したキーを
    #   そのまま貼り付けてください。前後に空白を入れないでください。
    #
    gemini_api_key: str = ""
    # ▲▲▲ ここまで ▲▲▲

    # フォルダ（すべて「このpyファイルと同じ場所」を基準にした場所になります）
    input_dir: str = field(default_factory=lambda: SCRIPT_DIR)
    renamed_dir: str = field(default_factory=lambda: os.path.join(SCRIPT_DIR, "整理済み"))
    merged_dir: str = field(default_factory=lambda: os.path.join(SCRIPT_DIR, "結合PDF"))
    report_dir: str = field(default_factory=lambda: os.path.join(SCRIPT_DIR, "レポート"))
    state_path: str = field(default_factory=lambda: os.path.join(SCRIPT_DIR, "state.json"))
    txt_dir: str = field(default_factory=lambda: os.path.join(SCRIPT_DIR, "TXT"))
    word_dir: str = field(default_factory=lambda: os.path.join(SCRIPT_DIR, "Word"))

    # 処理パラメータ
    page_limit_per_volume: int = 1000      # 1巻あたりの上限ページ数
    max_mb_per_volume: float = 150.0       # 1巻あたりの上限ファイル容量（MB）
    max_ai_workers: int = 5                # AI呼び出しの同時実行数
    max_title_length: int = 80             # タイトルとして許容する最大文字数
    ai_model: str = "gemini-3.6-flash"     # 2026-09現在のStableモデル。2.5系は新規利用者に制限があるため使用しない。

    # AI呼び出しが失敗した時の再試行設定
    # 大量件数を一度に処理すると、Gemini APIの「1分あたりのリクエスト数上限」に
    # 引っかかることがある(429エラー)。その場合、待つ時間を毎回少しずつ延ばす
    # (指数バックオフ)ことで、API側の制限が解除されるのを待ってから再試行する。
    ai_max_retries: int = 5
    ai_backoff_base_seconds: float = 2.0   # 1回目の待機時間の目安（秒）
    ai_backoff_max_seconds: float = 30.0   # 待機時間の上限（これ以上は伸ばさない）

    volume_prefix: str = "議会資料"         # 結合PDFの名前の接頭辞

    # 事前検査を「ページ数を数えるだけ」でなく、全ページの中身が読めるかまで
    # 確認するかどうか。件数が非常に多い場合は少し時間がかかるが、
    # 「表紙は正常なのに途中のページが壊れている」PDFを早期に見つけられる。
    deep_inspect: bool = True

    # お試し実行用: 数字を入れると、その件数だけ処理して終わる（Noneなら全件）
    test_file_limit: Optional[int] = None

    # 結合PDF→TXT→Wordの後段処理
    create_txt: bool = True
    create_word: bool = True
    include_page_markers: bool = True


CONFIG = Config()


# =====================================================
# 1. 発見 & 自然順ソート（Python担当）
# =====================================================

def natural_keys(text: str):
    """数字の大きさを考慮した自然順ソート (例: 1, 2, ..., 10, 24)"""
    return [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", text)]


def discover_pdfs(input_dir: str, config: "Config") -> list:
    """
    入力フォルダの直下にあるPDFだけを見つける。
    サブフォルダ（整理済み・結合PDF・レポート）の中は探さない。
    → glob.glob は直下しか見ないので、自動的にサブフォルダの中身は含まれない。

    さらに、過去の実行で作られた結合済みPDF（例: 議会資料_第1巻.pdf）が
    誤ってこのフォルダ直下に置かれていた場合に備えて、
    出力用のファイル名パターンに一致するものは念のため除外する。
    """
    raw = glob.glob(os.path.join(input_dir, "*.pdf"))

    def is_output_like(path: str) -> bool:
        name = os.path.basename(path)
        return name.startswith(config.volume_prefix + "_第")

    filtered = [p for p in raw if not is_output_like(p)]
    sorted_paths = sorted(filtered, key=lambda p: natural_keys(os.path.basename(p)))

    if config.test_file_limit is not None:
        sorted_paths = sorted_paths[: config.test_file_limit]
        print(f"🧪 お試し実行だな。とりあえず最初の{len(sorted_paths)}件だけやってみるわ。")

    return sorted_paths


# =====================================================
# 2. 機械的な検査（Python担当）
#    ページ数・ファイルサイズ・開けるか・暗号化されていないか
# =====================================================

@dataclass
class PdfRecord:
    original_path: str
    original_filename: str
    file_size_bytes: int = 0
    num_pages: int = 0
    inspect_status: str = "pending"   # ok / corrupt
    inspect_error: str = ""

    ai_municipality_raw: str = ""
    municipality: str = ""
    ai_date_raw: str = ""
    document_date: str = ""
    ai_title_raw: str = ""
    ai_teasing: str = ""             # 画面表示専用。対応表・しおり・ファイル名には使わない
    ai_status: str = "pending"        # ok / failed
    ai_error: str = ""

    final_title: str = ""
    validation_status: str = "pending"  # ok / needs_review
    validation_reason: str = ""

    renamed_filename: str = ""

    volume_index: Optional[int] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None

    # 結合(マージ)段階の結果。ここが failed だと、この資料が入るはずだった
    # 結合PDF全体を「未完成」として扱う。
    merge_status: str = "pending"     # ok / failed / not_attempted
    merge_error: str = ""

    # 後段処理（巻単位のTXT/Word生成結果を資料にも反映）
    text_status: str = "pending"      # ok / needs_review / failed / not_attempted
    text_error: str = ""
    word_status: str = "pending"      # ok / failed / not_attempted
    word_error: str = ""

    def overall_status(self) -> str:
        """人間に見せる最終ステータス（正常 / 要確認 / エラー）を判定する"""
        if self.inspect_status != "ok":
            return "エラー"
        if self.merge_status == "failed":
            return "エラー"
        if self.text_status == "failed" or self.word_status == "failed":
            return "エラー"
        if self.ai_status == "failed":
            return "要確認"
        if self.validation_status == "needs_review":
            return "要確認"
        return "正常"


def inspect_pdf(path: str, config: "Config") -> PdfRecord:
    """
    そのPDFが「開けるか」「何ページか」「暗号化されていないか」を
    Pythonが機械的に検査する。ここではAIは一切使わない。

    config.deep_inspect が True の場合は、さらに踏み込んで
    「全ページの中身が実際に読めるか」も確認する。
    （表紙の1ページ目は無事でも、真ん中のページだけデータが壊れている、
      というPDFを、AI呼び出しや結合の段階まで進む前に見つけるため）
    """
    rec = PdfRecord(
        original_path=path,
        original_filename=os.path.basename(path),
    )
    try:
        rec.file_size_bytes = os.path.getsize(path)
    except OSError as e:
        rec.inspect_status = "corrupt"
        rec.inspect_error = f"ファイルサイズ取得失敗: {e}"
        return rec

    try:
        reader = PdfReader(path)

        # 暗号化されている場合、まず空パスワードでの復号を試みる
        # （「閲覧は自由だが編集だけ制限」というタイプのPDFはこれで開けることが多い）
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                pass

        rec.num_pages = len(reader.pages)

        if rec.num_pages == 0:
            rec.inspect_status = "corrupt"
            rec.inspect_error = "ページ数が0（壊れているか空のPDFの可能性）"
            return rec

        if config.deep_inspect:
            for page_index, page in enumerate(reader.pages):
                try:
                    page.extract_text()
                except Exception as e:
                    raise RuntimeError(f"{page_index + 1}ページ目の読み込みに失敗: {e}")

        rec.inspect_status = "ok"

    except Exception as e:
        rec.inspect_status = "corrupt"
        rec.inspect_error = f"読み込み失敗: {e}"

    return rec


# =====================================================
# 3. AIによるタイトル判断（AI担当・冒頭3ページ）
# =====================================================

def extract_title_pages_bytes(path: str, max_pages: int = 3) -> bytes:
    """
    元PDFの冒頭最大3ページを切り出して、単独のPDFバイト列にする。

    議会資料では1ページ目が「目次」になっており、2～3ページ目に
    正式な会議名・開催日・議事日程が載るケースがあるため、1ページ限定をやめる。
    後半ページまで渡さず、タイトル判定に必要な冒頭だけを見る。
    """
    reader = PdfReader(path)
    writer = PdfWriter()
    page_count = min(max_pages, len(reader.pages))
    for i in range(page_count):
        writer.add_page(reader.pages[i])
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


AI_PROMPT = r"""
あなたは自治体議会資料を整理するPDFアシスタントです。
このPDFには資料冒頭の最大3ページが入っています。
必ず次のJSONオブジェクトだけを返してください。Markdownのコードブロックは不要です。

{
  "municipality": "資料に実際に記載された自治体名",
  "date": "会議の開催日。YYYY-MM-DD形式。会議開催日が確認できない場合は NO_DATE_FOUND",
  "title": "資料に実際に書かれている主な正式タイトル",
  "teasing": "資料内容に合わせた短い一言"
}

municipality のルール:
- PDFに実際に記載された市区町村等の自治体名を抽出する。
- ファイル名から推測しない。
- 自治体名が確認できない場合は "NO_MUNICIPALITY_FOUND" とする。

date のルール:
- 会議の開催年月日・開催日を抽出する。
- 単なる発行日・作成日・更新日・印刷日は除外する。
- 令和表記は西暦の YYYY-MM-DD に変換する。
- 開催日が確認できない場合は "NO_DATE_FOUND" とする。

title のルール:
- 日本語の主な正式タイトルだけを抽出する。
- 表紙に複数の文字列がある場合、資料全体を代表する主タイトルを選ぶ。
- 会議名・委員会名・総会名・審議会名・回次・年度など、
  資料を識別するための正式情報を残す。
- 開催日は独立した date フィールドで管理するため、
  title には原則として開催日を重複して入れない。
- ただし、正式名称そのものに日付表現が組み込まれている場合は、その表現を勝手に削らない。
- 単なる発行日・作成日・更新日・印刷日などは title に入れない。
- 発行者、著者、作成部署、URL、ファイル名、説明文、感想は title に入れない。
- 会議名に「令和〇年度」「第〇回」などの年度・回次が正式名称として含まれる場合は、
  それらもタイトルから除外しない。
- 冒頭ページが「目次」でも、それだけを title にしない。目次だけで判断できない場合は、
  2～3ページ目も確認する。そこに議会名・会議名・回次・開催日・「議事日程」・
  「会議録」などが確認できるなら、それらを組み合わせて資料全体を識別できる正式タイトルを選ぶ。
  冒頭3ページを確認しても正式タイトルが判断できない場合は "NO_TITLE_FOUND" とする。
- ファイル名をそのまま title にコピーしない。ファイル名しか手掛かりがない場合は
  "NO_TITLE_FOUND" とする。
- 明確なタイトルがない場合は "NO_TITLE_FOUND" とする。

teasing のルール:
- 画面に表示するだけの遊び心ある一言。
- 「反抗期の中学生男子が議会資料を見せられた」ような、少しすれて冷めたツッコミ口調。
- 数字、ページ数、難しい言葉、行政っぽさなど、その資料の1ページ目の内容に触れてよい。
- 最後は完全な悪口ではなく、資料整理をちゃんと手伝っている感じを残す。
- 1文、短め。日本語。
- 資料そのものを改変・要約したり、政治的な評価や事実認定をしたりしない。
- 人や自治体を侮辱・攻撃する内容にしない。
- title と teasing を混ぜない。
"""


def parse_ai_json(raw_text: str) -> tuple[str, str, str, str]:
    """GeminiのJSON応答を安全に分離する。title失敗とヤジ失敗を切り分ける。"""
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("AI応答が空です")

    # 念のためコードブロックで返ってきた場合も外側だけ取り除く。
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # JSONだけ抜き出せるケースへの穏当なフォールバック。
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("AI応答をJSONとして解釈できません")
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            raise ValueError(f"AI応答のJSON解析失敗: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("AI応答がJSONオブジェクトではありません")

    municipality = str(data.get("municipality", "")).strip()
    date = str(data.get("date", "")).strip()
    title = str(data.get("title", "")).strip()
    teasing = str(data.get("teasing", "")).strip()
    return municipality, date, title, teasing


def is_retryable_ai_error(exc: Exception) -> bool:
    """
    AI APIエラーのうち「待てば直る可能性があるもの」だけを再試行対象にする。

    404/NOT_FOUND、400/BAD_REQUEST、401/UNAUTHENTICATED、403/PERMISSION_DENIED
    のような設定・モデル・認証系エラーは、何回待っても直らないことが多いため
    リトライしない。429や500/502/503/504などの一時的なエラーは再試行する。
    """
    text = str(exc).upper()
    permanent_markers = (
        "404", "NOT_FOUND",
        "400", "BAD_REQUEST",
        "401", "UNAUTHENTICATED",
        "403", "PERMISSION_DENIED",
    )
    if any(marker in text for marker in permanent_markers):
        return False

    transient_markers = (
        "429", "RESOURCE_EXHAUSTED",
        "500", "INTERNAL",
        "502", "BAD_GATEWAY",
        "503", "UNAVAILABLE",
        "504", "GATEWAY_TIMEOUT",
        "TIMEOUT", "TIMED OUT",
        "TEMPORARY", "CONNECTION",
    )
    return any(marker in text for marker in transient_markers)


def call_ai_title_and_teasing(
    client: "genai.Client", title_pages_bytes: bytes, config: Config
) -> tuple[str, str, str, str]:
    """Geminiから正式タイトルと画面表示用ヤジを1回のAPI呼び出しで取得する。"""
    last_error = None
    for attempt in range(1, config.ai_max_retries + 1):
        try:
            response = client.models.generate_content(
                model=config.ai_model,
                contents=[
                    types.Part.from_bytes(data=title_pages_bytes, mime_type="application/pdf"),
                    AI_PROMPT,
                ],
            )
            return parse_ai_json(response.text)
        except Exception as e:
            last_error = e

            # 404等の恒久的なエラーは、何回待っても直らないので即終了。
            if not is_retryable_ai_error(e):
                with print_lock:
                    print(f"    🛑 [再試行しない] Gemini APIの設定・モデル等に関するエラーです。待っても直らない可能性が高いため、このPDFのAI処理を終了します。（{e}）")
                break

            if attempt < config.ai_max_retries:
                delay = min(
                    config.ai_backoff_base_seconds * (2 ** (attempt - 1)),
                    config.ai_backoff_max_seconds,
                )
                delay += random.uniform(0, 1.0)
                with print_lock:
                    print(f"    ⏳ チッ、ちょっと詰まった。{delay:.1f}秒待ってからもう一回やるぞ。（{attempt}回目失敗: {e}）")
                time.sleep(delay)

    raise RuntimeError(f"AI呼び出し失敗: {last_error}")


# =====================================================
# 4. AI出力の検証（Python担当）
#    「AIだから正しいはず」を前提にしない
# =====================================================

FORBIDDEN_CHARS_PATTERN = re.compile(r'[\\/:*?"<>|\r\n\t\x00-\x1f]')

# タイトルとして不自然な返答のパターン（説明文・URL・空判定など）
SUSPICIOUS_PATTERNS = [
    re.compile(r"^(sure|here is|the title|title:|タイトル[:：]|申し訳|すみません)", re.IGNORECASE),
    re.compile(r"^NO_TITLE_FOUND$"),
    re.compile(r"https?://", re.IGNORECASE),
]

# 1ページ目に「目次」と書かれている議事録で、AIがその語だけを
# 資料タイトルとして返す事故を防ぐ。実際に「目次」という名前の資料もあり得るため、
# 自動修正はせず「要確認」にする。
GENERIC_TITLE_PATTERNS = {
    "目次",
    "contents",
    "table of contents",
}
MUNICIPALITY_FALLBACK_MARKERS = {"no_municipality_found", "no municipality found"}
DATE_FALLBACK_MARKERS = {"no_date_found", "no date found"}

def validate_municipality(raw_municipality: str) -> tuple:
    if not raw_municipality or not raw_municipality.strip():
        return "", "needs_review", "自治体名が空"
    value = unicodedata.normalize("NFKC", raw_municipality.strip())
    if value.casefold() in MUNICIPALITY_FALLBACK_MARKERS:
        return "", "needs_review", "自治体名を確認できなかった"
    if FORBIDDEN_CHARS_PATTERN.search(value):
        return "", "needs_review", "自治体名にファイル名に使えない文字が含まれていた"
    if len(value) < 2:
        return "", "needs_review", "自治体名が短すぎる"
    if len(value) > 40:
        return "", "needs_review", f"自治体名が長すぎる（{len(value)}文字）"
    return value.strip(" 　."), "ok", ""

def validate_document_date(raw_date: str) -> tuple:
    if not raw_date or raw_date.strip().casefold() in DATE_FALLBACK_MARKERS:
        return "", "needs_review", "開催日を確認できなかった"
    value = unicodedata.normalize("NFKC", raw_date.strip())
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return "", "needs_review", f"日付形式が不正: {value}"
    return value, "ok", ""


def validate_ai_title(raw_title: str, fallback_name: str, config: Config) -> tuple:
    """
    AIの応答を検証し、(使用する文字列, ステータス, 理由) を返す。
    ステータスは "ok" か "needs_review"。

    【重要な方針】
    少しでも怪しい点があれば、中途半端に加工したAIの文字列は一切使わず、
    "fallback_name"（＝元のファイル名）を丸ごと採用する。
    「AIの回答を検証し、怪しいものはファイル名に使わず要確認にする」という
    最初のご要望に忠実に、"ok"以外はすべて fallback_name を返す設計にした。
    （以前のバージョンでは、長すぎるタイトルを"切り詰めて"使ってしまっており、
      要確認フラグは立つのに不完全な文字列がファイル名や対応表・しおりに
      そのまま残ってしまう問題があったため、ここを直した）

    ここでできるのは「ファイル名として安全か」「不自然な形をしていないか」
    という機械的なチェックだけ。タイトルの中身が"意味的に正しいか"は
    Pythonには判断できないため、それは要確認として人間の目に委ねる。
    """
    if not raw_title or not raw_title.strip():
        return fallback_name, "needs_review", "AI応答が空"

    title = unicodedata.normalize("NFKC", raw_title.strip())

    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(title):
            return fallback_name, "needs_review", f"不自然な応答パターン: {title[:40]}"

    # 「目次」などの汎用語だけを正式タイトルとして採用しない。
    if title.casefold() in GENERIC_TITLE_PATTERNS:
        return fallback_name, "needs_review", f"汎用語だけのタイトル: {title}"

    # AIがファイル名をそのままタイトルとして返した場合も、意味的なタイトル取得に
    # 成功したとは扱わない。元ファイル名をフォールバックとして残し、要確認にする。
    fallback_stem = os.path.splitext(os.path.basename(fallback_name))[0]
    title_stem = os.path.splitext(os.path.basename(title))[0]
    if title.casefold() == fallback_name.casefold() or title_stem.casefold() == fallback_stem.casefold():
        return fallback_name, "needs_review", "AIが元ファイル名をそのまま返した"

    if len(title) > config.max_title_length:
        return fallback_name, "needs_review", f"タイトルが長すぎる（{len(title)}文字）"

    if len(title) < 2:
        return fallback_name, "needs_review", "タイトルが短すぎる"

    if FORBIDDEN_CHARS_PATTERN.search(title):
        return fallback_name, "needs_review", "ファイル名に使えない文字が含まれていた"

    safe_title = title.strip(" 　.")

    if not safe_title:
        return fallback_name, "needs_review", "無害化後に空文字になった"

    return safe_title, "ok", ""


# =====================================================
# 5. 1ファイル分の処理をまとめる関数
#    （検査→AI→検証の3段階。段階ごとに例外を分けて扱う）
# =====================================================

def process_single_pdf(path: str, client: "genai.Client", config: Config) -> PdfRecord:
    rec = inspect_pdf(path, config)

    if rec.inspect_status != "ok":
        with print_lock:
            print(f"  ❌ [開けない] {rec.original_filename}: おい、このファイル中身壊れてないか？ 俺のせいじゃないぞ。元データ確認した方がいいかも。（{rec.inspect_error}）")
        return rec

    try:
        title_pages_bytes = extract_title_pages_bytes(path, max_pages=3)
        municipality_raw, date_raw, raw_title, teasing = call_ai_title_and_teasing(client, title_pages_bytes, config)
        rec.ai_municipality_raw = municipality_raw
        rec.ai_date_raw = date_raw
        rec.ai_title_raw = raw_title
        rec.ai_teasing = teasing
        rec.ai_status = "ok"
    except Exception as e:
        rec.ai_status = "failed"
        rec.ai_error = str(e)
        with print_lock:
            print(f"  ⚠️ [タイトル取得失敗] {rec.original_filename}: チッ、表紙が分かりづらすぎるんだよ……。無理に推測して間違えたら嫌だから、元のファイル名のまま要確認に入れておく。（エラー: {e}）")
        # AI失敗時はファイル名をそのままタイトル代わりに使い、要確認に回す
        rec.final_title = rec.original_filename
        rec.ai_teasing = ""
        rec.validation_status = "needs_review"
        rec.validation_reason = "AI呼び出し失敗"
        return rec

    municipality, municipality_status, municipality_reason = validate_municipality(rec.ai_municipality_raw)
    document_date, date_status, date_reason = validate_document_date(rec.ai_date_raw)

    final_title, title_status, title_reason = validate_ai_title(
        rec.ai_title_raw, rec.original_filename, config
    )
    rec.municipality = municipality
    rec.document_date = document_date
    rec.final_title = final_title
    rec.validation_status = (
        "ok" if municipality_status == "ok" and date_status == "ok" and title_status == "ok"
        else "needs_review"
    )
    rec.validation_reason = "; ".join(
        reason for reason in (municipality_reason, date_reason, title_reason) if reason
    )

    with print_lock:
        mark = "✅" if rec.validation_status == "ok" else "⚠️"
        print(f"  {mark} [{rec.original_filename}] → {rec.municipality or '自治体不明'}_{rec.document_date or '日付不明'}_{final_title}")
        if rec.ai_teasing:
            print(f"      👦「{rec.ai_teasing}」")
        if rec.validation_status != "ok":
            print(f"      ⚠️ 要確認: {rec.validation_reason}")

    return rec


# =====================================================
# 6. 途中経過の保存・再開（Python担当）
# =====================================================

def load_state(state_path: str) -> dict:
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state_path: str, state: dict):
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def record_key(path: str) -> str:
    """再開判定用のキー。パス＋更新日時＋サイズで、内容が変わっていないか判別する。"""
    try:
        stat = os.stat(path)
        return f"{os.path.abspath(path)}::{stat.st_mtime_ns}::{stat.st_size}"
    except OSError:
        return os.path.abspath(path)


# =====================================================
# 7. ファイル名の安全化・コピー（Python担当）
# =====================================================

# Windowsの標準的なパス長上限は約260文字。
# 深い階層のフォルダに置かれても安全なように、少し余裕を持たせた上限を設ける。
SAFE_PATH_LIMIT = 240


def sanitize_filename_part(value: str, fallback: str) -> str:
    value = unicodedata.normalize("NFKC", (value or "").strip())
    value = FORBIDDEN_CHARS_PATTERN.sub(" ", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value or fallback

def build_unique_filename(title: str, ext: str, used_names: set) -> str:
    # フォールバックタイトルが元ファイル名（例: xxx.pdf）の場合でも、
    # 「xxx.pdf.pdf」にはしない。
    clean_title = title.strip()
    if ext and clean_title.casefold().endswith(ext.casefold()):
        clean_title = clean_title[:-len(ext)].rstrip()
    if not clean_title:
        clean_title = "資料"

    candidate = f"{clean_title}{ext}"
    counter = 2
    while candidate in used_names:
        candidate = f"{clean_title}_{counter}{ext}"
        counter += 1
    used_names.add(candidate)
    return candidate


def copy_and_rename(records: list, renamed_dir: str) -> None:
    """
    原本はそのまま。整理済みフォルダにコピーしてリネームする。

    対応表やしおりに載せる rec.final_title はフルの文字列のまま残すが、
    実際にディスクに保存する「ファイル名」だけは、深いフォルダに置かれた
    場合にWindowsのパス長上限を超えないよう、必要なら短く切り詰める。
    """
    os.makedirs(renamed_dir, exist_ok=True)
    used_names = set()
    abs_dir = os.path.abspath(renamed_dir)

    for rec in records:
        if rec.inspect_status != "ok":
            continue
        ext = os.path.splitext(rec.original_path)[1] or ".pdf"

        # 「フォルダの絶対パスの長さ」を差し引いて、ファイル名に使える残り文字数を決める
        max_name_len = SAFE_PATH_LIMIT - len(abs_dir) - 1 - len(ext)
        max_name_len = max(max_name_len, 10)  # 極端に短くなりすぎないための最低保証

        municipality_part = sanitize_filename_part(rec.municipality, "自治体不明")
        date_part = sanitize_filename_part(rec.document_date, "日付不明")
        title_for_filename = sanitize_filename_part(rec.final_title, "資料")
        prefix = f"{municipality_part}_{date_part}_"
        available_title_len = max(max_name_len - len(prefix), 5)
        if len(title_for_filename) > available_title_len:
            title_for_filename = title_for_filename[: max(available_title_len - 1, 4)] + "…"
            if rec.validation_status == "ok":
                rec.validation_status = "needs_review"
            reason = "ファイルパスが長くなりすぎるため、ファイル名のみ短縮"
            rec.validation_reason = (rec.validation_reason + "; " + reason).strip("; ")

        new_name = build_unique_filename(prefix + title_for_filename, ext, used_names)
        rec.renamed_filename = new_name
        dest = os.path.join(renamed_dir, new_name)
        shutil.copy2(rec.original_path, dest)  # 原本は変更しない（コピーのみ）


# =====================================================
# 8. ページ数＋容量単位のグループ分け（Python担当・貪欲法）
# =====================================================

def group_records_by_page_limit(
    records: list, page_limit: int, max_mb: float = 150.0
) -> list:
    """
    ページ数またはファイルサイズ(MB)の累積が上限を超える手前で
    グループを区切る。

    1ファイル単独でページ数または容量上限を超える場合は、
    自動分割せず単独グループとして扱い、要確認にする。
    原本PDFは分割しない。
    """
    normal_records = [r for r in records if r.inspect_status == "ok"]

    groups = []
    current_group = []
    current_page_total = 0
    current_bytes_total = 0
    max_bytes = max_mb * 1024 * 1024
    oversized_alone = []

    for rec in normal_records:
        rec_bytes = rec.file_size_bytes or 0

        # 1ファイル単独で上限超過
        if rec.num_pages > page_limit or rec_bytes > max_bytes:
            if current_group:
                groups.append(current_group)
                current_group = []
                current_page_total = 0
                current_bytes_total = 0

            groups.append([rec])
            oversized_alone.append(rec)
            rec.validation_status = "needs_review"

            mb_size = rec_bytes / (1024 * 1024)
            reasons = []
            if rec.num_pages > page_limit:
                reasons.append(f"{rec.num_pages}p")
            if rec_bytes > max_bytes:
                reasons.append(f"{mb_size:.1f}MB")

            reason = (
                f"単独で巻上限超過（{', '.join(reasons)} / "
                f"上限 {page_limit}p・{max_mb:.1f}MB）"
            )
            rec.validation_reason = (
                (rec.validation_reason + "; " + reason).strip("; ")
            )
            continue

        # 今回のPDFを追加するとページ数または容量のどちらかを超えるか
        exceeds_pages = current_page_total + rec.num_pages > page_limit
        exceeds_bytes = current_bytes_total + rec_bytes > max_bytes

        if current_group and (exceeds_pages or exceeds_bytes):
            groups.append(current_group)
            current_group = []
            current_page_total = 0
            current_bytes_total = 0

        current_group.append(rec)
        current_page_total += rec.num_pages
        current_bytes_total += rec_bytes

    if current_group:
        groups.append(current_group)

    if oversized_alone:
        with print_lock:
            print(
                f"\n⚠️ 単独で巻上限（{page_limit}p / {max_mb:.1f}MB）を超える"
                f"ファイルが{len(oversized_alone)}件あるんだけど！？ "
                f"原本は分割せず単独巻にしてある。要確認リストを見といて。"
            )

    return groups


# =====================================================
# 9. 対応表の作成（2パス方式でページ番号のズレを防ぐ）
# =====================================================
#
# 【レイアウトの数値を全部ここにまとめる理由】
#   「対応表が何ページになるかを見積もる計算」と「実際に描画する処理」が、
#   別々の場所でバラバラの数値を使っていると、後から片方だけ変更したときに
#   見積もりと実描画がズレるバグが起きやすい。
#   そのため、レイアウトに関する数値はすべてこの1か所にまとめ、
#   見積もり用の _count_toc_pages() と、実際に描画する build_toc_and_assign_pages()
#   の両方が、必ずこの同じ数値を使うようにしている。

TOC_FONT_NAME = "HeiseiKakuGo-W5"
TOC_FONT_SIZE = 8
TOC_LEFT_MARGIN = 50
TOC_RIGHT_MARGIN = 50
TOC_USABLE_WIDTH = letter[0] - TOC_LEFT_MARGIN - TOC_RIGHT_MARGIN  # 1行に使える横幅(pt)

TOC_TITLE_Y = 750       # 「原本対応表（第X巻）」の見出し位置（1ページ目だけ）
TOC_HEADER_Y = 715      # 列見出し（No. 元ファイル名...）の位置（毎ページ）
TOC_SEPARATOR_Y = 700   # 区切り線の位置（毎ページ）
TOC_ITEM_TOP_Y = 680    # 資料一覧の1行目の位置（毎ページ、ここが基準点）
TOC_Y_STEP = 16         # 1行ごとに下がる幅
TOC_BOTTOM_MARGIN = 50  # これより下に行ったら改ページ


def _count_toc_pages(n_items: int, y_step: int, top_y: float, bottom_margin: float) -> int:
    """
    実際の描画ルールと全く同じ計算式で、対応表が何ページになるか数える。
    「たぶん25件で1ページ」のような当てずっぽうの見積もりをやめて、
    実際の改ページ判定と完全に同じ式を使うことで、見積もりと実描画が
    食い違わないようにしている。

    ここでの top_y は「資料一覧が始まる位置」であって、見出しや区切り線の
    描画そのものはページ数の計算に影響しない（見出しは毎ページ同じ場所に
    固定で描くだけなので、件数によって位置がズレることがないため）。
    """
    y = top_y
    pages = 1
    for _ in range(n_items):
        y -= y_step
        if y < bottom_margin:
            pages += 1
            y = top_y
    return pages


def truncate_text_to_width(text: str, max_width: float, font_name: str, font_size: float) -> str:
    """
    文字列がmax_width(pt)に収まるように、必要なら末尾を「…」に置き換えて短くする。
    ページ番号などの重要な情報を印字する余白を必ず確保するために使う。
    """
    if pdfmetrics.stringWidth(text, font_name, font_size) <= max_width:
        return text

    ellipsis = "…"
    ellipsis_width = pdfmetrics.stringWidth(ellipsis, font_name, font_size)
    if ellipsis_width > max_width:
        return ""  # 幅が極端に狭い場合の保険

    lo, hi = 0, len(text)
    best = ellipsis
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = text[:mid] + ellipsis
        if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
            best = candidate
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def build_toc_and_assign_pages(group_records: list, volume_index: int):
    """
    対応表PDFを作りつつ、各資料のstart_page/end_pageを確定させる。

    【手順】
      1パス目: 実際の改ページルールで、対応表が何ページになるか正確に数える(_count_toc_pages)
      2パス目: 確定したページ数をもとに、本文の開始ページを計算しながら描画する

    【今回追加した安全策】
      ・1行の合計幅が用紙からはみ出さないよう、まず「-> Page 12-34 (Total 5p)」
        という最重要部分の幅を先に確保し、残りの幅に収まるようファイル名と
        タイトルを必要なら「…」で省略する。これにより、タイトルがどれだけ
        長くても、ページ範囲の表示が用紙の外にはみ出して消えることはない。
      ・列見出しと区切り線を、対応表の全ページ（2ページ目以降も含めて）に
        同じ位置へ描く。資料一覧が始まる高さ(TOC_ITEM_TOP_Y)はどのページでも
        変わらないため、見積もり計算(_count_toc_pages)とズレることもない。
    """
    toc_page_count = _count_toc_pages(
        len(group_records), TOC_Y_STEP, TOC_ITEM_TOP_Y, TOC_BOTTOM_MARGIN
    )

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    def draw_page_header(is_first_page: bool):
        if is_first_page:
            can.setFont("Helvetica-Bold", 14)
            can.drawString(TOC_LEFT_MARGIN, TOC_TITLE_Y, f"原本対応表（第{volume_index}巻）")

        can.setFont("Helvetica", 8)
        can.drawString(TOC_LEFT_MARGIN, TOC_HEADER_Y, "No.  [元ファイル名] 自治体 | 開催日 | 資料タイトル")
        can.drawString(TOC_LEFT_MARGIN, TOC_SEPARATOR_Y, "-" * 105)
        can.setFont(TOC_FONT_NAME, TOC_FONT_SIZE)

    draw_page_header(is_first_page=True)
    y = TOC_ITEM_TOP_Y
    current_page = toc_page_count + 1

    for i, rec in enumerate(group_records, 1):
        rec.volume_index = volume_index
        rec.start_page = current_page
        rec.end_page = current_page + max(rec.num_pages - 1, 0)

        # 最重要情報（ページ範囲）の幅を先に測っておく
        page_range_text = f" -> Page {rec.start_page}-{rec.end_page} (Total {rec.num_pages}p)"
        page_range_width = pdfmetrics.stringWidth(page_range_text, TOC_FONT_NAME, TOC_FONT_SIZE)

        # 残りの幅の中に、ファイル名とタイトルを収める（収まらなければ省略記号で短縮）
        available_width = TOC_USABLE_WIDTH - page_range_width
        left_text_full = (
            f"{i}. [{rec.original_filename}] "
            f"{rec.municipality or '自治体不明'} | {rec.document_date or '日付不明'} | {rec.final_title}"
        )
        left_text = truncate_text_to_width(
            left_text_full, available_width, TOC_FONT_NAME, TOC_FONT_SIZE
        )

        can.drawString(TOC_LEFT_MARGIN, y, left_text + page_range_text)
        y -= TOC_Y_STEP

        if y < TOC_BOTTOM_MARGIN:
            can.showPage()
            draw_page_header(is_first_page=False)
            y = TOC_ITEM_TOP_Y

        current_page += rec.num_pages

    can.save()
    packet.seek(0)
    toc_reader = PdfReader(packet)

    # 安全確認: 見積もったページ数と、実際に描画されたページ数が本当に一致しているか。
    # 一致していなければ、どこかの計算式がズレているということなので、
    # 黙って進まずにここで止める。
    actual_toc_pages = len(toc_reader.pages)
    if actual_toc_pages != toc_page_count:
        raise RuntimeError(
            f"対応表のページ数計算が一致しません"
            f"（見積もり{toc_page_count}ページ、実際{actual_toc_pages}ページ）。"
            f"処理を中止します。"
        )

    return toc_reader, toc_page_count


def _collect_outline_items(outline):
    """pypdfのoutlineから、実際のしおり項目と遷移先を平坦化して取得する。"""
    items = []
    for item in outline or []:
        if isinstance(item, list):
            items.extend(_collect_outline_items(item))
            continue
        try:
            # pypdfのDestination / outline item
            items.append(item)
        except Exception:
            pass
    return items


def verify_completed_pdf(output_path: str, group_records: list, expected_total: int, toc_page_count: int):
    """
    保存後の完成PDFを再読込し、ページ数だけでなく、しおりの件数と
    各しおりの遷移先が対応表の開始ページと一致するかを検証する。
    ここは「完成品そのもの」を検品する最終工程。
    """
    reader = PdfReader(output_path)
    actual_total = len(reader.pages)
    if actual_total != expected_total:
        raise RuntimeError(f"完成PDFの総ページ数が不一致（予定{expected_total} / 実際{actual_total}）")

    outline = reader.outline
    outline_items = _collect_outline_items(outline)
    if len(outline_items) != len(group_records):
        raise RuntimeError(
            f"完成PDFのしおり件数が不一致（予定{len(group_records)} / 実際{len(outline_items)}）"
        )

    for rec, item in zip(group_records, outline_items):
        try:
            title = str(getattr(item, "title", ""))
            if title != rec.final_title:
                raise RuntimeError(
                    f"しおりタイトル不一致: {rec.original_filename} "
                    f"（予定「{rec.final_title}」/ 実際「{title}」）"
                )
            dest_page = reader.get_destination_page_number(item)
            expected_dest = rec.start_page - 1
            if dest_page != expected_dest:
                raise RuntimeError(
                    f"しおり遷移先不一致: {rec.original_filename} "
                    f"（予定0始まり{expected_dest} / 実際{dest_page}）"
                )
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"しおり検証中にエラー: {rec.original_filename}: {exc}"
            )

    # 対応表の最初の本文ページも、TOCページ数から機械的に再確認する。
    if group_records and group_records[0].start_page != toc_page_count + 1:
        raise RuntimeError(
            f"本文開始ページがTOCページ数と不一致（予定{toc_page_count + 1} / 実際記録{group_records[0].start_page}）"
        )

    return actual_total, len(outline_items)


# =====================================================
# 10. 結合 & しおり付け（Python担当）
#     ★1件でも失敗したら、その巻は完成させない（安全側に倒す）
# =====================================================

def merge_group(group_records: list, volume_index: int, merged_dir: str, config: Config):
    """
    1つのグループ(巻)を結合する。

    安全のための方針:
      ・結合の直前に、すべての原本PDFをもう一度読み直して再検査する
        （最初の検査から時間が経って、ファイルが変わっている可能性があるため）
      ・1件でも「開けない」「ページ数が食い違う」などの問題があれば、
        その巻は丸ごと「未完成」とし、中途半端なPDFファイルは作らない
      ・結合が終わったあと、予定した合計ページ数と、実際にできあがった
        PDFの合計ページ数を照合し、合っていなければ完成させない

    戻り値: (output_path または None, 成功したかどうか)
    """
    os.makedirs(merged_dir, exist_ok=True)

    # --- 事前チェック: 結合直前にもう一度、全ファイルを読めるか確認する ---
    opened_readers = []
    for rec in group_records:
        try:
            reader = PdfReader(rec.original_path)
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    pass
            actual_pages = len(reader.pages)
            if actual_pages != rec.num_pages:
                raise RuntimeError(
                    f"ページ数が食い違っています"
                    f"（検査時{rec.num_pages}ページ→結合時{actual_pages}ページ）"
                )
            opened_readers.append((rec, reader))
        except Exception as e:
            # 1件でも失敗したら、この巻に含まれる全員を「結合失敗」にして中止する
            error_msg = f"{rec.original_filename} の再検査でエラー: {e}"
            with print_lock:
                print(f"  ❌ [第{volume_index}巻・結合中止] {error_msg}")
            for r in group_records:
                r.merge_status = "failed"
                r.merge_error = error_msg
            return None, False

    # --- 対応表(目次)を作成し、各資料の開始・終了ページを確定させる ---
    try:
        toc_reader, toc_page_count = build_toc_and_assign_pages(group_records, volume_index)
    except Exception as e:
        with print_lock:
            print(f"  ❌ [第{volume_index}巻・結合中止] 対応表の作成でエラー: {e}")
        for r in group_records:
            r.merge_status = "failed"
            r.merge_error = f"対応表作成エラー: {e}"
        return None, False

    # --- 結合本体 ---
    writer = PdfWriter()
    for page in toc_reader.pages:
        writer.add_page(page)

    try:
        for rec, reader in opened_readers:
            start_page_idx = len(writer.pages)
            for page in reader.pages:
                writer.add_page(page)
            end_page_idx = len(writer.pages) - 1

            # 対応表に書いた開始ページと、実際に結合された開始ページが
            # 一致しているかをその場で照合する
            expected_start_idx = rec.start_page - 1  # 1始まり→0始まりに変換
            if start_page_idx != expected_start_idx:
                raise RuntimeError(
                    f"{rec.original_filename} の開始ページが対応表と食い違っています"
                    f"（対応表:{expected_start_idx}、実際:{start_page_idx}）"
                )

            writer.add_outline_item(title=rec.final_title, page_number=start_page_idx)
    except Exception as e:
        with print_lock:
            print(f"  ❌ [第{volume_index}巻・結合中止] 結合中にエラー: {e}")
        for r in group_records:
            r.merge_status = "failed"
            r.merge_error = f"結合中エラー: {e}"
        return None, False

    # --- 最終照合: 予定していた合計ページ数と、実際にできたページ数を比較 ---
    expected_total = toc_page_count + sum(rec.num_pages for rec in group_records)
    actual_total = len(writer.pages)
    if expected_total != actual_total:
        error_msg = f"合計ページ数が一致しません（予定{expected_total}、実際{actual_total}）"
        with print_lock:
            print(f"  ❌ [第{volume_index}巻・結合中止] {error_msg}")
        for r in group_records:
            r.merge_status = "failed"
            r.merge_error = error_msg
        return None, False

    # --- ここまで問題なければ、初めてファイルとして保存する ---
    output_name = f"{config.volume_prefix}_第{volume_index}巻.pdf"
    output_path = os.path.join(merged_dir, output_name)
    tmp_path = output_path + ".tmp"

    # 以前の実行で残った古い完成品を、今回の処理失敗時に誤って
    # 「完成品」として残さないよう、保存前に一時ファイルを整理する。
    try:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if os.path.exists(output_path):
            os.remove(output_path)
    except OSError as exc:
        error_msg = f"旧出力ファイルを整理できません: {exc}"
        for r in group_records:
            r.merge_status = "failed"
            r.merge_error = error_msg
        return None, False

    with open(tmp_path, "wb") as f:
        writer.write(f)
    os.replace(tmp_path, output_path)  # 書き込み完了後に本来の名前へ変更(安全のため)

    # --- 完成品Post-Verification ---
    # メモリ上のwriterではなく、実際に保存されたPDFを再読込して検品する。
    try:
        verify_pages, verify_outline_count = verify_completed_pdf(
            output_path, group_records, expected_total, toc_page_count
        )
    except Exception as e:
        error_msg = f"完成PDFの最終検証に失敗しました: {e}"
        try:
            os.remove(output_path)
        except OSError:
            pass
        for r in group_records:
            r.merge_status = "failed"
            r.merge_error = error_msg
        with print_lock:
            print(f"  ❌ [第{volume_index}巻・検証失敗] 保存されたPDFを検品したらページ数の辻褄が合わない。このまま完成扱いにはできないから弾いておく。（詳細: {error_msg}）")
        return None, False

    for rec in group_records:
        rec.merge_status = "ok"

    return output_path, True


# =====================================================
# 11. 結合PDF → TXT → Word（Python担当）
# =====================================================


def _require_text_word_libraries(config: Config):
    """後段処理に必要なライブラリを、実行時に分かりやすく確認する。"""
    missing = []
    if config.create_txt and fitz is None:
        missing.append("PyMuPDF (pymupdf)")
    if config.create_word and Document is None:
        missing.append("python-docx")
    if missing:
        raise RuntimeError(
            "後段処理に必要なライブラリがありません: " + ", ".join(missing)
            + "\nコマンドプロンプトで次を実行してください:\n"
            + "py -m pip install pymupdf python-docx"
        )


def _safe_text(text: str) -> str:
    """TXT/Word向けに改行を正規化する。"""
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def extract_merged_pdf_to_txt(output_path: str, group_records: list, txt_dir: str, config: Config):
    """
    結合済みPDFを、対応表で確定した資料単位に分解してTXT化する。

    重要:
      ・PDF→TXTを直接「1本のベタ文章」にせず、資料境界を明示する。
      ・各ページに結合PDFのPDF PAGEを付ける。
      ・原本PDFページ番号も付ける。
      ・本文はPDFから機械抽出した文字をそのまま保存し、内容の要約やAI改変はしない。
    """
    os.makedirs(txt_dir, exist_ok=True)
    volume_index = group_records[0].volume_index if group_records else None
    if not volume_index:
        raise RuntimeError("TXT化対象の巻番号が確定していません")

    txt_name = os.path.splitext(os.path.basename(output_path))[0] + ".txt"
    txt_path = os.path.join(txt_dir, txt_name)

    doc = fitz.open(output_path)
    try:
        total_pages = len(doc)
        expected_total = max((r.end_page or 0 for r in group_records), default=0)
        if total_pages < expected_total:
            raise RuntimeError(
                f"TXT化時のPDFページ数不足（実際{total_pages}p / 対応表上{expected_total}p）"
            )

        empty_pages = []
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"自治体議会資料 テキスト化データ（第{volume_index}巻）\n")
            f.write(f"元PDF: {os.path.basename(output_path)}\n")
            f.write(f"総ページ数: {total_pages}\n")
            f.write("\n")

            for rec_no, rec in enumerate(group_records, 1):
                start = rec.start_page
                end = rec.end_page
                if not start or not end or start < 1 or end > total_pages or start > end:
                    raise RuntimeError(
                        f"資料ページ範囲が不正: {rec.original_filename} ({start}-{end})"
                    )

                f.write("=" * 80 + "\n")
                f.write(f"【資料 {rec_no:03d}】\n")
                f.write(f"自治体名: {rec.municipality or '自治体不明'}\n")
                f.write(f"開催日: {rec.document_date or '日付不明'}\n")
                f.write(f"資料タイトル: {rec.final_title}\n")
                f.write(f"元ファイル名: {rec.original_filename}\n")
                f.write(f"整理後ファイル名: {rec.renamed_filename}\n")
                f.write(f"結合PDFページ: {start}-{end}\n")
                f.write(f"原本ページ数: {rec.num_pages}\n")
                f.write("=" * 80 + "\n\n")

                for merged_page in range(start, end + 1):
                    page = doc[merged_page - 1]
                    text = _safe_text(page.get_text("text"))
                    original_page = merged_page - start + 1
                    if not text:
                        empty_pages.append(merged_page)
                        text = "[TEXT EXTRACTION EMPTY: このPDFページから文字を抽出できませんでした。画像PDF等の可能性があります。]"

                    if config.include_page_markers:
                        f.write(f"[PDF PAGE {merged_page}] [ORIGINAL PDF PAGE {original_page}]\n")
                    f.write(text + "\n\n")

        status = "needs_review" if empty_pages else "ok"
        error = "" if not empty_pages else (
            "文字抽出結果が空のページあり: " + ", ".join(map(str, empty_pages[:20]))
            + (" …" if len(empty_pages) > 20 else "")
        )
        return txt_path, status, error
    finally:
        doc.close()


def txt_to_word(txt_path: str, word_dir: str, expected_records: Optional[list] = None):
    """
    ④で生成したTXTだけを読み、⑤としてWordを生成する。
    PDFをここでは直接読まない。TXT→Wordの工程を明確に分離する。

    expected_records が渡された場合は、TXTから抽出した資料台帳と
    「資料数・資料番号・順序・タイトル」を照合し、資料の静かな欠落や
    並べ替えを検知してからWordを生成する。
    """
    os.makedirs(word_dir, exist_ok=True)
    word_name = os.path.splitext(os.path.basename(txt_path))[0] + ".docx"
    word_path = os.path.join(word_dir, word_name)

    document = Document()
    styles = document.styles
    styles["Normal"].font.name = "Yu Gothic"
    styles["Normal"].font.size = Pt(10)

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    # 目次を先頭に置く。資料境界の後ろ数行から資料タイトルを取得する。
    # 自治体名・開催日を追加しても、タイトル抽出位置が壊れないよう固定行番号に依存しない。
    toc_items = []
    for i, line in enumerate(lines):
        if line.startswith("【資料 "):
            search_end = min(i + 8, len(lines))
            for metadata_line in lines[i + 1:search_end]:
                if metadata_line.startswith("資料タイトル:"):
                    title = metadata_line.split(":", 1)[1].strip()
                    toc_items.append((line.strip("【】"), title))
                    break

    # 期待される資料台帳がある場合は、数だけでなく番号・順序・タイトルまで照合する。
    if expected_records is not None:
        expected_items = [
            (f"資料 {idx:03d}", str(rec.final_title).strip())
            for idx, rec in enumerate(expected_records, 1)
        ]
        actual_items = [(label.strip(), title.strip()) for label, title in toc_items]
        if len(actual_items) != len(expected_items):
            raise RuntimeError(
                f"TXTの資料数が不一致（期待{len(expected_items)} / 実際{len(actual_items)}）"
            )
        if actual_items != expected_items:
            mismatches = []
            for idx, (expected, actual) in enumerate(zip(expected_items, actual_items), 1):
                if expected != actual:
                    mismatches.append(f"{idx}件目: 期待={expected} / 実際={actual}")
            detail = "; ".join(mismatches[:10])
            if len(mismatches) > 10:
                detail += " …"
            raise RuntimeError(f"TXTの資料番号・順序・タイトルが対応表と不一致: {detail}")

    title = next((line for line in lines if line.startswith("自治体議会資料 テキスト化データ")), "自治体議会資料")
    p = document.add_paragraph()
    p.style = document.styles["Title"]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(title)

    document.add_heading("資料目次", level=1)
    for label, item_title in toc_items:
        p = document.add_paragraph(style="List Number")
        p.add_run(f"{label}: {item_title}")

    document.add_page_break()

    # TXTの構造を尊重してWord化する。資料見出しはHeading 1、ページマーカーはHeading 2。
    for line in lines:
        if line.startswith("自治体議会資料 テキスト化データ"):
            continue
        if line.startswith("【資料 "):
            document.add_heading(line.strip("【】"), level=1)
            continue
        if line.startswith("[PDF PAGE "):
            document.add_heading(line, level=2)
            continue
        if line == "=" * 80:
            continue
        if not line.strip():
            continue

        # メタデータ行は本文より小さくせず、普通の段落として残す。
        document.add_paragraph(line)

    document.save(word_path)
    return word_path


def generate_txt_and_word_for_volumes(volume_results: list, config: Config):
    """
    結合成功した巻だけを対象に、④TXT→⑤Wordを順番に実行する。
    TXT生成に成功してからWord生成へ進むため、工程が混ざらない。
    """
    _require_text_word_libraries(config)
    generated = []

    for volume_index, group_records, output_path in volume_results:
        print(f"\n📄 第{volume_index}巻: PDF→TXTを開始。")
        txt_path = None
        txt_status = "not_attempted"
        txt_error = ""
        word_path = None
        word_status = "not_attempted"
        word_error = ""

        try:
            if config.create_txt:
                txt_path, txt_status, txt_error = extract_merged_pdf_to_txt(
                    output_path, group_records, config.txt_dir, config
                )
                print(f"   📝 TXT: {txt_path}")
                if txt_status == "needs_review":
                    print(f"   ⚠️ TXT要確認: {txt_error}")
            else:
                txt_status = "not_attempted"

            if config.create_word:
                if not txt_path:
                    raise RuntimeError("Word生成にはTXTが必要ですが、TXTが生成されていません")
                print(f"   🗂️ 第{volume_index}巻: TXT→Wordを開始。")
                word_path = txt_to_word(txt_path, config.word_dir, expected_records=group_records)
                word_status = "ok"
                print(f"   📘 Word: {word_path}")
        except Exception as e:
            if word_status != "ok" and txt_path and config.create_word:
                word_status = "failed"
                word_error = str(e)
            elif config.create_txt and txt_path is None:
                txt_status = "failed"
                txt_error = str(e)
            else:
                word_status = "failed"
                word_error = str(e)

            print(f"   ❌ 第{volume_index}巻の後段処理に失敗: {e}")

        for rec in group_records:
            rec.text_status = txt_status
            rec.text_error = txt_error
            rec.word_status = word_status
            rec.word_error = word_error

        generated.append({
            "volume_index": volume_index,
            "pdf_path": output_path,
            "txt_path": txt_path,
            "txt_status": txt_status,
            "txt_error": txt_error,
            "word_path": word_path,
            "word_status": word_status,
            "word_error": word_error,
        })

    return generated


# =====================================================
# 12. レポート出力（Python担当）
# =====================================================

def write_reports(records: list, report_dir: str):
    os.makedirs(report_dir, exist_ok=True)
    import csv

    all_path = os.path.join(report_dir, "対応表_全体.csv")
    inventory_path = os.path.join(report_dir, "資料一覧_全体.csv")
    review_path = os.path.join(report_dir, "要確認リスト.csv")
    error_path = os.path.join(report_dir, "エラーリスト.csv")
    summary_path = os.path.join(report_dir, "処理集計サマリー.csv")

    fieldnames = [
        "総合ステータス", "自治体名", "開催日", "元ファイル名", "整理後ファイル名", "資料タイトル",
        "原本ページ数", "巻番号", "開始ページ", "終了ページ",
        "検査結果", "AI結果", "検証結果", "結合結果", "TXT結果", "Word結果", "備考",
    ]

    def row_of(rec: PdfRecord) -> dict:
        return {
            "総合ステータス": rec.overall_status(),
            "自治体名": rec.municipality,
            "開催日": rec.document_date,
            "元ファイル名": rec.original_filename,
            "整理後ファイル名": rec.renamed_filename,
            "資料タイトル": rec.final_title,
            "原本ページ数": rec.num_pages,
            "巻番号": rec.volume_index,
            "開始ページ": rec.start_page,
            "終了ページ": rec.end_page,
            "検査結果": rec.inspect_status,
            "AI結果": rec.ai_status,
            "検証結果": rec.validation_status,
            "結合結果": rec.merge_status,
            "TXT結果": rec.text_status,
            "Word結果": rec.word_status,
            "備考": rec.inspect_error or rec.ai_error or rec.merge_error or rec.text_error or rec.word_error or rec.validation_reason,
        }

    with open(all_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(row_of(rec))

    # 「結局、資料は何部あったのか？」を確認するための全資料一覧。
    # 1行=1原本PDF。正常・要確認・エラーを含め、発見した全資料を記録する。
    inventory_fields = [
        "通し番号", "総合ステータス", "自治体名", "開催日", "元ファイル名", "資料タイトル",
        "原本ページ数", "巻番号", "開始ページ", "終了ページ",
        "整理後ファイル名", "検査結果", "AI結果", "検証結果", "結合結果", "TXT結果", "Word結果", "備考",
    ]
    with open(inventory_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=inventory_fields)
        writer.writeheader()
        for idx, rec in enumerate(records, 1):
            row = row_of(rec)
            writer.writerow({
                "通し番号": idx,
                **{k: row[k] for k in inventory_fields if k != "通し番号"},
            })

    review_records = [r for r in records if r.overall_status() == "要確認"]
    error_records = [r for r in records if r.overall_status() == "エラー"]

    with open(review_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in review_records:
            writer.writerow(row_of(rec))

    with open(error_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in error_records:
            writer.writerow(row_of(rec))

    # 「資料は何部・何ページ・何巻になったか」を一目で確認する集計。
    normal_count = sum(1 for r in records if r.overall_status() == "正常")
    review_count = len(review_records)
    error_count = len(error_records)
    total_source_pages = sum((r.num_pages or 0) for r in records)
    summary_fields = ["項目", "値"]
    summary_rows = [
        ("原本資料数", len(records)),
        ("原本総ページ数", total_source_pages),
        ("正常", normal_count),
        ("要確認", review_count),
        ("エラー", error_count),
        ("完成した巻", len([r for r in records if r.merge_status == "ok" and r.volume_index]) if records else 0),
        ("資料一覧", os.path.basename(inventory_path)),
        ("対応表全体", os.path.basename(all_path)),
        ("要確認リスト", os.path.basename(review_path)),
        ("エラーリスト", os.path.basename(error_path)),
    ]
    # 巻数はレコードのvolume_indexの最大値で数える。
    volume_numbers = {r.volume_index for r in records if r.volume_index}
    summary_rows[5] = ("完成した巻", len(volume_numbers))
    with open(summary_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(summary_fields)
        writer.writerows(summary_rows)

    return all_path, inventory_path, review_path, error_path, summary_path, len(review_records), len(error_records)


# =====================================================
# 13. 全体の流れ（main）
# =====================================================

def main():
    config = CONFIG

    if config.create_txt or config.create_word:
        _require_text_word_libraries(config)

    api_key = config.gemini_api_key.strip()
    if (
        not api_key
        or "ここに取得した" in api_key
        or api_key == "YOUR_API_KEY"
    ):
        print("❌ おい、APIキー入ってないんだけど……。これがないと俺も何もできないから、Configの gemini_api_key にキー貼ってからもう一度動かしてく。")
        sys.exit(1)
    client = genai.Client(api_key=api_key)

    pdf_paths = discover_pdfs(config.input_dir, config)
    if not pdf_paths:
        print("❌ ここ、PDFが1個もないぞ。準備できてると思って待ってたのに……。整理したいPDFを同じフォルダに入れてからもう一回呼んで。")
        sys.exit(1)

    print(f"📂 PDF {len(pdf_paths)}件発見。よし、このくらいならサクサク片付けてやるから見てろよ。\n")

    # --- 再開用の状態を読み込む ---
    state = load_state(config.state_path)

    records = []
    to_process = []
    for path in pdf_paths:
        key = record_key(path)
        if key in state and state[key].get("municipality") and state[key].get("document_date"):
            # 新しい自治体名・開催日メタデータまで保存済みの記録だけ再利用する。
            saved = dict(state[key])
            # v11/v12以前のstate.jsonには後段処理等の追加項目がないため、
            # 欠落項目はdataclassのデフォルト値で補って後方互換にする。
            for field_name, default_value in {
                "ai_municipality_raw": "",
                "municipality": "",
                "ai_date_raw": "",
                "document_date": "",
                "text_status": "pending",
                "text_error": "",
                "word_status": "pending",
                "word_error": "",
            }.items():
                saved.setdefault(field_name, default_value)
            rec = PdfRecord(**saved)
            records.append(rec)
            with print_lock:
                print(f"  ⏭️ [スキップ] {rec.original_filename} （自治体名・開催日まで処理済みなので再利用）")
        else:
            # 旧state.jsonに自治体名・開催日がない場合は、今回の仕様変更に合わせて再処理する。
            to_process.append((path, key))

    # --- 未処理分だけAI呼び出しを含めて処理 ---
    if to_process:
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_ai_workers) as executor:
            futures = {
                executor.submit(process_single_pdf, path, client, config): key
                for path, key in to_process
            }
            for future in concurrent.futures.as_completed(futures):
                key = futures[future]
                rec = future.result()
                records.append(rec)
                state[key] = asdict(rec)
                save_state(config.state_path, state)  # 1件ごとに保存 = 途中で落ちても安心

    # 元の発見順（自然順）に並べ直す
    records.sort(key=lambda r: natural_keys(r.original_filename))

    # --- コピー＆リネーム ---
    copy_and_rename(records, config.renamed_dir)

    # --- ページ数および容量単位でグループ分け ---
    groups = group_records_by_page_limit(
        records,
        config.page_limit_per_volume,
        config.max_mb_per_volume,
    )

    # --- グループごとに結合（1件でも失敗したらその巻は完成させない） ---
    print()
    succeeded_volumes = 0
    failed_volumes = 0
    volume_results = []
    for i, group in enumerate(groups, 1):
        output_path, success = merge_group(group, i, config.merged_dir, config)
        total_pages = sum(r.num_pages for r in group)
        if success:
            succeeded_volumes += 1
            volume_results.append((i, group, output_path))
            print(f"📚 第{i}巻できたぞ！ {len(group)}件・計{total_pages}ページ分。目次もしおりもピッタリ合ってる。完璧だな。")
        else:
            failed_volumes += 1
            print(f"🛑 [第{i}巻・結合中断] {len(group)}件の結合中にエラーが出た。中途半端なファイルを出力すると事故るから処理を止めている。要確認リストを見て対応してく。（エラー: 巻の結合に失敗）")

    # --- ④ PDF→TXT、⑤ TXT→Word ---
    if volume_results and (config.create_txt or config.create_word):
        generate_txt_and_word_for_volumes(volume_results, config)

    # --- 古い巻ファイルの整理 ---
    # 今回の処理が全巻成功した場合のみ、今回の巻数を超える古い完成品を削除する。
    # 途中で失敗した実行では、前回の完成品を残しておき、誤って有効な資料を消さない。
    if failed_volumes == 0:
        import re
        volume_pattern = re.compile(
            rf"^{re.escape(config.volume_prefix)}_第(\d+)巻\.pdf$"
        )
        current_volume_count = len(groups)
        stale_files = []
        try:
            for existing_path in Path(config.merged_dir).glob("*.pdf"):
                match = volume_pattern.match(existing_path.name)
                if match and int(match.group(1)) > current_volume_count:
                    stale_files.append(existing_path)

            for stale_path in stale_files:
                stale_path.unlink()
                print(f"  🧹 前回の古い巻（{stale_path.name}）が残ってたから片付けておいたぞ。")
        except OSError as e:
            print(f"  ⚠️ 古い結合PDFの整理に失敗しました: {e}")
    else:
        print("  ⚠️ 待て。まだ未完成の巻がある。この状態で古いPDFまで消すとデータ事故に繋がるから、今回は消さずに残すぞ。全巻完成してから片付ける。")

    # --- レポート出力 ---
    # 5種類のCSVを「該当0件でも必ず」生成する。
    (all_path, inventory_path, review_path, error_path, summary_path,
     review_count, error_count_from_report) = write_reports(records, config.report_dir)

    # レポート生成そのものを検証。成功したのに帳票が無い状態を見逃さない。
    report_paths = [all_path, inventory_path, review_path, error_path, summary_path]
    missing_reports = [p for p in report_paths if not os.path.isfile(p)]
    if missing_reports:
        print("\n🛑 [レポート生成失敗] 必要なCSVが作られていないぞ。")
        for p in missing_reports:
            print(f"   未生成: {p}")
        print("   この状態では処理完了扱いにしない。")
        raise RuntimeError("必要なレポートCSVの生成に失敗しました")

    print("\n📊 レポート生成完了。")
    print(f"   📋 資料一覧       : {inventory_path}")
    print(f"   🔗 対応表         : {all_path}")
    print(f"   ⚠️ 要確認リスト   : {review_path}")
    print(f"   🛑 エラーリスト   : {error_path}")
    print(f"   📈 処理集計       : {summary_path}")

    # 結合結果・ページ範囲まで確定した最新状態を保存する。
    # 次回実行時に、途中までの処理だけでなく最終状態も参照できるようにする。
    try:
        final_state = {record_key(r.original_path): asdict(r) for r in records}
        save_state(config.state_path, final_state)
    except Exception as e:
        print(f"  ⚠️ state保存に失敗した。次回の再開に影響するから、ここは要確認な。（エラー: {e}）")

    # --- 最終サマリー ---
    ok_count = sum(1 for r in records if r.overall_status() == "正常")
    error_count = sum(1 for r in records if r.overall_status() == "エラー")

    print("\n" + "=" * 50)
    print(f"よし。全{len(records)}件、終わり。")
    print()
    print(f"  正常   : {ok_count}件")
    print(f"  要確認 : {review_count}件")
    print(f"  エラー : {error_count}件")
    print()
    print(f"完成した巻 : {succeeded_volumes}巻")
    print(f"未完成の巻 : {failed_volumes}巻")
    print()
    print(f"資料一覧全体  : {inventory_path}")
    print(f"対応表全体    : {all_path}")
    print(f"要確認リスト  : {review_path}")
    print(f"エラーリスト  : {error_path}")
    print(f"処理集計      : {summary_path}")
    print()
    print("目次、ページ番号、しおり、最後の検品、TXT化、Word化まで全部済ませた。")
    print("……ほら、ちゃんと仕事できるだろ？")
    print()
    print("まあ……アンタが使うなら、")
    print("これくらいきっちりやっとかないとな。")
    print()
    print("……別に褒められたいわけじゃないけど。")
    print("=" * 50)


if __name__ == "__main__":
    main()
