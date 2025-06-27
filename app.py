import streamlit as st

def implied_probability_from_roi(original_odds, roi):
    if original_odds > 0:
        payout = original_odds / 100
    else:
        payout = 100 / abs(original_odds)
    p = (roi + 1) / (payout + 1)
    return p

def expected_roi(new_odds, true_prob):
    if new_odds > 0:
        payout = new_odds / 100
    else:
        payout = 100 / abs(new_odds)
    ev = true_prob * payout - (1 - true_prob)
    return ev * 100

st.title("Expected ROI Calculator")

original_odds = st.number_input("Original Odds (e.g. -100)", value=-100)
new_odds = st.number_input("New Odds (e.g. -105)", value=-105)
roi_percent = st.number_input("Bettor ROI (%)", value=10.0)

roi_decimal = roi_percent / 100
true_prob = implied_probability_from_roi(original_odds, roi_decimal)
expected_return = expected_roi(new_odds, true_prob)

st.write(f"Implied True Probability: {true_prob:.2%}")
st.write(f"Your Expected ROI: {expected_return:.2f}%")
