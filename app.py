import streamlit as st
import pandas as pd

# Load the spreadsheet
df = pd.read_csv("bettor_stats.csv")
st.write("DataFrame loaded:")
st.write(df.head())
st.write("Columns:", df.columns.tolist())

# Sidebar selections
st.sidebar.header("Select Bettor & Bet Type")
bettor = st.sidebar.selectbox("Bettor", sorted(df['Bettor'].unique()))
bet_type = st.sidebar.selectbox("Bet Type", sorted(df['Bet Type'].unique()))

# Filter to get ROI
row = df[(df['Bettor'] == bettor) & (df['Bet Type'] == bet_type)]
if row.empty:
    st.error("No ROI data for that bettor + bet type.")
    st.stop()

roi_decimal = row.iloc[0]['ROI (%)'] / 100

# Let user input odds
original_odds = st.number_input("Original Odds (e.g. -100)", value=-100)
new_odds = st.number_input("New Odds (e.g. -105)", value=-105)

# Calculate ITP
def implied_probability_from_roi(original_odds, roi):
    payout = original_odds / 100 if original_odds > 0 else 100 / abs(original_odds)
    return (roi + 1) / (payout + 1)

def expected_roi(new_odds, true_prob):
    payout = new_odds / 100 if new_odds > 0 else 100 / abs(new_odds)
    return (true_prob * payout - (1 - true_prob)) * 100

true_prob = implied_probability_from_roi(original_odds, roi_decimal)
your_roi = expected_roi(new_odds, true_prob)

st.write(f"Implied True Probability (ITP): {true_prob:.2%}")
st.write(f"Expected ROI at New Odds: {your_roi:.2f}%")
