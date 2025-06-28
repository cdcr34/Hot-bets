import streamlit as st
import pandas as pd
import math

# Load the spreadsheet
df = pd.read_csv("bettor_stats.csv")

# Sidebar selections
st.sidebar.header("Select Bettor & Bet Type")
bettor = st.sidebar.selectbox("Bettor", sorted(df['Bettor'].unique()))

# Only show bet types this bettor has data for
bettor_df = df[df['Bettor'] == bettor]
available_bet_types = sorted(bettor_df['Bet Type'].dropna().unique())
bet_type = st.sidebar.selectbox("Bet Type", available_bet_types)

# Filter to get ROI from the spreadsheet
row = df[(df['Bettor'] == bettor) & (df['Bet Type'] == bet_type)]
if row.empty:
    st.error("No ROI data for that bettor + bet type.")
    st.stop()

roi_decimal = row.iloc[0]['ROI (%)'] / 100
sample_size = int(row.iloc[0]['Sample Size'])

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

# Calculate margin of error for bettor ROI
z_score = 1.96  # 95% confidence
std_dev = 1.0   # conservative estimate
margin_of_error = z_score * (std_dev / math.sqrt(sample_size))

# Calculate ITP
itp = implied_true_probability(original_odds, roi_decimal)

# Calculate expected ROI
expected = expected_roi(new_odds, itp)

# Calculate payout for new odds (needed for confidence interval on expected ROI)
payout_new = new_odds / 100 if new_odds > 0 else 100 / abs(new_odds)

# Calculate confidence interval for ITP using ROI ± margin of error
upper_itp = implied_true_probability(original_odds, roi_decimal + margin_of_error)
lower_itp = implied_true_probability(original_odds, roi_decimal - margin_of_error)

# Calculate expected ROI bounds using upper and lower ITP
expected_roi_upper = expected_roi(new_odds, upper_itp)
expected_roi_lower = expected_roi(new_odds, lower_itp)

# Margin of error on expected ROI
expected_roi_moe = (expected_roi_upper - expected_roi_lower) / 2

# Display results
st.title("Expected ROI Based on Bettor Performance")
st.markdown(f"**Selected Bettor:** {bettor}")
st.markdown(f"**Bet Type:** {bet_type}")
st.markdown(f"**Bettor ROI:** {roi_decimal * 100:.2f}%")
st.markdown(f"**Sample Size:** {sample_size} bets")
st.markdown(f"**Margin of Error on Bettor ROI (95% CI): ±{margin_of_error * 100:.2f}%**")
st.markdown(f"**Implied True Probability (ITP):** {itp:.2%}")
st.markdown(f"**Expected ROI:** {expected:.2f}%")
st.markdown(f"**Margin of Error on Expected ROI (95% CI): ±{expected_roi_moe:.2f}%**")
