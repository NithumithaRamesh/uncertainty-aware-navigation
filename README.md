# Uncertainty-Aware Navigation

An interactive navigation decision-support prototype that communicates route uncertainty and traffic-data freshness to help users make informed journey decisions.

## Overview

Conventional navigation systems present estimated journey times and route recommendations, but users may not know how reliable the underlying information is.

**Uncertainty-Aware Navigation** explores how uncertainty can be communicated through an interactive navigation interface. Rather than presenting a route recommendation as unquestionably reliable, the system makes estimated journey times, uncertainty ranges and traffic-data freshness visible to users.

Users can compare alternative routes, explore different journey preferences and make their own informed route selections.

## Features

- **Route discovery:** Enter an origin and destination to retrieve alternative routes.
- **Journey estimates:** View estimated travel durations and route distances.
- **Uncertainty communication:** Display illustrative lower and upper journey-time bounds.
- **Traffic-data freshness:** Classify information as recent, moderately old, outdated or unavailable.
- **Preference-based recommendations:** Explore routes using fastest, predictable, most recent traffic or balanced preferences.
- **Recommendation explanations:** Understand the information behind the suggested route.
- **User-controlled selection:** Review alternatives and explicitly choose a route rather than automatically accepting a recommendation.

## How It Works

1. The user enters an origin and destination.
2. The application resolves the locations and retrieves alternative routes using the OSRM routing service.
3. Each route is presented with its estimated duration and distance.
4. The application displays illustrative uncertainty ranges and traffic-data freshness information.
5. The recommendation logic evaluates the available route information and presents a suggestion.
6. The user compares the alternatives, reviews the explanation and selects their preferred route.

### Uncertainty and Data Freshness

The prototype treats journey-time uncertainty and traffic-data freshness as separate dimensions.

- **Journey-time uncertainty:** Illustrative lower and upper journey-time bounds are displayed alongside the estimated duration. These are simulated values, not statistically calibrated confidence intervals.
- **Traffic-data freshness:** Information is classified using its timestamp:
  - 0–10 minutes: Recent
  - Above 10–30 minutes: Moderately old
  - Above 30 minutes: Outdated
  - Missing timestamp: Unavailable

The freshness thresholds are provisional design assumptions.

OSRM provides routing information but does not supply the traffic-update timestamps used by this prototype. Consequently, illustrative timestamps are assigned after route retrieval to demonstrate the freshness interaction.

The system does not combine uncertainty and freshness into an unsupported reliability score.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic and data processing |
| Streamlit | Interactive user interface |
| OSRM | Route retrieval and journey estimates |
| Pytest | Automated testing |

## Project Structure

```text
uncertainty-aware-navigation/
│
├── app.py
├── requirements.txt
│
├── data/
│
├── logic/
│
├── services/
│
├── simulation/
│
├── scripts/
│
└── tests/
```

- `app.py` – Main Streamlit application and interaction flow.
- `logic/` – Route comparison and recommendation logic.
- `services/` – External service integrations.
- `simulation/` – Simulated uncertainty and traffic-data information.
- `data/` – Project data and supporting resources.
- `scripts/` – Supporting development scripts.
- `tests/` – Automated tests.

## Getting Started

### Prerequisites

- Python 3.10 or later
- pip
- Internet connection for external routing requests

### Installation

Clone the repository:

```bash
git clone https://github.com/NithumithaRamesh/uncertainty-aware-navigation.git
cd uncertainty-aware-navigation
```

Create and activate a virtual environment:

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
streamlit run app.py
```

The application will be available at the local URL provided by Streamlit, usually `http://localhost:8501`.

### Run Tests

```bash
pytest
```
