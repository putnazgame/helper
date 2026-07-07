# -*- coding: utf-8 -*-
"""สร้างไฟล์ MP3 สำหรับทุกรายการ (ต้องการอินเทอร์เน็ตครั้งเดียว)"""
import json, os, sys
from gtts import gTTS

SAVE_FILE = "menu_items.json"
DEFAULT   = [
    "ขอน้ำดื่ม","อยากเข้าห้องน้ำ","ช่วยพยุงหน่อย",
    "เปิดพัดลม","ปิดพัดลม","เปิดไฟ",
    "ปิดไฟ","ปวดหัว","หิวข้าว",
    "โทรหาหมอ","ขอความช่วยเหลือ","อยากนอน",
]

items = json.load(open(SAVE_FILE, encoding="utf-8")) if os.path.exists(SAVE_FILE) else DEFAULT[:]
all_texts = items + ["ใช่", "ไม่", "โปรแกรมพร้อมใช้งาน"]

os.makedirs("audio", exist_ok=True)

for i, text in enumerate(all_texts, 1):
    path = os.path.join("audio", text + ".mp3")
    if os.path.exists(path):
        print(f"[{i}/{len(all_texts)}] มีอยู่แล้ว: {text}")
        continue
    print(f"[{i}/{len(all_texts)}] ดาวน์โหลด: {text} ...", end=" ", flush=True)
    try:
        gTTS(text=text, lang="th", slow=False).save(path)
        print("OK")
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\nเสร็จแล้ว — ไฟล์อยู่ที่โฟลเดอร์ audio/")
