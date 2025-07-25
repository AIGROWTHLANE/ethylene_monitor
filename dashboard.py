import streamlit as st
import boto3
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText

# --------------------
# Streamlit Configuration
# --------------------
st.set_page_config(page_title="Ethylene Monitoring Dashboard", layout="wide")

# --------------------
# Load Secrets
# --------------------
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL")
SENDER_PASSWORD = st.secrets.get("SENDER_PASSWORD")
RECIPIENT_EMAIL = st.secrets.get("RECIPIENT_EMAIL")

# --------------------
# Alert Settings
# --------------------
ETHYLENE_THRESHOLD = 2.0
ALERT_COOLDOWN_SECONDS = 1800  # 30 minutes

# --------------------
# Session State Init
# --------------------
if 'last_alert_time' not in st.session_state:
    st.session_state.last_alert_time = None

# --------------------
# Send Email Function
# --------------------
def send_email_alert(ethylene_level):
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECIPIENT_EMAIL:
        st.error("Email credentials are missing.")
        return

    subject = f"High Ethylene Alert"
    body = f"⚠️ Ethylene level is high ({ethylene_level} ppm)!"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            st.toast(f"Alert sent!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# --------------------
# Load Data from DynamoDB
# --------------------
@st.cache_data(ttl=60)
def load_data():
    try:
        dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
        table = dynamodb.Table("EthyleneReadings")
        response = table.scan()
        return response['Items']
    except Exception as e:
        st.error(f"❌ Error loading data from DynamoDB: {e}")
        return []

data = load_data()
df = pd.DataFrame(data)

# --------------------
# Validate and preprocess data
# --------------------
if df.empty or 'timestamp' not in df.columns or 'ethylene_ppm' not in df.columns:
    st.warning("No valid data available.")
    st.stop()

df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
df['ethylene_ppm'] = pd.to_numeric(df['ethylene_ppm'], errors='coerce')
df.dropna(subset=['timestamp', 'ethylene_ppm'], inplace=True)

# --------------------
# UI Layout
# --------------------
st.title("📊 Ethylene Monitoring Dashboard")

if df.empty:
    st.warning("No data received yet.")
    st.stop()

df.sort_values('timestamp', inplace=True)
latest = df.iloc[-1]
ethylene = latest['ethylene_ppm']
now = datetime.datetime.utcnow()

# Threshold Alert
if ethylene > ETHYLENE_THRESHOLD:
    last_alert = st.session_state.last_alert_time
    if not last_alert or (now - last_alert).total_seconds() > ALERT_COOLDOWN_SECONDS:
        send_email_alert(ethylene)
        st.session_state.last_alert_time = now

# Display
st.metric("Current Ethylene Level (ppm)", f"{ethylene:.2f}", delta=None)
st.line_chart(df.set_index('timestamp')['ethylene_ppm'])

# --------------------
# Auto-refresh every minute
# --------------------
st.caption("Dashboard auto-refreshes every 60 seconds.")
