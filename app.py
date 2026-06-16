import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="ระบบตรวจติดตามเครื่องจักร",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "factory.db"


# =========================
# DATABASE
# =========================
def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def read_sql(q, params=()):
    c = conn()
    df = pd.read_sql_query(q, c, params=params)
    c.close()
    return df


def exec_sql(q, params=()):
    c = conn()
    cur = c.cursor()
    cur.execute(q, params)
    c.commit()
    c.close()


def init_db():
    c = conn()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS machines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine_id TEXT UNIQUE,
        machine_name TEXT,
        line_name TEXT,
        area TEXT,
        machine_type TEXT,
        model TEXT,
        status TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alarms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        machine_id TEXT,
        alarm_name TEXT,
        severity TEXT,
        status TEXT,
        downtime_minutes INTEGER
    )
    """)

    c.commit()
    c.close()


def seed():
    df_count = read_sql("SELECT COUNT(*) AS total FROM machines")
    if int(df_count.iloc[0]["total"]) > 0:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = []

    for i in range(1, 121):
        status = "RUNNING"
        if i % 17 == 0:
            status = "STOP"
        elif i % 11 == 0:
            status = "WARNING"

        line = "LINE A" if i <= 40 else "LINE B" if i <= 80 else "LINE C"
        machine_type = "CNC" if i <= 40 else "LATHE" if i <= 80 else "MILLING"

        data.append((
            f"MC-{i:03d}",
            f"Machine {i:03d}",
            line,
            f"AREA-{(i % 5) + 1}",
            machine_type,
            f"MODEL-{i:03d}",
            status,
            now,
        ))

    c = conn()
    cur = c.cursor()
    cur.executemany("""
    INSERT INTO machines (
        machine_id, machine_name, line_name, area,
        machine_type, model, status, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    c.commit()
    c.close()


init_db()
seed()


# =========================
# CSS
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700;800&display=swap');

* {
    font-family: Sarabun, sans-serif !important;
}

.stApp {
    background: #d1d5db;
    color: #111827;
}

.block-container {
    padding: 1.2rem;
    max-width: 100%;
}

header[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="stAppDeployButton"],
[data-testid="stDecoration"],
#MainMenu,
footer {
    display: none !important;
    visibility: hidden !important;
}

.topbar {
    background: #374151;
    color: white;
    padding: 24px 30px;
    border-radius: 22px;
    margin-bottom: 18px;
    border: 3px solid #111827;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.title {
    font-size: 42px;
    font-weight: 800;
}

.subtitle {
    font-size: 18px;
    color: #e5e7eb;
}

.datetime-box {
    text-align: right;
}

.datetime {
    font-size: 28px;
    font-weight: 800;
}

.developer {
    font-size: 17px;
    color: #f3f4f6;
    margin-top: 5px;
}

.kpi-box {
    background: #f9fafb;
    border: 3px solid #111827;
    border-radius: 20px;
    padding: 20px;
    color: #111827;
    box-shadow: 0 6px 14px rgba(0,0,0,.18);
}

.kpi-label {
    font-size: 18px;
    font-weight: 800;
}

.kpi-value {
    font-size: 42px;
    font-weight: 800;
    margin-top: 8px;
}

.card-wrap {
    border-radius: 20px;
    padding: 18px;
    margin-bottom: 10px;
    border: 3px solid #111827;
    color: white;
    min-height: 185px;
    box-shadow: 0 8px 18px rgba(0,0,0,.25);
}

.running {
    background: #15803d;
}

.warning {
    background: #ca8a04;
    color: #111827;
}

.stop {
    background: #dc2626;
}

.machine-id {
    font-size: 28px;
    font-weight: 800;
}

.machine-name {
    font-size: 17px;
    margin-top: 6px;
}

.machine-status {
    font-size: 34px;
    font-weight: 800;
    margin-top: 18px;
}

.machine-meta {
    font-size: 15px;
    margin-top: 6px;
}

div.stButton > button {
    width: 100%;
    border-radius: 14px;
    border: 3px solid #111827;
    background: #f9fafb;
    color: #111827;
    font-size: 18px;
    font-weight: 800;
    padding: 12px;
}

div.stButton > button:hover {
    background: #111827;
    color: white;
}

[data-testid="stDataFrame"] {
    border: 3px solid #111827;
    border-radius: 16px;
}

input, textarea, select {
    color: #111827 !important;
}
</style>
""", unsafe_allow_html=True)


# =========================
# DIALOG EDIT
# =========================
@st.dialog("✏️ แก้ไขข้อมูลเครื่องจักร")
def edit_machine_dialog(machine_id):
    selected_df = read_sql(
        "SELECT * FROM machines WHERE machine_id = ?",
        (machine_id,)
    )

    if selected_df.empty:
        st.error("ไม่พบข้อมูลเครื่องจักร")
        return

    r = selected_df.iloc[0]

    st.markdown(f"### เครื่องจักร: `{machine_id}`")

    with st.form("edit_machine_form"):
        machine_name = st.text_input("Machine Name", value=r["machine_name"] or "")

        line_options = ["LINE A", "LINE B", "LINE C", "LINE D"]
        line_name = st.selectbox(
            "Line",
            line_options,
            index=line_options.index(r["line_name"]) if r["line_name"] in line_options else 0
        )

        area = st.text_input("Area", value=r["area"] or "")

        type_options = ["CNC", "LATHE", "MILLING", "PRESS", "ROBOT", "CONVEYOR", "OTHER"]
        machine_type = st.selectbox(
            "Machine Type",
            type_options,
            index=type_options.index(r["machine_type"]) if r["machine_type"] in type_options else 0
        )

        model = st.text_input("Model", value=r["model"] or "")

        status_options = ["RUNNING", "WARNING", "STOP"]
        status = st.selectbox(
            "Status",
            status_options,
            index=status_options.index(r["status"]) if r["status"] in status_options else 0
        )

        save = st.form_submit_button("💾 บันทึกข้อมูล", use_container_width=True)

    if save:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        exec_sql("""
        UPDATE machines
        SET machine_name = ?,
            line_name = ?,
            area = ?,
            machine_type = ?,
            model = ?,
            status = ?,
            updated_at = ?
        WHERE machine_id = ?
        """, (
            machine_name,
            line_name,
            area,
            machine_type,
            model,
            status,
            now,
            machine_id
        ))

        if status in ["WARNING", "STOP"]:
            exec_sql("""
            INSERT INTO alarms (
                timestamp, machine_id, alarm_name, severity, status, downtime_minutes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                now,
                machine_id,
                "Machine Status Changed",
                "HIGH" if status == "STOP" else "MEDIUM",
                "OPEN",
                0
            ))

        st.success("บันทึกข้อมูลลงฐานข้อมูลเรียบร้อยแล้ว")
        st.rerun()

    st.markdown("---")

    confirm_delete = st.checkbox("ยืนยันการลบเครื่องจักรนี้")

    if st.button("🗑️ ลบเครื่องจักร", use_container_width=True):
        if confirm_delete:
            exec_sql("DELETE FROM machines WHERE machine_id = ?", (machine_id,))
            exec_sql("DELETE FROM alarms WHERE machine_id = ?", (machine_id,))
            st.success("ลบข้อมูลเรียบร้อยแล้ว")
            st.rerun()
        else:
            st.warning("กรุณาติ๊กยืนยันก่อนลบ")


# =========================
# DATA
# =========================
df = read_sql("SELECT * FROM machines ORDER BY machine_id")

total = len(df)
running = len(df[df["status"] == "RUNNING"])
warning = len(df[df["status"] == "WARNING"])
stop = len(df[df["status"] == "STOP"])
availability = round((running / total) * 100, 1) if total else 0

current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")


# =========================
# TOP BAR
# =========================
st.markdown(f"""
<div class="topbar">
    <div>
        <div class="title">🏭 ระบบตรวจติดตามเครื่องจักร</div>
        <div class="subtitle">บริษัท ซิกม่า แอนด์ ฮาร์ท จำกัด</div>
    </div>
    <div class="datetime-box">
        <div class="datetime">{current_datetime}</div>
        <div class="developer">พัฒนาระบบโดย นายโกสินทร์ แดงวิจิตร</div>
    </div>
</div>
""", unsafe_allow_html=True)


# =========================
# KPI
# =========================
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">TOTAL MACHINES</div>
        <div class="kpi-value">{total}</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">RUNNING</div>
        <div class="kpi-value">🟢 {running}</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">WARNING</div>
        <div class="kpi-value">🟡 {warning}</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">STOP</div>
        <div class="kpi-value">🔴 {stop}</div>
    </div>
    """, unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">AVAILABILITY</div>
        <div class="kpi-value">{availability}%</div>
    </div>
    """, unsafe_allow_html=True)


# =========================
# MACHINE CARDS
# =========================
st.markdown("## 📺 Machine Status Board")

df_show = read_sql("""
SELECT *
FROM machines
ORDER BY
CASE status
    WHEN 'STOP' THEN 1
    WHEN 'WARNING' THEN 2
    ELSE 3
END,
machine_id
LIMIT 36
""")

cols = st.columns(6)

for i, r in df_show.iterrows():
    status = str(r["status"]).upper()

    if status == "RUNNING":
        css = "running"
        status_text = "RUNNING"
    elif status == "WARNING":
        css = "warning"
        status_text = "WARNING"
    else:
        css = "stop"
        status_text = "STOP"

    with cols[i % 6]:
        st.markdown(f"""
        <div class="card-wrap {css}">
            <div class="machine-id">{r["machine_id"]}</div>
            <div class="machine-name">{r["machine_name"]}</div>
            <div class="machine-status">{status_text}</div>
            <div class="machine-meta">LINE: {r["line_name"]}</div>
            <div class="machine-meta">AREA: {r["area"]}</div>
            <div class="machine-meta">TYPE: {r["machine_type"]}</div>
            <div class="machine-meta">MODEL: {r["model"]}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"✏️ แก้ไข {r['machine_id']}", key=f"edit_{r['machine_id']}"):
            edit_machine_dialog(r["machine_id"])


# =========================
# ADD MACHINE
# =========================
st.markdown("---")
st.markdown("## ➕ เพิ่มเครื่องจักรใหม่")

with st.form("add_machine_form"):
    a1, a2, a3 = st.columns(3)

    with a1:
        new_id = st.text_input("Machine ID", placeholder="เช่น MC-121")
        new_name = st.text_input("Machine Name", placeholder="เช่น Machine 121")
        new_line = st.selectbox("Line", ["LINE A", "LINE B", "LINE C", "LINE D"], key="add_line")

    with a2:
        new_area = st.text_input("Area", placeholder="เช่น AREA-1")
        new_type = st.selectbox(
            "Machine Type",
            ["CNC", "LATHE", "MILLING", "PRESS", "ROBOT", "CONVEYOR", "OTHER"],
            key="add_type"
        )
        new_model = st.text_input("Model", placeholder="เช่น MODEL-121")

    with a3:
        new_status = st.selectbox("Status", ["RUNNING", "WARNING", "STOP"], key="add_status")

    add = st.form_submit_button("✅ เพิ่มข้อมูล")

if add:
    if not new_id.strip():
        st.error("กรุณากรอก Machine ID")
    else:
        try:
            exec_sql("""
            INSERT INTO machines (
                machine_id, machine_name, line_name, area,
                machine_type, model, status, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_id.strip(),
                new_name.strip(),
                new_line,
                new_area.strip(),
                new_type,
                new_model.strip(),
                new_status,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            st.success("เพิ่มข้อมูลเครื่องจักรเรียบร้อยแล้ว")
            st.rerun()

        except sqlite3.IntegrityError:
            st.error("Machine ID นี้มีอยู่แล้วในระบบ")


# =========================
# TABLE
# =========================
st.markdown("---")
st.markdown("## 📋 ตารางข้อมูลทั้งหมด")

df_all = read_sql("""
SELECT 
    machine_id,
    machine_name,
    line_name,
    area,
    machine_type,
    model,
    status,
    updated_at
FROM machines
ORDER BY machine_id
""")

st.dataframe(df_all, use_container_width=True, height=500)

csv = df_all.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="📥 ดาวน์โหลดข้อมูลเป็น CSV",
    data=csv,
    file_name="machine_master.csv",
    mime="text/csv",
    use_container_width=True
)