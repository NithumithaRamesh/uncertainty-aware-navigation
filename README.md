# Uncertainty-Aware Navigation

An intelligent navigation recommendation prototype that communicates uncertainty
in route estimates to support informed user decisions.

## Milestone 1

This milestone establishes the Python project structure and implements traffic
data freshness assessment:

- `0–10` minutes: Recent
- Above `10–30` minutes: Moderately old
- Above `30` minutes: Outdated
- Missing traffic timestamp: Unavailable

The thresholds are provisional design assumptions. The freshness logic keeps
data age separate from travel-time uncertainty.

## Route model

Routes are represented with their identifier, display name, estimated journey
time, independent uncertainty value, and optional traffic-update timestamp.
The uncertainty helper reports the simulated lower and upper journey-time
bounds; these bounds are not statistically calibrated confidence intervals.

Dynamic OSRM routes do not include traffic-data timestamps. The prototype
therefore assigns deterministic illustrative ages to routes after retrieval
(for example, Route A is recent and Route B is outdated). These timestamps
support the freshness interaction and are not real traffic-data predictions.

## Recommendation logic

The comparison logic selects the route with the lowest estimated journey time
only. It reports uncertainty ranges and traffic-data freshness separately
instead of combining them into an unsupported reliability score.

## User flow

The interface is designed for a short navigation decision rather than a
questionnaire:

1. Enter an origin and destination.
2. Choose what matters most: fastest, predictable, most recent traffic, or
   balanced.
3. Scan the suggested route's journey estimate, possible arrival range, and
   traffic-data age.
4. Select **Use this route**. Additional explanation is available below the
   route cards.

The application does not claim that simulated uncertainty predicts actual
traffic or that it improves driver trust. It is a decision-support prototype
whose uncertainty and freshness values remain illustrative until validated with
real data.

## Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Run the prototype with:

```powershell
streamlit run app.py
```

Run the tests with:

```powershell
pytest
```
