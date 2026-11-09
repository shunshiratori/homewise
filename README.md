# Homewise

自分用の不動産評価レポート。既存のCodex skillsによる1件の評価結果を、Chromeで見やすく表示する。

最初はHTMLレポートの表示を試作。オンラインアプリ化、過去物件との横並び比較、条件変更・再計算は対象外。
既存skills自体は変更していない。URL評価からレポート生成までの自動連携は未実装。

要件と検証状況は [プロダクト整理](docs/product-plan.md) を参照。

## HTML評価レポート

[表示サンプル](reports/sample.html) をChromeで開く。サーバー・API・追加パッケージ不要。
サンプルは既存の過去評価を使っており、最新の評価ではない。未算入費用や未検証の数値は画面に明示している。

```sh
python3 scripts/render_report.py examples/report.json --output reports/sample.html
```

入力例は [examples/report.json](examples/report.json)。別の評価を表示するときはこの形式でJSONを用意し、
物件名、判定、費用、根拠、注意点、評価条件を設定する。
`costs_note`・`scores_note`には、その評価固有の算入範囲や判定調整の説明を入れる。
不明なデータは「未確認」と明記し、サンプルの数字を流用しない。

出力はCSSを含む単体HTML。物件情報・評価条件・出典は折りたたみ表示でき、
「印刷 / PDF保存」からブラウザの印刷機能を使える。外部フォントや画像の読み込みは行わない。

## テスト

```sh
python3 -m unittest discover -s tests -v
git diff --check
```

## HOME’S取得の検証

Python 3とcurlを使用。追加パッケージ不要。

```sh
python3 scripts/probe_homes.py https://www.homes.co.jp/mansion/b-1259230001938/
```

価格・面積・管理費・修繕積立金などをJSONで出力する。金額は円。
未確認項目はnullとし、賃貸中・オーナーチェンジの記載をフラグ表示する。
相場調査や購入評価は行わない。SUUMOにはまだ対応していない。
HTTPエラー・必須項目の欠落時は終了コード1を返す。

保存済みHTMLによる再検証と、抽出処理のテスト：

```sh
python3 scripts/probe_homes.py https://www.homes.co.jp/mansion/b-1259230001938/ --html-file /tmp/homewise-homes-browser-headers.html
python3 -m unittest discover -s tests -v
```

取得成功は単一ページ・単一環境での検証結果であり、継続取得や他サイトでの成功を保証しない。
