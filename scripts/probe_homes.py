"""HOME'S取得の技術検証。依存パッケージ不要。評価・相場調査は行わない。"""

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class AcquisitionError(ValueError):
    pass


def validate_url(value):
    url = urlsplit(value)
    if (url.scheme != "https" or url.hostname != "www.homes.co.jp"
            or url.username or url.password or url.port not in (None, 443)
            or not re.fullmatch(r"/mansion/b-\d+/", url.path)
            or url.query or url.fragment):
        raise AcquisitionError("HOME'Sの物件詳細URL（https://www.homes.co.jp/mansion/b-数字/）を指定してください")
    return value


class OverviewParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}
        self.row = None
        self.cell = None
        self.cell_tag = None
        self.hidden = 0
        self.in_title = False
        self.title_done = False
        self.title = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if self.hidden:
            return
        if tag == "title" and not self.title_done:
            self.in_title = True
        if tag == "tr":
            self.row = []
        if tag in ("th", "td") and self.row is not None:
            self.cell, self.cell_tag = [], tag

    def handle_data(self, data):
        if self.hidden:
            return
        if self.in_title:
            self.title.append(data)
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)
            return
        if self.hidden:
            return
        if tag == "title":
            self.title_done = True
            self.in_title = False
        if tag == self.cell_tag and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell, self.cell_tag = None, None
        if tag == "tr" and self.row is not None:
            if len(self.row) == 2:
                self.fields.setdefault(*self.row)
            self.row = None


def amount(value, unit):
    match = re.search(r"([\d,]+(?:\.\d+)?)\s*(?:" + unit + ")", value or "")
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def extract(html, url):
    validate_url(url)
    parser = OverviewParser()
    parser.feed(html)
    fields = parser.fields
    # 相場・おすすめカードやサイトの返済試算から数値を拾わない。
    price = amount(fields.get("価格"), "万円")
    area = amount(fields.get("専有面積"), "㎡|m²")
    if price is None or area is None:
        raise AcquisitionError("物件概要の価格・専有面積を確認できません（取得制限・掲載終了・形式変更の可能性）")
    management = amount(fields.get("管理費等"), "円")
    reserve = amount(fields.get("修繕積立金"), "円")
    missing = [key for key in ("管理費等", "修繕積立金", "築年月", "交通", "現況")
               if not fields.get(key)]
    for key, value in (("管理費等", management), ("修繕積立金", reserve)):
        if value is None and key not in missing:
            missing.append(key)
    raw_occupancy = fields.get("現況")
    status_match = re.match(r"^(賃貸中|空家|空き家|居住中|未完成|完成済)", raw_occupancy or "")
    occupancy = status_match.group(1) if status_match else raw_occupancy
    conditions = fields.get("その他条件")
    flags = []
    if "賃貸中" in (occupancy or "") or "オーナーチェンジ" in (conditions or ""):
        flags.append("賃貸中・オーナーチェンジの記載あり。自宅としての入居可否は要確認")
    return {
        "source_url": url,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "page_title": "".join(parser.title).strip(),
        "price_yen": round(price * 10000),
        "area_sqm": area,
        "management_fee_yen": round(management) if management is not None else None,
        "repair_reserve_yen": round(reserve) if reserve is not None else None,
        "built": fields.get("築年月"),
        "access": fields.get("交通"),
        "occupancy": occupancy,
        "conditions": conditions,
        "missing_fields": missing,
        "flags": flags,
        "raw_overview": fields,
    }


def fetch(url):
    validate_url(url)
    result = subprocess.run([
        "curl", "--silent", "--show-error", "--max-time", "30",
        "--max-filesize", "5242880", "--proto", "=https",
        "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "--header", "Accept: text/html,application/xhtml+xml",
        "--header", "Accept-Language: ja,en-US;q=0.9,en;q=0.8",
        "--write-out", "\n%{http_code}", url,
    ], capture_output=True, text=True, timeout=35)
    if result.returncode:
        raise AcquisitionError(f"接続に失敗しました（curl終了コード {result.returncode}）")
    html, status = result.stdout.rsplit("\n", 1)
    if status != "200":
        raise AcquisitionError(f"HTTP {status}。取得制限・掲載終了・URL変更の可能性があります")
    return html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--html-file", type=Path, help="保存済みHTMLで抽出だけを検証")
    args = parser.parse_args()
    try:
        html = args.html_file.read_text() if args.html_file else fetch(args.url)
        print(json.dumps(extract(html, args.url), ensure_ascii=False, indent=2))
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"取得失敗: {error}\n")


if __name__ == "__main__":
    main()
