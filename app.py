import streamlit as st
import pandas as pd
import math

# Load data
df = pd.read_csv("bettor_stats.csv")

# --- Tabs ---
tab1, tab2 = st.tabs(["Bet Size Signal", "Multi-Bettor Signal"])

# -------------------------
# ----- TAB 1: BET SIZE SIGNAL -----
# -------------------------
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

    original_odds = st.number_input("Original Odds (the odds the bettor got)", value=-100, key="original_odds_tab1")
    new_odds = st.number_input("New Odds (your current odds)", value=-105, key="new_odds_tab1")
    specific_bet_size = st.number_input("How Big Was the Bettor's Bet?", value=float(avg_bet_size_units), min_value=0.0, step=0.1, key="bet_size_tab1")

    z_score = 1.96
    std_dev = 1.0
    k = 100
    prior_mean = 0.00

    margin_of_error = z_score * (std_dev / math.sqrt(sample_size))
    shrink_weight = sample_size / (sample_size + k)
    adjusted_roi = shrink_weight * roi_decimal + (1 - shrink_weight) * prior_mean
    adjusted_moe = shrink_weight * margin_of_error

    roi_lower = adjusted_roi - adjusted_moe
    roi_upper = adjusted_roi + adjusted_moe

    def implied_true_probability(odds, roi):
        payout = odds / 100 if odds > 0 else 100 / abs(odds)
        return (roi + 1) / (payout + 1)

    def expected_roi(odds, true_prob):
        payout = odds / 100 if odds > 0 else 100 / abs(odds)
        return (true_prob * payout - (1 - true_prob)) * 100

    itp = implied_true_probability(original_odds, adjusted_roi)
    expected = expected_roi(new_odds, itp)

    signal_strength = specific_bet_size / avg_bet_size_units
    weighted_expected_roi = expected * signal_strength

    upper_itp = implied_true_probability(original_odds, roi_upper)
    lower_itp = implied_true_probability(original_odds, roi_lower)
    expected_upper = expected_roi(new_odds, upper_itp)
    expected_lower = expected_roi(new_odds, lower_itp)
    expected_roi_moe = (expected_upper - expected_lower) / 2

    def kelly_fraction(odds, win_prob):
        payout = odds / 100 if odds > 0 else 100 / abs(odds)
        b = payout
        q = 1 - win_prob
        kelly = (b * win_prob - q) / b
        return max(0, kelly)

    kelly = kelly_fraction(new_odds, itp)
    kelly_half = kelly / 2
    recommended_units = kelly_half * 100
    signal_weighted_stake = kelly_half * signal_strength
    signal_weighted_units = signal_weighted_stake * 100

    # Results
    st.subheader(f"Bettor ROI: {roi_decimal * 100:.2f}%")
    st.markdown(f"**Sample Size:** {sample_size} bets")
    st.markdown(f"**Avg Bet Size:** {avg_bet_size_units:.2f} units")
    st.markdown("---")
    st.subheader(f"Bayesian Adjusted Bettor ROI: {adjusted_roi * 100:.2f}%")
    st.markdown(f"**95% CI:** {roi_lower * 100:.2f}% to {roi_upper * 100:.2f}%")
    st.markdown("---")
    st.subheader(f"Expected ROI: {expected:.2f}%")
    st.markdown(f"**Signal-Weighted Expected ROI:** {weighted_expected_roi:.2f}%")
    st.markdown(f"**MoE on Expected ROI (95% CI): ±{expected_roi_moe:.2f}%**")
    st.markdown("---")
    st.subheader(f"**Recommended Units to Bet:** {recommended_units:.2f} units")
    st.markdown(f"**Signal-Weighted Recommended Units:** {signal_weighted_units:.2f} units")

# -------------------------
# ----- TAB 2: MULTI-BETTOR SIGNAL -----
# -------------------------
with tab2:
    st.header("Multi-Bettor Signal")

    col1, col2 = st.columns(2)
    with col1:
        bettor1 = st.selectbox("Bettor 1", sorted(df['Bettor'].unique()), key="bettor1")
    with col2:
        bettor2 = st.selectbox("Bettor 2", sorted(df['Bettor'].unique()), key="bettor2")

    bet_type = st.selectbox("Bet Type (shared)", sorted(df['Bet Type'].dropna().unique()), key="bet_type_multibettor")

    odds_bettor1 = st.number_input("Odds Bettor 1 Got", value=-110, key="odds_bettor1")
    odds_bettor2 = st.number_input("Odds Bettor 2 Got", value=-110, key="odds_bettor2")
    your_odds = st.number_input("Your Current Odds", value=-110, key="your_odds")

    def get_adjusted_roi(bettor_name, odds):
        row = df[(df['Bettor'] == bettor_name) & (df['Bet Type'] == bet_type)]
        if row.empty:
            st.warning(f"No data for {bettor_name} and {bet_type}")
            return None, None, None
        roi = row.iloc[0]['ROI (%)'] / 100
        n = int(row.iloc[0]['Sample Size'])
        bet_size = float(row.iloc[0]['Avg Bet Size'])

        shrink = n / (n + k)
        adjusted = shrink * roi + (1 - shrink) * prior_mean
        itp = implied_true_probability(odds, adjusted)
        return adjusted, itp, bet_size

    roi1, itp1, bet_size1 = get_adjusted_roi(bettor1, odds_bettor1)
    roi2, itp2, bet_size2 = get_adjusted_roi(bettor2, odds_bettor2)

    if None not in [itp1, itp2]:
        agreement = "Agree" if itp1 > 0.5 and itp2 > 0.5 or itp1 < 0.5 and itp2 < 0.5 else "Conflict"
        st.markdown(f"**Signal Agreement:** `{agreement}`")

        avg_itp = (itp1 * bet_size1 + itp2 * bet_size2) / (bet_size1 + bet_size2)
        expected = expected_roi(your_odds, avg_itp)
        kelly = kelly_fraction(your_odds, avg_itp)
        kelly_half = kelly / 2
        recommended_units = kelly_half * 100

        st.markdown("---")
        st.subheader("Combined Multi-Bettor Output")
        st.markdown(f"**Avg Implied Win Probability:** {avg_itp:.2%}")
        st.markdown(f"**Expected ROI:** {expected:.2f}%")
        st.markdown(f"**Recommended Units to Bet (Half Kelly):** {recommended_units:.2f} units")
        st.markdown(f"**Signal Type:** Weighted by average bet size")
