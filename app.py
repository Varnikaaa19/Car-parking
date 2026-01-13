
import json
from pathlib import Path
from datetime import datetime
import streamlit as st

DATA_FILE = Path('data.json')

def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding='utf-8'))
    return {'location': 'K P Towers', 'availability': {'car': 0, 'bike': 0}, 'currently_in': []}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')

st.set_page_config(page_title='CUROPark', layout='centered')
data = load_data()

st.title(data['location'])
st.subheader('Availability')

car = int(data['availability']['car'])
bike = int(data['availability']['bike'])

st.markdown(f"""
<div style="border:1px solid #e5e7eb;border-radius:30px;padding:12px 16px;display:flex;justify-content:space-between;">
<span>Car Parking Count</span>
<span style="background:#F59E0B;color:#fff;font-weight:800;padding:6px 18px;border-radius:24px;">{car}</span>
</div>
""", unsafe_allow_html=True)

st.write("")
st.markdown(f"""
<div style="border:1px solid #e5e7eb;border-radius:30px;padding:12px 16px;display:flex;justify-content:space-between;">
<span>Bike Parking Count</span>
<span style="background:#16A34A;color:#fff;font-weight:800;padding:6px 18px;border-radius:24px;">{bike}</span>
</div>
""", unsafe_allow_html=True)

st.subheader('Currently In')
latest = data['currently_in'][0] if data['currently_in'] else None
if latest:
    c1, c2 = st.columns(2)
    with c1:
        st.caption('VEHICLE NUMBER'); st.write(f"**{latest['vehicle_number']}**")
    with c2:
        st.caption('VEHICLE TYPE'); st.write(f"**{latest['vehicle_type']}**")
    c3, c4 = st.columns(2)
    with c3:
        st.caption('IN TIME'); st.write(f"**{latest['in_time']}**")
    with c4:
        st.caption('STATUS'); st.write(f"**{latest['status']}**")
else:
    st.info('No vehicles currently in.')

st.divider()
st.subheader('Add / Update')

with st.form('add_form'):
    vnum = st.text_input('Vehicle number', '')
    vtype = st.selectbox('Vehicle type', ['CAR', 'BIKE'])
    status = st.selectbox('Status', ['ALLOWED', 'BLOCKED', 'EXIT'])
    submitted = st.form_submit_button('Save entry')

if submitted:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = {'vehicle_number': vnum.strip() or 'UNKNOWN', 'vehicle_type': vtype, 'in_time': now, 'status': status}
    data['currently_in'].insert(0, entry)
    key = 'car' if vtype == 'CAR' else 'bike'
    if status == 'ALLOWED':
        data['availability'][key] = max(0, int(data['availability'][key]) - 1)
    elif status == 'EXIT':
        data['availability'][key] = int(data['availability'][key]) + 1
    save_data(data)
    st.success('Saved. Data updated.')
    st.experimental_rerun()
