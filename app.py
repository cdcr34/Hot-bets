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

avg_bet_size_units = row.iloc[0]['Avg Bet Size']

# --- User inputs odds ---
original_odds = st.number_input("Original Odds (the odds the bettor got)", value=-100)
new_odds = st.number_input("New Odds (your current odds)", value=-105)
specific_bet_size = st.number_input(
    "How Big Was the Bettor's Bet?", 
    value=float(avg_bet_size_units), 
    min_value=0.0, 
    step=0.1
)

# --- Statistical parameters ---
z_score = 1.96  # 95% confidence
std_dev = 1.0   # conservative std dev for ROI
k = 100         # Bayesian shrinkage constant
prior_mean = 0.00  # prior average ROI

# --- Margin of Error ---
margin_of_error = z_score * (std_dev / math.sqrt(sample_size))

# --- Bayesian shrinkage ---
shrink_weight = sample_size / (sample_size + k)
adjusted_roi = shrink_weight * roi_decimal + (1 - shrink_weight) * prior_mean
adjusted_moe = shrink_weight * margin_of_error

# --- Confidence Interval for Adjusted ROI ---
roi_lower = adjusted_roi - adjusted_moe
roi_upper = adjusted_roi + adjusted_moe

# --- Implied True Probability function ---
def implied_true_probability(odds, roi):
    payout = odds / 100 if odds > 0 else 100 / abs(odds)
    return (roi + 1) / (payout + 1)

# --- Expected ROI function ---
def expected_roi(odds, true_prob):
    payout = odds / 100 if odds > 0 else 100 / abs(odds)
    return (true_prob * payout - (1 - true_prob)) * 100

# --- ITP & Expected ROI using adjusted ROI ---
itp = implied_true_probability(original_odds, adjusted_roi)
expected = expected_roi(new_odds, itp)

# Display the average bet size in units
signal_strength = specific_bet_size / avg_bet_size_units
weighted_expected_roi = expected * signal_strength

# --- Confidence intervals for ITP and Expected ROI ---
upper_itp = implied_true_probability(original_odds, roi_upper)
lower_itp = implied_true_probability(original_odds, roi_lower)

expected_upper = expected_roi(new_odds, upper_itp)
expected_lower = expected_roi(new_odds, lower_itp)
expected_roi_moe = (expected_upper - expected_lower) / 2

# --- Kelly Criterion ---
def kelly_fraction(odds, win_prob):
    payout = odds / 100 if odds > 0 else 100 / abs(odds)
    b = payout
    q = 1 - win_prob
    kelly = (b * win_prob - q) / b
    return max(0, kelly)  # avoid negative bets

kelly = kelly_fraction(new_odds, itp)
kelly_half = kelly / 2
recommended_units = kelly_half * 100  # assume 1 unit = 1% of bankroll

# --- Signal-weighted Kelly stake ---
signal_weighted_stake = kelly_half * signal_strength
signal_weighted_units = signal_weighted_stake * 100  # units = % of bankroll

# --- Display Results ---
st.subheader(f"Bettor ROI: {roi_decimal * 100:.2f}%")
st.markdown(f"**Sample Size:** {sample_size} bets")
st.markdown(f"**Avg Bet Size:** {avg_bet_size_units:.2f} units")
st.markdown("---")
st.subheader(f"Bayesian Adjusted Bettor ROI: {adjusted_roi * 100:.2f}%")
st.markdown(f"**95% CI:** {roi_lower * 100:.2f}% to {roi_upper * 100:.2f}%")
st.markdown(f"**Adjusted MoE (95% CI): ±{adjusted_moe * 100:.2f}%**")
st.markdown("---")
st.subheader(f"Expected ROI: {expected:.2f}%")
st.markdown(f"**95% CI:** {expected_lower:.2f}% to {expected_upper:.2f}%")
st.markdown(f"**MoE on Expected ROI (95% CI): ±{expected_roi_moe:.2f}%**")
st.markdown(f"**Signal-Weighted Expected ROI:** {weighted_expected_roi:.2f}%")
st.markdown("---")
st.subheader(f"**Recommended Units to Bet:** {recommended_units:.2f} units")
st.markdown(f"**Recommended Stake (Half-Kelly):** {kelly_half:.2%} of bankroll")
st.markdown(f"**Signal-Weighted Recommended Units:** {signal_weighted_units:.2f} units")
st.markdown(f"**Signal-Weighted Stake:** {signal_weighted_stake:.2%} of bankroll")
st.markdown("---")
st.subheader(f"Terms")
with st.expander("Sample Size"):
    st.markdown("""
    The number of bets included in the analysis. A larger sample size increases the reliability of the ROI estimate.
    """)

with st.expander("Margin of Error"):
    st.markdown("""
    An estimate of how much the true ROI might differ from the observed ROI due to randomness. Calculated based on sample size and assumed variance.
    """)

with st.expander("95% Confidence Interval"):
    st.markdown("""
    A range calculated from the data that, if we repeated the process many times, would contain the true ROI 95% of the time. 
    It reflects uncertainty in the estimate — wider intervals mean less precision, often due to smaller sample sizes or higher variance.
    """)

with st.expander("Unit Size"):
    st.markdown("""
    For each bettor, 1 unit is defined as their **average bet size** over the last 3 months. 
    This ensures ROI and stake sizing are scaled to that bettor’s typical risk level. I value 1 unit as 1% of my bankroll.
    CAUTION: Some bettors choose to place multiple of the same bet, making the average bet size smaller
    """)

with st.expander("Bayesian Adjusted Bettor ROI"):
    st.markdown("""
    Bayesian-adjusted ROI "shrinks" extreme values toward 0% based on sample size.  
    This helps reduce overconfidence from small datasets while allowing stronger signals from larger ones.
    """)

with st.expander("Expected ROI"):
    st.markdown("""
    The profit you expect to make on average per dollar bet, based on the bettor's implied true win probability and your current odds.
    """)

with st.expander("Signal-Weighted Expected ROI"):
    st.markdown("""
    The Expected ROI adjusted based on how large the bettor's stake was compared to their average. A larger bet implies higher confidence, increasing the weight of the ROI estimate.
    CAUTION: Some bettors choose to place multiple of the same bet, making the average bet size smaller
    """)

with st.expander("Recomended Units to bet (Kelly Criterion)"):
    st.markdown("""
    The Kelly Criterion is a formula used to determine the optimal bet size based on edge and odds.  
    It maximizes long-term growth by balancing risk and reward. This version uses half-Kelly to reduce volatility.
    """)
