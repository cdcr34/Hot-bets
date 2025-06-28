import streamlit as st
import pandas as pd

# Load the spreadsheet
df = pd.read_csv("bettor_stats.csv")

# Sidebar selections
st.sidebar.header("Select Bettor & Bet Type")
bettor = st.sidebar.selectbox("Bettor", sorted(df['Bettor'].unique()))
bet_type = st.sidebar.selectbox("Bet Type", sorted(df['Bet Type'].unique()))

# Filter to get ROI from the spreadsheet
row = df[(df['Bettor'] == bettor) & (df['Bet Type'] == bet_type)]
if row.empty:
    st.error("No ROI data for that bettor + bet type.")
    st.stop()

roi_decimal = row.iloc[0]['ROI (%)'] / 100

# User inputs odds
original_odds = st.number_input("Original Odds (the odds the bettor got)", value=-100)
new_odds = st.number_input("New Odds (your current odds)", value=-105)

# Calculate Implied True Probability (ITP) from ROI
def implied_true_probability(original_odds, roi):
    payout = original_odds / 100 if original_odds > 0 else 100 / abs(original_odds)
    return (roi + 1) / (payout + 1)

# Calculate expected ROI from ITP and new odds
def expected_roi(new_odds, true_prob):
    payout = new_odds / 100 if new_odds > 0 else 100 / abs(new_odds)
    return (true_prob * payout - (1 - true_prob)) * 100

# Do the math
itp = implied_true_probability(original_odds, roi_decimal)
expected = expected_roi(new_odds, itp)

# Output results
st.title("Expected ROI")
st.markdown(f"**ROI from spreadsheet:** {roi_decimal * 100:.2f}%")
st.markdown(f"**Implied True Probability (ITP):** {itp:.2%}")
st.markdown(f"**Your Expected ROI at new odds:** {expected:.2f}%")
