import streamlit as st
import pandas as pd

# Load the spreadsheet
df = pd.read_csv("bettor_stats.csv")

# Sidebar selections
st.sidebar.header("Select Bettor & Bet Type")
bettor = st.sidebar.selectbox("Bettor", sorted(df['Bettor'].unique()))
# Filter the DataFrame to only rows for the selected bettor
bettor_df = df[df['Bettor'] == bettor]

# Get only bet types that this bettor has data for
available_bet_types = sorted(bettor_df['Bet Type'].dropna().unique())

# Let user choose from those bet types only
bet_type = st.sidebar.selectbox("Bet Type", available_bet_types)

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
st.markdown(f"**Bettor ROI:** {roi_decimal * 100:.2f}%")
st.markdown(f"**Implied True Probability (ITP):** {itp:.2%}")
st.markdown(f"**Expected ROI:** {expected:.2f}%")
sample_size = int(row.iloc[0]['Sample Size'])
st.markdown(f"**Sample Size:** {sample_size} bets")
import math
z_score = 1.96
std_dev = 1.0
margin_of_error = z_score * (std_dev / math.sqrt(sample_size))
st.markdown(f"**Margin of Error (95% CI): ±{margin_of_error * 100:.2f}%**")
