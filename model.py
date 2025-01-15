import numpy as np
import streamlit as st

# --------------------------------------
#          CONFIGURATIONS
# --------------------------------------
DEFAULT_DISCOUNT_RATE = 0.15  # Adjusted for startup biotech firms

# Phase success probabilities
PHASE_PROBABILITIES = {
    "Preclinical": 0.33,
    "Phase 1": 0.6,
    "Phase 2": 0.36,
    "Phase 3": 0.63
}

# Rare disease probabilities
RARE_DISEASE_PHASE_PROBABILITIES = {
    "Preclinical": 0.4,
    "Phase 1": 0.7,
    "Phase 2": 0.45,
    "Phase 3": 0.8
}

# Clinical development costs based on Pharmagellan
CLINICAL_DEVELOPMENT_COSTS = {
    "Preclinical": 30e6,  # $10-50M range
    "Phase 1": 10e6,      # $2-20M range
    "Phase 2": 50e6,      # $10-100M range
    "Phase 3": 150e6      # $50-300M range
}

# Pricing adjustments
EX_U_S_PRICE_FACTOR = 0.5  # Normalization factor for non-U.S. prices
ANNUAL_PRICE_INCREASE = 0.02  # Conservative annual increase

# Timeframes for revenue modeling
DEFAULT_RAMP_YEARS = 6
DEFAULT_PEAK_YEARS = 7
DEFAULT_DECLINE_YEARS = 8

# --------------------------------------
#          HELPER FUNCTIONS
# --------------------------------------
def calculate_npv(cash_flows: list, discount_rate: float) -> float:
    """
    Calculates the Net Present Value (NPV) of a series of cash flows.
    """
    return sum(cf / ((1 + discount_rate) ** t) for t, cf in enumerate(cash_flows, start=1))


def calculate_roi(npv: float, total_investment: float) -> float:
    """
    Calculates the Return on Investment (ROI).
    """
    return (npv - total_investment) / total_investment * 100 if total_investment > 0 else float('nan')


def calculate_revenue_curve(eligible_population, price_per_patient, market_penetration, ramp_years, peak_years, decline_years, decline_rate):
    """
    Generates revenue over time with ramp-up, peak, and decline phases.
    """
    peak_revenue = eligible_population * price_per_patient * (market_penetration / 100)

    # Ramp-up phase (S-curve)
    ramp_curve = [peak_revenue * p for p in np.linspace(0.1, 1.0, ramp_years)]

    # Peak phase (constant revenue for a defined period)
    peak_curve = [peak_revenue] * peak_years

    # Decline phase (exponential decay)
    decline_curve = [peak_revenue * ((1 - decline_rate) ** year) for year in range(1, decline_years + 1)]

    # Combine all phases
    return ramp_curve + peak_curve + decline_curve


def simulate_pipeline_cash_flows(
    eligible_population, price_per_patient, market_penetration, delay_years, ramp_years, peak_years, decline_years, decline_rate
):
    """
    Simulates cash flows for a pipeline product using revenue ramp-up, peak, and decline phases.
    """
    cash_flows = [-500e6 for _ in range(delay_years)]  # Negative cash flows for delay period
    revenue_curve = calculate_revenue_curve(
        eligible_population, price_per_patient, market_penetration, ramp_years, peak_years, decline_years, decline_rate
    )
    cash_flows.extend(revenue_curve)
    return cash_flows


def estimate_funding_requirements(pipeline_cash_flows, phase_costs):
    """
    Estimates the total funding required based on the cash flow projections, broken down by development phase.
    """
    pre_revenue_cash_flows = [cf for cf in pipeline_cash_flows if cf < 0]
    breakdown = {
        phase: phase_costs[phase] for phase in phase_costs
    }
    return {
        "total_funding": sum(breakdown.values()),
        "breakdown": breakdown
    }

# --------------------------------------
#          STREAMLIT APP
# --------------------------------------
def main():
    st.title("📈 Biotech Startup Pipeline NPV Tool 🧬")

    with st.expander("Disclaimer"):
        st.write(
            """
            This application provides a simplified tool to calculate the NPV of biotech pipeline assets based on user assumptions.
            It is designed for early-stage startups and does not include public market data or external valuation comparisons.
            """
        )

    st.subheader("Pipeline Inputs")
    num_assets = st.number_input("Number of Pipeline Assets:", min_value=1, max_value=10, value=1, step=1)

    pipeline_cash_flows = []
    total_investment = 0

    for i in range(num_assets):
        st.write(f"**Pipeline Asset {i+1}**")

        rare_disease = st.radio(
            f"Is Asset {i+1} a Rare Disease?",
            options=["Yes", "No"],
            index=1,
            key=f"rare_{i}",
            help="Indicate if the disease is classified as rare."
        )

        probabilities = RARE_DISEASE_PHASE_PROBABILITIES if rare_disease == "Yes" else PHASE_PROBABILITIES

        phase = st.selectbox(
            f"Select Phase for Asset {i+1}:",
            options=list(probabilities.keys()),
            key=f"phase_{i}",
            help="Select the current phase of clinical trials for this asset."
        )
        phase_probability = probabilities[phase]

        col1, col2 = st.columns(2)

        with col1:
            eligible_population = st.number_input(
                f"Eligible Patient Population for Asset {i+1}:",
                min_value=0,
                value=0,
                key=f"pop_{i}",
                help="The estimated number of patients who could benefit from this treatment."
            )

            market_penetration_rate = st.slider(
                f"Market Penetration Rate for Asset {i+1} (%):",
                min_value=0,
                max_value=100,
                value=50,
                key=f"penetration_{i}",
                help="Percentage of the eligible population expected to use this treatment."
            )

            price_per_patient = st.number_input(
                f"Price per Patient for Asset {i+1} (USD):",
                min_value=0.0,
                value=100000.0,
                key=f"price_{i}",
                help="Treatment price per patient."
            )

        with col2:
            ramp_years = st.slider(
                f"Years to Reach Peak Revenue for Asset {i+1}:",
                min_value=1,
                max_value=10,
                value=DEFAULT_RAMP_YEARS,
                key=f"ramp_{i}",
                help="Time needed to achieve peak sales."
            )

            peak_years = st.slider(
                f"Years at Peak Revenue for Asset {i+1}:",
                min_value=1,
                max_value=10,
                value=DEFAULT_PEAK_YEARS,
                key=f"peak_{i}",
                help="Duration of peak revenue."
            )

            decline_years = st.slider(
                f"Years of Revenue Decline for Asset {i+1}:",
                min_value=1,
                max_value=20,
                value=DEFAULT_DECLINE_YEARS,
                key=f"decline_{i}",
                help="Number of years revenue decreases after peak."
            )

            decline_rate = st.slider(
                f"Annual Decline Rate for Asset {i+1} (%):",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                key=f"decline_rate_{i}",
                help="Rate at which revenue declines annually after peak."
            )

        cash_flows = simulate_pipeline_cash_flows(
            eligible_population=eligible_population,
            price_per_patient=price_per_patient,
            market_penetration=market_penetration_rate,
            delay_years=0,  # No delay assumed in this simplified version
            ramp_years=ramp_years,
            peak_years=peak_years,
            decline_years=decline_years,
            decline_rate=decline_rate
        )

        total_investment += abs(sum(cf for cf in cash_flows if cf < 0))
        risk_adjusted_cash_flows = [cf * phase_probability for cf in cash_flows]
        pipeline_cash_flows.extend(risk_adjusted_cash_flows)

    npv_pipeline = calculate_npv(pipeline_cash_flows, DEFAULT_DISCOUNT_RATE)
    funding_requirements = estimate_funding_requirements(pipeline_cash_flows, CLINICAL_DEVELOPMENT_COSTS)
    roi = calculate_roi(npv_pipeline, total_investment)

    st.subheader("Valuation Results")
    st.write(f"NPV of Pipeline: ${npv_pipeline:,.2f}")
    st.write(f"Total Funding Requirements: ${funding_requirements['total_funding']:,.2f}")
    st.write("Funding Breakdown by Phase:")
    for phase, amount in funding_requirements['breakdown'].items():
        st.write(f"  {phase}: ${amount:,.2f}")
    st.write(f"Return on Investment (ROI): {roi:.2f}%")

if __name__ == "__main__":
    main()
