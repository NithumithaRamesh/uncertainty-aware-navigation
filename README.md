# Uncertainty-Aware Navigation

An interactive navigation decision-support prototype that communicates route uncertainty and traffic-data freshness to help users make informed journey decisions.

## Overview

Conventional navigation systems present estimated journey times and route recommendations, but users may not know how reliable the underlying information is.

**Uncertainty-Aware Navigation** explores how uncertainty can be communicated through an interactive navigation interface. Rather than presenting a route recommendation as unquestionably reliable, the system makes estimated journey times, uncertainty ranges and traffic-data freshness visible to users.

Users can compare alternative routes, explore different journey preferences and make their own informed route selections.

## Project Status

| Part | Status | Where |
|---|---|---|
| City search with UK-only matches and a confirmation step for ambiguous names | Implemented | `services/geocoding.py`, `app.py` |
| Live alternative routes (duration, distance) | Implemented — OSRM public demo server | `services/routing.py` |
| Freshness classification (Recent ≤10 min, Moderately old ≤30, Outdated >30, Unavailable) | Implemented; thresholds are provisional assumptions | `logic/freshness.py` |
| Uncertainty range (estimate ± uncertainty) | Implemented calculation | `logic/uncertainty.py` |
| Priority-based suggestions: Fastest, Most predictable, Most recent traffic, Balanced (non-dominated shortlist) | Implemented | `logic/preference.py`, `logic/tradeoff.py` |
| Explicit route selection, "View details" disclosure | Implemented | `app.py` |
| Traffic-data timestamps | **Simulated**: fixed age per route ID (A 5, B 45, C 18, D 8, E 35 min) | `simulation/freshness_simulator.py` |
| Journey-time uncertainty | **Simulated**: fixed ± minutes per route ID (A 8, B 2, C 3, D 5, E 4), else a hash of the route ID, within 2–10 min | `simulation/uncertainty_simulator.py` |
| Live traffic data, learned uncertainty model | Planned | — |
| Remembering the user's priority, in-drive voice reroute prompt, "estimate only" baseline view with study logging | Planned | — |
| User study of trust and route choice | Not started | — |

The simulated values are deterministic so every run shows the same trade-off (Route A: fast but uncertain; Route B: predictable but older data). They are labelled in the interface and are not evidence about real traffic.

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
| Nominatim (OpenStreetMap) | Place search; UK only, up to 5 matches, 1 request per second, with a User-Agent header |

No API key is needed. Both services are public; an internet connection is required to run the app, but not to run the tests (network calls are mocked).

Undecided: where real traffic timestamps and uncertainty would come from (for example a commercial traffic API or historical journey-time data).

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

## Development Record

| Stage | Commits | What changed and why | How I checked it |
|---|---|---|---|
| 1. Freshness model | [03b1718](https://github.com/NithumithaRamesh/uncertainty-aware-navigation/commit/03b1718), [2bf0b1c](https://github.com/NithumithaRamesh/uncertainty-aware-navigation/commit/2bf0b1c) | Classified data age into four labels; a missing timestamp became "Unavailable" so one incomplete route does not block the others | `tests/test_freshness.py`: boundary cases at 10 and 30 min, missing, naive vs timezone-aware times |
| 2. Route model and comparison | [a9239cf](https://github.com/NithumithaRamesh/uncertainty-aware-navigation/commit/a9239cf), [f5f9c33](https://github.com/NithumithaRamesh/uncertainty-aware-navigation/commit/f5f9c33), [d7a7db2](https://github.com/NithumithaRamesh/uncertainty-aware-navigation/commit/d7a7db2) | Route validation, uncertainty range, fastest-route comparison that reports uncertainty and freshness separately (no combined score); rejected duplicate route IDs | `test_route.py`, `test_recommendation.py`, `test_uncertainty.py` |
| 3. First interface | [02772db](https://github.com/NithumithaRamesh/uncertainty-aware-navigation/commit/02772db), [940cb03](https://github.com/NithumithaRamesh/uncertainty-aware-navigation/commit/940cb03) | Streamlit page on five hard-coded sample routes; always recommended the fastest route | Displayed journey estimates, uncertainty and freshness labels, but did not yet support city input or user-controlled route selection |
| 4. Architecture change | [19a5491](https://github.com/NithumithaRamesh/uncertainty-aware-navigation/commit/19a5491) | Sample routes gave trade-offs that were too tidy, and a fastest-only suggestion ignored the reliability it displayed. Added Nominatim + OSRM; separated `simulation/` from `logic/` via an adapter so simulated values cannot pass as retrieved; added priorities and the Balanced shortlist | Mocked tests for routing, geocoding, adapter, simulators, preferences; `scripts/*_smoke.py` against the live services; manual Birmingham → Manchester run |
| 5. Interaction fixes | [6c54c80](https://github.com/NithumithaRamesh/uncertainty-aware-navigation/commit/6c54c80) | Added "Most recent traffic"; suggestion banner with its reason; range shown beside the estimate; "Use this route" buttons with the suggested route highlighted; uncertainty made independent of route duration | `test_uncertainty_simulator.py` (independence from duration); changed preferences, checked suggestion highlighting and uncertainty ranges, selected an alternative route, and opened "View details" |
| 6. Documentation | [0618999](https://github.com/NithumithaRamesh/uncertainty-aware-navigation/commit/0618999) and later | README, status and this record | — |

## Using AI

- **GitHub Copilot (VS Code/Copilot CLI)** helped develop the model foundation and implementation based on the design and requirements I provided. This included drafting and refining Python logic, application code and README sections. I reviewed the code against the project requirements, ran the tests, checked status labels and commit hashes, and corrected or removed unsupported suggestions. 
- **Claude (claude.ai)** helped prepare an initial structure for the A2 report, system diagram and interaction storyboards using the repository and lecture notes. I checked the resulting claims against the implementation and commit history, particularly the distinction between live routing and simulated freshness or uncertainty, and corrected wording before finalising it.

AI-assisted text was used as a starting point, not as evidence or a final authority. I am responsible for the design choices, implementation, report claims and references submitted.

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
