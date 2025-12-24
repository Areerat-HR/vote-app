import sqlite3
import time
from pathlib import Path
from typing import List
import streamlit as st

# ================== CONFIG ==================
APP_TITLE = "Vote: Who do you want to work with the most?"
ADMIN_PASSWORD = "22"
MAX_CHOICES = 3
SHOW_TOP_N = 5
FORBIDDEN_CANDIDATE = "Jirapong Nanta"   # 🚫 ห้ามโหวตชื่อนี้

EMPLOYEES = [
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

DB_PATH = Path("votes.db")

# ================== DATABASE ==================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter TEXT,
            candidate TEXT,
            created_at INTEGER
        )
    """)

    c.execute("PRAGMA table_info(votes)")
    cols = {row[1] for row in c.fetchall()}
    required = {"id", "voter", "candidate", "created_at"}

    if not required.issubset(cols):
        c.execute("DROP TABLE IF EXISTS votes")
        c.execute("""
            CREATE TABLE votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voter TEXT,
                candidate TEXT,
                created_at INTEGER
            )
        """)

    conn.commit()
    conn.close()

def has_voted(voter: str) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM votes WHERE voter=? LIMIT 1", (voter,))
    voted = c.fetchone() is not None
    conn.close()
    return voted

def add_votes(voter: str, candidates: List[str]):
    conn = get_conn()
    c = conn.cursor()
    now_ts = int(time.time())
    for name in candidates:
        c.execute(
            "INSERT INTO votes(voter, candidate, created_at) VALUES (?,?,?)",
            (voter, name, now_ts)
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
        ORDER BY cnt DESC, candidate ASC
        LIMIT ?
    """, (n,))
    rows = c.fetchall()
    conn.close()
    return rows

def not_voted_yet():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT voter FROM votes")
    voted = {row[0] for row in c.fetchall()}
    conn.close()
    return sorted([e for e in EMPLOYEES if e not in voted])

def reset_votes():
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM votes")
    conn.commit()
    conn.close()

# ================== APP ==================
st.set_page_config(page_title=APP_TITLE)
init_db()

st.title(APP_TITLE)
st.caption(f"เลือกได้สูงสุด {MAX_CHOICES} คน / โหวตได้ 1 ครั้ง")

tab_vote, tab_admin = st.tabs(["🗳️ Vote", "🏆 Results (HR)"])

# ------------------ VOTE TAB ------------------
with tab_vote:
    voter = st.selectbox("ชื่อของคุณ", EMPLOYEES)

    # ห้ามโหวตตัวเอง และห้ามโหวตชื่อที่ถูกแบน
    candidate_options = [
        e for e in EMPLOYEES
        if e != voter and e != FORBIDDEN_CANDIDATE
    ]

    st.info(f"คุณเลือกโหวตได้ไม่เกิน {MAX_CHOICES} คน")
    st.warning(f"❌ ไม่อนุญาตให้โหวตชื่อ {FORBIDDEN_CANDIDATE}")

    choices = st.multiselect(
        "เลือกพนักงานที่อยากทำงานด้วยมากที่สุด",
        candidate_options,
        max_selections=MAX_CHOICES,
    )

    if st.button("Submit Vote"):
        if FORBIDDEN_CANDIDATE in choices:
            st.error("ไม่อนุญาตให้โหวตชื่อนี้")
        elif has_voted(voter):
            st.error("คุณได้โหวตไปแล้ว")
        elif len(choices) == 0:
            st.error("กรุณาเลือกอย่างน้อย 1 คน")
        else:
            add_votes(voter, choices)
            st.success("บันทึกคะแนนเรียบร้อย ขอบคุณค่ะ 💙")

# ------------------ ADMIN TAB ------------------
with tab_admin:
    if "reset_done" not in st.session_state:
        st.session_state.reset_done = False

    pw = st.text_input("HR password", type="password")

    if pw == ADMIN_PASSWORD:
        if st.session_state.reset_done:
            st.success("ลบผลโหวตทั้งหมดเรียบร้อยแล้ว ✅")

        st.subheader(f"🏆 Top {SHOW_TOP_N} ผู้ได้รับคะแนนสูงสุด")
        rows = top_n(SHOW_TOP_N)
        if rows:
            for i, (name, cnt) in enumerate(rows, start=1):
                st.write(f"#{i} {name} — {cnt} votes")
        else:
            st.info("ยังไม่มีคะแนนโหวต")

        st.subheader("📋 พนักงานที่ยังไม่ได้โหวต")
        remaining = not_voted_yet()
        if remaining:
            for name in remaining:
                st.write(f"- {name}")
        else:
            st.success("พนักงานโหวตครบทุกคนแล้ว 🎉")

        st.divider()
        st.subheader("⚠️ HR Only: Reset Votes")
        confirm = st.checkbox("ยืนยันว่าต้องการลบคะแนนโหวตทั้งหมด")

        if st.button("🗑️ Reset all votes"):
            if not confirm:
                st.warning("กรุณาติ๊กยืนยันก่อนลบข้อมูล")
            else:
                reset_votes()
                st.session_state.reset_done = True
                st.rerun()

    elif pw != "":
        st.error("รหัสผ่านไม่ถูกต้อง")
