"""構造化した評価結果JSONから、単体で開けるHTMLレポートを作成する。"""

import argparse
import json
import math
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]


def text(value):
    return escape(str(value), quote=True)


def rows(items):
    return "".join(
        '<div class="row"><dt>' + text(item["label"]) + '</dt><dd>'
        + text(item["value"]) + ('<small>' + text(item["note"]) + '</small>' if item.get("note") else '')
        + '</dd></div>' for item in items
    )


def insights(items):
    return "".join('<div class="insight"><h3>' + text(item["title"]) + '</h3><p>'
                   + text(item["text"]) + '</p></div>' for item in items)


def render(data):
    names = ("title", "subtitle", "report_label", "limitations", "price", "access", "location",
             "grade", "verdict", "summary", "scenario_note", "source_name", "evaluated_at", "costs_note", "scores_note")
    values = {key: text(data[key]) for key in names}
    values["page_title"] = text(data["title"])
    values["metrics"] = "".join(
        '<article class="metric' + (' negative' if item.get("tone") == "negative" else '')
        + '"><div class="metric-label">' + text(item["label"]) + '</div><div class="metric-value">'
        + text(item["value"]) + '<small>' + text(item["unit"]) + '</small></div><div class="metric-note">'
        + text(item["note"]) + '</div></article>' for item in data["metrics"]
    )
    values["strengths"] = insights(data["strengths"])
    values["risks"] = insights(data["risks"])
    for key in ("costs", "facts", "conditions"):
        values[key] = rows(data[key])
    scores = []
    for item in data["scores"]:
        score, maximum = item["value"], item["max"]
        if (not isinstance(score, (int, float)) or not isinstance(maximum, (int, float))
                or not math.isfinite(score) or not math.isfinite(maximum)
                or maximum <= 0 or score < 0 or score > maximum):
            raise ValueError("スコアは0以上、配点以下の数値で指定してください")
        scores.append('<div><div class="score-top"><span>' + text(item["label"])
                      + '</span><span>' + text(score) + ' / ' + text(maximum)
                      + '</span></div><div class="bar" aria-hidden="true"><span style="width:'
                      + f'{score / maximum * 100:.2f}%' + '"></span></div></div>')
    values["scores"] = "".join(scores)
    values["scenarios"] = "".join('<tr>' + "".join('<td>' + text(item[key]) + '</td>' for key in
                                      ("label", "period", "sale_price", "balance", "sale_cost", "cash"))
                                    + '</tr>' for item in data["scenarios"])
    values["checks"] = "".join('<li>' + text(item) + '</li>' for item in data["checks"])
    source_url = data.get("source_url")
    if source_url:
        parsed = urlsplit(source_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("出典URLは認証情報を含まないhttps URLで指定してください")
        values["source_link"] = '<a href="' + text(source_url) + '" target="_blank" rel="noopener noreferrer">掲載ページを確認</a>'
    else:
        values["source_link"] = "元の掲載URLは記録されていません。"
    return Template((ROOT / "templates/report.html").read_text()).substitute(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="評価結果JSON")
    parser.add_argument("--output", type=Path, required=True, help="出力HTML")
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text())
        html = render(data)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html, encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"レポート生成失敗: {error}\n")
    print(f"Created: {args.output.resolve()}")


if __name__ == "__main__":
    main()
