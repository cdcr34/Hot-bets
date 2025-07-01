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

# --- Extract ROI and sample size ---
roi_decimal = row.iloc[0]['ROI (%)'] / 100
sample_size = int(row.iloc[0]['Sample Size'])

# --- User inputs odds ---
original_odds = st.number_input("Original Odds (the odds the bettor got)", value=-100)
new_odds = st.number_input("New Odds (your current odds)", value=-105)

# --- Statistical parameters ---
z_score = 1.96  # 95% confidence
std_dev = 1.0   # conservative std dev for ROI
k = 100         # Bayesian shrinkage constant
prior_mean = 0.00  # prior average ROI

# --- Observed ROI margin of error ---
margin_of_error = z_score * (std_dev / math.sqrt(sample_size))

# --- Bayesian shrinkage ---
shrink_weight = sample_size / (sample_size + k)
adjusted_roi = shrink_weight * roi_decimal + (1 - shrink_weight) * prior_mean
adjusted_moe = shrink_weight * margin_of_error

# Use adjusted ROI to calculate Implied True Probability (ITP)
def implied_true_probability(original_odds, roi):
    payout = original_odds / 100 if original_odds > 0 else 100 / abs(original_odds)
    return (roi + 1) / (payout + 1)

itp = implied_true_probability(original_odds, adjusted_roi)

# --- Expected ROI function ---
def expected_roi(new_odds, true_prob):
    payout = new_odds / 100 if new_odds > 0 else 100 / abs(new_odds)
    return (true_prob * payout - (1 - true_prob)) * 100

expected = expected_roi(new_odds, itp)

# --- ITP confidence bounds using adjusted ROI ± margin of error ---
upper_itp = implied_true_probability(original_odds, adjusted_roi + adjusted_moe)
lower_itp = implied_true_probability(original_odds, adjusted_roi - adjusted_moe)

# --- Calculate Kelly Fraction (fraction of bankroll to wager) ---
def kelly_fraction(odds, win_prob):
    payout = odds / 100 if odds > 0 else 100 / abs(odds)
    b = payout
    q = 1 - win_prob
    kelly = (b * win_prob - q) / b
    return max(0, kelly)  # avoid negative bets
kelly = kelly_fraction(new_odds, itp)
kelly_half = kelly / 2  # safer version

# Assume 1 unit = 1% of bankroll
recommended_units = kelly_half * 100

# --- Expected ROI bounds ---
expected_roi_upper = expected_roi(new_odds, upper_itp)
expected_roi_lower = expected_roi(new_odds, lower_itp)
expected_roi_moe = (expected_roi_upper - expected_roi_lower) / 2

# Margin of error on expected ROI
expected_roi_moe = (expected_roi_upper - expected_roi_lower) / 2

# Display results
st.subheader(f"Bettor ROI: {roi_decimal * 100:.2f}%")
st.markdown(f"**MoE on Bettor ROI (95% CI): ±{margin_of_error * 100:.2f}%**")
st.markdown(f"**Sample Size:** {sample_size} bets")
st.subheader(f"**Bayesian Adjusted Bettor ROI:** {adjusted_roi * 100:.2f}%")
st.markdown(f"**Adjusted MoE (95% CI): ±{adjusted_moe * 100:.2f}%**")
st.markdown(f"**Adjusted Confidence Interval:** {(adjusted_roi - adjusted_moe) * 100:.2f}% to {(adjusted_roi + adjusted_moe) * 100:.2f}%")
st.markdown("---")
st.subheader(f"Expected ROI: {expected:.2f}%")
st.markdown(f"**MoE on Expected ROI (95% CI): ±{expected_roi_moe:.2f}%**")
st.subheader(f"**Recommended Units to Bet:** {recommended_units:.2f} units")
st.markdown(f"**Recommended Stake (Half-Kelly):** {kelly_half:.2%} of bankroll")
