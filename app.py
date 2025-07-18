import streamlit as st
import pandas as pd
import math

def bayesian_shrink(roi, sample_size, prior=0, prior_weight=30):
    """
    Shrinks ROI toward a prior (default 0) based on sample size.
    Higher sample size = less shrinkage. Lower sample size = more.
    """
    weight = sample_size / (sample_size + prior_weight)
    return weight * roi + (1 - weight) * prior

# Load the spreadsheet
df = pd.read_csv("bettor_stats.csv")

# --- Statistical parameters ---
z_score = 1.96  # 95% confidence
std_dev = 1.0   # conservative std dev for ROI
k = 100         # Bayesian shrinkage constant
prior_mean = 0.00  # prior average ROI

# --- Functions ---
def implied_true_probability(odds, roi):
    payout = odds / 100 if odds > 0 else 100 / abs(odds)
    return (roi + 1) / (payout + 1)

def expected_roi(odds, true_prob):
    payout = odds / 100 if odds > 0 else 100 / abs(odds)
    return (true_prob * payout - (1 - true_prob)) * 100

def kelly_fraction(odds, win_prob):
    payout = odds / 100 if odds > 0 else 100 / abs(odds)
    b = payout
    q = 1 - win_prob
    kelly = (b * win_prob - q) / b
    return max(0, kelly)  # avoid negative bets

def get_adjusted_roi(row):
    roi = row['ROI (%)'] / 100
    n = row['Sample Size']
    avg_bet = row['Avg Bet Size']
    margin_error = z_score * (std_dev / math.sqrt(n))
    shrink = n / (n + k)
    adj_roi = shrink * roi + (1 - shrink) * prior_mean
    adj_moe = shrink * margin_error
    return adj_roi, adj_moe, avg_bet, roi, n

# --- Create tabs ---
tab1, tab2 = st.tabs(["Bet Size Signal", "Multi-Bettor Signal"])

# ---------------- Tab 1 ----------------
with tab1:
    st.sidebar.header("Select Bettor & Bet Type")
    bettor = st.sidebar.selectbox("Bettor", sorted(df['Bettor'].unique()))

    bettor_df = df[df['Bettor'] == bettor]
    available_bet_types = sorted(bettor_df['Bet Type'].dropna().unique())
    bet_type = st.sidebar.selectbox("Bet Type", available_bet_types)

    row = df[(df['Bettor'] == bettor) & (df['Bet Type'] == bet_type)]
    if row.empty:
        st.error("No ROI data for that bettor + bet type.")
        st.stop()

    roi_decimal = row.iloc[0]['ROI (%)'] / 100
    sample_size = int(row.iloc[0]['Sample Size'])
    avg_bet_size_units = row.iloc[0]['Avg Bet Size']

    original_odds = st.number_input("Original Odds (the odds the bettor got)", value=-100)
    new_odds = st.number_input("New Odds (your current odds)", value=-105)
    specific_bet_size = st.number_input("How Big Was the Bettor's Bet?", value=float(avg_bet_size_units), min_value=0.0, step=0.1)

    margin_of_error = z_score * (std_dev / math.sqrt(sample_size))
    shrink_weight = sample_size / (sample_size + k)
    adjusted_roi = shrink_weight * roi_decimal + (1 - shrink_weight) * prior_mean
    adjusted_moe = shrink_weight * margin_of_error

    roi_lower = adjusted_roi - adjusted_moe
    roi_upper = adjusted_roi + adjusted_moe

    itp = implied_true_probability(original_odds, adjusted_roi)
    expected = expected_roi(new_odds, itp)

    signal_strength = specific_bet_size / avg_bet_size_units
    weighted_expected_roi = expected * signal_strength

    upper_itp = implied_true_probability(original_odds, roi_upper)
    lower_itp = implied_true_probability(original_odds, roi_lower)

    expected_upper = expected_roi(new_odds, upper_itp)
    expected_lower = expected_roi(new_odds, lower_itp)
    expected_roi_moe = (expected_upper - expected_lower) / 2

    kelly = kelly_fraction(new_odds, itp)
    kelly_half = kelly / 2
    recommended_units = kelly_half * 100

    signal_weighted_stake = kelly_half * signal_strength
    signal_weighted_units = signal_weighted_stake * 100

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

# ---------------- Tab 2 ----------------
with tab2:
    st.header("Multi-Bettor Signal")

    col1, col2 = st.columns(2)
    with col1:
        bettor_1 = st.selectbox("Bettor 1", sorted(df['Bettor'].unique()), key="bettor_1")
    with col2:
        bettor_2 = st.selectbox("Bettor 2", sorted(df['Bettor'].unique()), key="bettor_2")

    bet_type_1 = st.selectbox("Bet Type for Bettor 1", sorted(df[df['Bettor'] == bettor_1]['Bet Type'].dropna().unique()), key="bt1")
    bet_type_2 = st.selectbox("Bet Type for Bettor 2", sorted(df[df['Bettor'] == bettor_2]['Bet Type'].dropna().unique()), key="bt2")

# --- Filter data for each bettor ---
row_1 = df[(df['Bettor'] == bettor_1) & (df['Bet Type'] == bet_type_1)]
row_2 = df[(df['Bettor'] == bettor_2) & (df['Bet Type'] == bet_type_2)]

if row_1.empty or row_2.empty:
    st.error("Missing ROI data for one or both bettors.")
    st.stop()

# --- Extract ROI and sample size ---
roi_1 = row_1.iloc[0]['ROI (%)'] / 100
sample_size_1 = int(row_1.iloc[0]['Sample Size'])
avg_bet_size_1 = row_1.iloc[0]['Avg Bet Size']

roi_2 = row_2.iloc[0]['ROI (%)'] / 100
sample_size_2 = int(row_2.iloc[0]['Sample Size'])
avg_bet_size_2 = row_2.iloc[0]['Avg Bet Size']

# --- User inputs ---
odds_1 = st.number_input(f"{bettor_1}'s Odds", value=-110, key="odds_1")
odds_2 = st.number_input(f"{bettor_2}'s Odds", value=-110, key="odds_2")
user_odds = st.number_input("Your Current Odds", value=-110, key="multi_user_odds")

specific_bet_size_1 = st.number_input(f"{bettor_1}'s Bet Size (in units)", value=float(avg_bet_size_1), min_value=0.0, step=0.1)
specific_bet_size_2 = st.number_input(f"{bettor_2}'s Bet Size (in units)", value=float(avg_bet_size_2), min_value=0.0, step=0.1)

# --- Shrink ROI for both bettors ---
adjusted_roi_1 = bayesian_shrink(roi_1, sample_size_1)
adjusted_roi_2 = bayesian_shrink(roi_2, sample_size_2)

# --- Signal strength from bet size relative to average ---
signal_strength_1 = specific_bet_size_1 / avg_bet_size_1
signal_strength_2 = specific_bet_size_2 / avg_bet_size_2

# --- Implied true probabilities ---
p1 = implied_true_probability(odds_1, adjusted_roi_1)
p2 = implied_true_probability(odds_2, adjusted_roi_2)

# --- Weight each bettor's signal by sample size and bet size ---
weight_1 = sample_size_1 * signal_strength_1
weight_2 = sample_size_2 * signal_strength_2

# --- Weighted average of implied probabilities ---
combined_itp = (p1 * weight_1 + p2 * weight_2) / (weight_1 + weight_2)

# --- Expected ROI at user's odds ---
multi_expected_roi = expected_roi(user_odds, combined_itp)

# --- Kelly fraction ---
kelly_fraction_multi = kelly_fraction(user_odds, combined_itp)
recommended_units_multi = kelly_fraction_multi / 2 * 100  # Half-Kelly, converted to units

# --- Display Results ---
st.markdown("### Multi-Bettor Signal Results")
st.markdown(f"**Adjusted ROI ({bettor_1})**: {adjusted_roi_1:.2%}")
st.markdown(f"**Adjusted ROI ({bettor_2})**: {adjusted_roi_2:.2%}")
st.markdown(f"**Combined Implied Win Probability**: {combined_itp:.2%}")
st.markdown(f"**Expected ROI (Your Odds)**: {multi_expected_roi:.2%}")
st.markdown(f"**Recommended Stake**: {recommended_units_multi:.2f} units (Half Kelly)")
