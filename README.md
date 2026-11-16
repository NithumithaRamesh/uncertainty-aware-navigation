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

## Recommendation logic

The comparison logic selects the route with the lowest estimated journey time
only. It reports uncertainty ranges and traffic-data freshness separately
instead of combining them into an unsupported reliability score.

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
