import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import StringIO

# -----------------------
# Utility Functions
# -----------------------
def normalize_grant_data(df):
    """Normalize columns for consistency"""
    df = df.rename(columns=lambda x: x.strip().lower().replace(' ', '_'))
    
    if 'application_due_date' in df.columns:
        df['application_due_date'] = pd.to_datetime(df['application_due_date'], errors='coerce')
    
    if 'funding_quantum' in df.columns:
        df['funding_quantum'] = pd.to_numeric(df['funding_quantum'], errors='coerce')
    
    return df

def evaluate_relevance(df, issue_area=None, min_funding=None, max_funding=None):
    """Simple relevance scoring based on criteria"""
    df['relevance_score'] = 0
    
    if issue_area:
        df['relevance_score'] += df.get('issue_area', pd.Series([""]*len(df))).apply(
            lambda x: 1 if issue_area.lower() in str(x).lower() else 0
        )
    
    if min_funding:
        df['relevance_score'] += df.get('funding_quantum', pd.Series([0]*len(df))).apply(
            lambda x: 1 if x >= min_funding else 0
        )
    
    if max_funding:
        df['relevance_score'] += df.get('funding_quantum', pd.Series([0]*len(df))).apply(
            lambda x: 1 if x <= max_funding else 0
        )
    
    return df.sort_values(by='relevance_score', ascending=False)

def generate_alerts(df):
    """Generate reminders for grants nearing application due date"""
    alerts = []
    today = datetime.today()
    for _, row in df.iterrows():
        if pd.notnull(row.get('application_due_date')):
            days_left = (row['application_due_date'] - today).days
            if 0 <= days_left <= 7:
                alerts.append(f"Reminder: '{row['grant_name']}' is due in {days_left} day(s)!")
    return alerts

# -----------------------
# Streamlit UI
# -----------------------
st.title("Non-Profit Grant Tracker (OurSG Prototype)")
st.markdown("""
Upload a CSV or paste grant details below.  
The system will normalize, evaluate relevance, and give sustainability insights.
""")

# -----------------------
# Input: CSV upload or raw text
# -----------------------
uploaded_file = st.file_uploader("Upload grant CSV", type=['csv'])
pasted_data = st.text_area("Or paste grant details here (unstructured text)")

df = None

# Handle CSV
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, on_bad_lines='skip')
    except Exception as e:
        st.error(f"Error reading CSV: {e}")

# Handle pasted unstructured text
elif pasted_data:
    # Example parsing: convert raw text into one-row DataFrame
    grant_info = {
        "grant_name": "Active Citizen Grant",
        "description": pasted_data,
        "who_can_apply": "Anyone",
        "application_period": "All year round",
        "funding_cap": 20000
    }
    df = pd.DataFrame([grant_info])

# -----------------------
# Process & Display
# -----------------------
if df is not None and not df.empty:
    st.subheader("Structured Grant Info")
    st.dataframe(df)

    # Sidebar criteria for relevance scoring
    st.sidebar.subheader("Relevance Criteria")
    issue_area = st.sidebar.text_input("Filter by issue area (e.g., sport, health)")
    min_funding = st.sidebar.number_input("Min Funding Quantum", min_value=0, value=0)
    max_funding = st.sidebar.number_input("Max Funding Quantum", min_value=0, value=1000000)

    # Normalize and evaluate relevance
    df = normalize_grant_data(df)
    df = evaluate_relevance(df, issue_area, min_funding, max_funding)

    st.subheader("Grants Ranked by Relevance")
    # Show relevant columns if exist
    display_cols = [col for col in ['grant_name', 'issue_area', 'funding_quantum', 'application_due_date', 'relevance_score'] if col in df.columns]
    st.dataframe(df[display_cols])

    # Alerts & reminders
    st.subheader("Upcoming Deadlines")
    alerts = generate_alerts(df)
    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("No upcoming deadlines within 7 days!")
else:
    st.info("Upload a CSV or paste grant text to begin.")
