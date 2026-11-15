"""Đọc/ghi dữ liệu JSON và CSV."""
import csv
import json
import os

DUONG_DAN_MAC_DINH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "du_lieu.json")


def luu_json(du_lieu, duong_dan=DUONG_DAN_MAC_DINH):
    os.makedirs(os.path.dirname(duong_dan), exist_ok=True)
    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump(du_lieu, f, ensure_ascii=False, indent=2)


def doc_json(duong_dan=DUONG_DAN_MAC_DINH):
    with open(duong_dan, encoding="utf-8") as f:
        return json.load(f)


def xuat_csv(hang, duong_dan, cot):
    # utf-8-sig để Excel mở đúng tiếng Việt
    with open(duong_dan, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cot)
        w.writeheader()
        w.writerows(hang)


def doc_csv(duong_dan):
    with open(duong_dan, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))
