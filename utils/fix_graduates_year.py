import json
import os

graduates_path = "backend/data/graduates.json"

if not os.path.exists(graduates_path):
    print("graduates.json が存在しません。")
    exit()

with open(graduates_path, "r", encoding="utf-8") as f:
    graduates = json.load(f)

updated = False

for g in graduates:

    # ① すでに graduated_year がある場合 → 何もしない
    if "graduated_year" in g:
        # もし日本語キーが残っていたら削除
        if "卒業年度" in g:
            g.pop("卒業年度", None)
            updated = True
        continue

    # ② 日本語キー「卒業年度」がある場合 → それを英語キーに移す
    if "卒業年度" in g:
        g["graduated_year"] = g["卒業年度"]
        g.pop("卒業年度", None)
        updated = True
        continue

    # ③ どちらも無い場合 → ID の先頭4桁から年度を生成
    sid = g.get("id", "")
    if len(sid) >= 4 and sid[:4].isdigit():
        g["graduated_year"] = int(sid[:4])
        updated = True
    else:
        print(f"⚠ ID から年度が取得できません: {sid}")

# 保存
if updated:
    with open(graduates_path, "w", encoding="utf-8") as f:
        json.dump(graduates, f, ensure_ascii=False, indent=2)
    print("卒業年度キーを修正しました。")
else:
    print("更新はありませんでした。")
