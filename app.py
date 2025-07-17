import streamlit as st
import pandas as pd
import math

# Load the spreadsheet
df = pd.read_csv("bettor_stats.csv")

# --- Existing code for single bettor signal ---

# (You can keep your current code here for single bettor signal)

# --- New Multi-Bettor Signal tab ---
st.sidebar.header("Select App Mode")
app_mode = st.sidebar.radio("Choose Mode:", ["Bet Size Signal", "Multi-Bettor Signal"])

if app_mode == "Multi-Bettor Signal":
    st.title("Multi-Bettor Signal")

    # Select two bettors
    bettor_list = sorted(df['Bettor'].unique())
    bettor1 = st.selectbox("Select Bettor 1", bettor_list, key="bettor1")
    bettor2 = st.selectbox("Select Bettor 2", bettor_list, key="bettor2")

    # Filter bet types common to both bettors
    bet_types1 = set(df[df['Bettor'] == bettor1]['Bet Type'].dropna().unique())
    bet_types2 = set(df[df['Bettor'] == bettor2]['Bet Type'].dropna().unique())
    common_bet_types = sorted(bet_types1.intersection(bet_types2))

    if not common_bet_types:
        st.error("No common bet types between the two bettors.")
        st.stop()

    bet_type = st.selectbox("Select Bet Type", common_bet_types)

    # Get ROI, sample size, avg bet size for bettor 1
    row1 = df[(df['Bettor'] == bettor1) & (df['Bet Type'] == bet_type)]
    roi1 = row1.iloc[0]['ROI (%)'] / 100
    sample_size1 = int(row1.iloc[0]['Sample Size'])
    avg_bet_size1 = row1.iloc[0]['Avg Bet Size']

    # Get ROI, sample size, avg bet size for bettor 2
    row2 = df[(df['Bettor'] == bettor2) & (df['Bet Type'] == bet_type)]
    roi2 = row2.iloc[0]['ROI (%)'] / 100
    sample_size2 = int(row2.iloc[0]['Sample Size'])
    avg_bet_size2 = row2.iloc[0]['Avg Bet Size']

    # User inputs odds and bet sizes
    original_odds1 = st.number_input(f"{bettor1} Original Odds", value=-100, key="orig_odds1")
    original_odds2 = st.number_input(f"{bettor2} Original Odds", value=-100, key="orig_odds2")
    your_odds = st.number_input("Your Current Odds", value=-105, key="your_odds")

    bet_size1 = st.number_input(f"{bettor1} Bet Size (units)", value=float(avg_bet_size1), min_value=0.0, step=0.1, key="bet_size1")
    bet_size2 = st.number_input(f"{bettor2} Bet Size (units)", value=float(avg_bet_size2), min_value=0.0, step=0.1, key="bet_size2")

    # Helper functions
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
        return max(0, kelly)  # no negative bets

    # Calculate bettors' implied true probabilities
    itp1 = implied_true_probability(original_odds1, roi1)
    itp2 = implied_true_probability(original_odds2, roi2)

    # Check agreement (both > 0.5 or both < 0.5)
    agree = (itp1 > 0.5 and itp2 > 0.5) or (itp1 < 0.5 and itp2 < 0.5)
    agreement_str = "Agree" if agree else "Conflict"
    st.markdown(f"**Signal Agreement:** {agreement_str}")

    if agree:
        # Calculate Kelly fractions per bettor
        kelly1 = kelly_fraction(your_odds, itp1)
        kelly2 = kelly_fraction(your_odds, itp2)

        # Combine Kelly fractions weighted by bet sizes
        total_bet_size = bet_size1 + bet_size2
        weighted_kelly = (kelly1 * bet_size1 + kelly2 * bet_size2) / total_bet_size if total_bet_size > 0 else 0
        weighted_kelly_half = weighted_kelly / 2
        recommended_units = weighted_kelly_half * 100  # units as % of bankroll

        # Calculate average implied true probability weighted by bet size
        avg_itp = (itp1 * bet_size1 + itp2 * bet_size2) / total_bet_size if total_bet_size > 0 else 0
        expected = expected_roi(your_odds, avg_itp)

        st.markdown("---")
        st.subheader("Combined Multi-Bettor Signal Output")
        st.markdown(f"**Avg Implied Win Probability:** {avg_itp:.2%}")
        st.markdown(f"**Expected ROI:** {expected:.2f}%")
        st.markdown(f"**Recommended Units to Bet (Half Kelly):** {recommended_units:.2f} units")
    else:
        st.warning("⚠️ The bettors have conflicting signals. Consider betting less or skipping this bet.")
