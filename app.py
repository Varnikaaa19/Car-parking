
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
from zoneinfo import ZoneInfo
from PIL import Image

# ---------- Config ----------
DATA_FILE = Path("data.json")
ASSETS_DIR = Path("assets")
SOURCE_IMAGE = ASSETS_DIR / "source.jpeg"
CAR_ICON = ASSETS_DIR / "car.png"
BIKE_ICON = ASSETS_DIR / "bike.png"
IST = ZoneInfo("Asia/Kolkata")

# ---------- Data I/O ----------
def load_data() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    # Default seed
    return {
        "location": "K P Towers",
        "availability": {"car": 1, "bike": 290},
        "currently_in": [
            {
                "vehicle_number": "DL1CAF8567",
                "vehicle_type": "CAR",
                "in_time": "2026-01-07 12:38:17",
                "status": "ALLOWED",
            }
        ],
    }

def save_data(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

# ---------- Icon extraction (from screenshot) ----------
def ensure_icons():
    ASSETS_DIR.mkdir(exist_ok=True)
    if CAR_ICON.exists() and BIKE_ICON.exists():
        return

    if not SOURCE_IMAGE.exists():
        return  # fallback will be used

    try:
        img = Image.open(SOURCE_IMAGE).convert("RGBA")
        w, h = img.size

        # Heuristic crops based on screenshot layout (percent ratios).
        # Adjust if your screenshot layout differs.
        car_box = (int(0.07 * w), int(0.26 * h), int(0.28 * w), int(0.34 * h))
        bike_box = (int(0.07 * w), int(0.40 * h), int(0.28 * w), int(0.49 * h))

        car_img = img.crop(car_box)
        bike_img = img.crop(bike_box)

        # Trim transparent borders (simple bounding box)
        def trim_alpha(im):
            bg = Image.new("RGBA", im.size, (255, 255, 255, 0))
            diff = Image.alpha_composite(bg, im)
            bbox = diff.getbbox()
            return im.crop(bbox) if bbox else im

        car_img = trim_alpha(car_img)
        bike_img = trim_alpha(bike_img)

        car_img.save(CAR_ICON)
        bike_img.save(BIKE_ICON)
    except Exception:
        # If anything fails, we’ll use emoji fallback in UI.
        pass

# ---------- UI Helpers ----------
def icon_img(path: Path, fallback: str, size_px: int = 36):
    if path.exists():
        st.image(str(path), width=size_px)
    else:
        st.markdown(f"<div style='font-size:{size_px}px'>{fallback}</div>", unsafe_allow_html=True)

def availability_pill(label: str, count: int, icon_path: Path, fallback_icon: str, color_hex: str):
    left, right = st.columns([1, 1])
    with left:
        st.markdown(
            f"""
            <div style="
                display:flex;align-items:center;gap:10px;
                border:1px solid #e5e7eb;border-radius:30px;padding:10px 14px;
                box-shadow:0 2px 8px rgba(0,0,0,0.04); background:#fff;">
                <div>""",
            unsafe_allow_html=True,
        )
        icon_img(icon_path, fallback_icon, size_px=32)
        st.markdown(
            f"""
                </div>
                <div style="font-size:18px;color:#2d3748">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            <div style="
                background:{color_hex};color:#fff;font-weight:800;
                padding:10px 18px;border-radius:26px;text-align:center;font-size:24px;">
                {count}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------- Page ----------
st.set_page_config(page_title="CUROPark", layout="centered")
ensure_icons()
data = load_data()

# Top bar (responsive width container)
st.markdown(
    """
    <style>
    /* Responsive container */
    .app-wrap{max-width:950px;margin:0 auto;}
    @media (max-width: 480px){ .pill{flex-direction:column;} }
    /* Table style tweaks */
    .stDataFrame div[role='table'] { font-size: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='app-wrap'>", unsafe_allow_html=True)

# Header
st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:10px;padding:8px 0;">
      <div style="font-weight:800;color:#1791DC;font-size:22px;">CUROPark</div>
      <div style="margin-left:auto;color:#1791DC;font-size:22px;">☰</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Location + current time (IST)
now_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S %Z")
st.markdown(f"### {data['location']}")
st.caption(f"Opened at: **{now_ist}**")

# Divider bar under title (like screenshot)
st.markdown(
    "<div style='height:6px;width:60px;background:#1791DC;border-radius:6px;margin:8px 0 16px'></div>",
    unsafe_allow_html=True,
)

# Availability section
st.subheader("Availability")
availability_pill("Parking Count", int(data["availability"]["car"]), CAR_ICON, "🚗", "#F59E0B")
st.write("")
availability_pill("Parking Count", int(data["availability"]["bike"]), BIKE_ICON, "🏍️", "#16A34A")

# Currently In — tabular
st.subheader("Currently In")
if data["currently_in"]:
    df = pd.DataFrame(data["currently_in"])
    # Column order + nicer labels
    df = df[["vehicle_number", "vehicle_type", "in_time", "status"]]
    df.columns = ["Vehicle Number", "Vehicle Type", "In Time", "Status"]
    st.dataframe(df, use_container_width=True)
else:
    st.info("No vehicles currently in.")

st.divider()
st.subheader("Add / Update")

with st.form("add_form", clear_on_submit=True):
    vnum = st.text_input("Vehicle number", "")
    vtype = st.selectbox("Vehicle type", ["CAR", "BIKE"])
    status = st.selectbox("Status", ["ALLOWED", "BLOCKED", "EXIT"])
    submitted = st.form_submit_button("Save entry")

if submitted:
    # Use current IST time on each submission
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S %Z")
    entry = {
        "vehicle_number": vnum.strip() or "UNKNOWN",
        "vehicle_type": vtype,
        "in_time": now,
        "status": status,
    }
    data["currently_in"].insert(0, entry)
    key = "car" if vtype == "CAR" else "bike"
    if status == "ALLOWED":
        data["availability"][key] = max(0, int(data["availability"][key]) - 1)
    elif status == "EXIT":
        data["availability"][key] = int(data["availability"][key]) + 1
    save_data(data)
    st.success("Saved. Data updated.")
    st.experimental_rerun()

# Footer
st.caption("Responsive UI • Streamlit")

st.markdown("</div>", unsafe_allow_html=True)

