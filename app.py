import sqlite3
import time
from pathlib import Path
from typing import Optional, List
import streamlit as st

# ================== CONFIG ==================
APP_TITLE = "Vote: Who do you want to work with most?"
ADMIN_PASSWORD = "banana-hr"   # เปลี่ยนรหัสได้
MAX_CHOICES = 3
SHOW_TOP_N = 5

CANDIDATES = [
    "Apisit Wisai",
    "Areerat Tippayawong",
    "Athiwat Khamnon",
    "Atthaphon Kajitpongpanich",
    "Aunyamanee Pukkaew",
    "Bussaraporn Daungin",
    "Jirapong Nanta",
    "Kamonrat Sangkeiwrat",
    "Kronpongsakon Kronkum",
    "Nampheung Chuatay",
    "Nattapon Deebang",
    "Nutchaporn Jaengmongkol",
    "Nuttapon Comsoi",
    "Panupong Yodwong",
    "Paradon Saengjam",
    "Peerapan Khanchoom",
    "Piangsit Nualsri",
    "Pipatpon Kessuwan",
    "Pitakpong Chitsutti",
    "Pratpong Muaengwong",
    "Sai Lounge Mine",
    "Saranya Jeenmatchaya",
    "Sasipong Singprom",
    "Sirakrit Sermsuk",
    "Siwakon Sittirin",
    "Songyot Jaichai",
    "Suchonlaphat Suwanaphokin",
    "Sujaree Khumgoen",
    "Supasit Wiriyapap",
    "Suphuruek Somboon",
    "Tawan Chandsri",
    "Teerasak Wichai",
    "Thanabodee Krathu",
    "Thawatchai Sunarat",
    "Theerapan Khanthigul",
    "Thipawan Nanta",
    "Ungkairt Sirivoranankul",
    "Wiriya Jamol",
    "Worachet Baramee",
]

TOKEN_MODE = True
VALID_TOKENS = {
    "BC-001","BC-002","BC-003","BC-004","BC-005",
    "BC-006","BC-007","BC-008","BC-009","BC-010",
    "BC-011","BC-012","BC-013","BC-014","BC-015",
    "BC-016","BC-017","BC-018","BC-019","BC-020",
    "BC-021","BC-022","BC-023","BC-024","BC-025",
    "BC-026","BC-027","BC-028","BC-029","BC-030",
    "BC-031","BC-032","BC-033","BC-034","BC-035",
    "BC-036","BC-037","BC-038","BC-039",
}

DB_PATH = Path("votes.db")

# ================== DATABASE ==================
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate TEXT,
            token TEXT,
            created_at INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS used_tokens (
            token TEXT PRIMARY KEY,
            used_at INTEGER
        )
    """)
    conn.commit()
    conn.close()

def token_used(token: str) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM used_tokens WHERE token=?", (token,))
    used = c.fetchone() is not None
    conn.close()
    return used

def mark_token(token: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO used_tokens(token, used_at) VALUES (?,?)",
        (token, int(time.time()))
    )
    conn.commit()
    conn.close()

def add_votes(candidates: List[str], token: Optional[str]):
    conn = get_conn()
    c = conn.cursor()
    for name in candidates:
        c.execute(
            "INSERT INTO votes(candidate, token, created_at) VALUES (?,?,?)",
            (name, token, int(time.time()))
        )
    conn.commit()
    conn.close()

def top_n(n: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT candidate, COUNT(*) as cnt
        FROM votes
        GROUP BY candidate
        ORDER BY cnt DESC
        LIMIT ?
    """, (n,))
    rows = c.fetchall()
    conn.close()
    return rows

# ================== APP ==================
st.set_page_config(page_title=APP_TITLE)
init_db()

st.title(APP_TITLE)
st.caption(f"เลือกได้สูงสุด {MAX_CHOICES} คน / โหวตได้ 1 ครั้ง")

tab_vote, tab_result = st.tabs(["🗳️ Vote", "🏆 Results (Admin)"])

with tab_vote:
    token = st.text_input("โค้ดโหวต (จาก HR)").strip().upper()
    selected = st.multiselect(
        f"เลือกพนักงาน (สูงสุด {MAX_CHOICES} คน)",
        CANDIDATES
    )

    if st.button("Submit Vote"):
        if TOKEN_MODE:
            if token not in VALID_TOKENS:
                st.error("โค้ดไม่ถูกต้อง")
            elif token_used(token):
                st.error("โค้ดนี้ถูกใช้แล้ว")
            elif len(selected) == 0 or len(selected) > MAX_CHOICES:
                st.error("กรุณาเลือก 1–3 คน")
            else:
                add_votes(selected, token)
                mark_token(token)
                st.success("บันทึกคะแนนเรียบร้อย ขอบคุณค่ะ 💙")
        else:
            if len(selected) == 0 or len(selected) > MAX_CHOICES:
                st.error("กรุณาเลือก 1–3 คน")
            else:
                add_votes(selected, None)
                st.success("บันทึกคะแนนเรียบร้อย ขอบคุณค่ะ 💙")

with tab_result:
    pw = st.text_input("Admin password", type="password")
    if pw == ADMIN_PASSWORD:
        results = top_n(SHOW_TOP_N)
        for i, (name, cnt) in enumerate(results, start=1):
            st.write(f"#{i} {name} — {cnt} votes")

