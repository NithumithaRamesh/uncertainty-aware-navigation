"""Small manual smoke test for the Nominatim geocoding service."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.geocoding import search_cities


def main() -> None:
    city_name = " ".join(sys.argv[1:]) or "Birmingham"
    places = search_cities(city_name)
    if not places:
        print(f"No UK settlement found for {city_name!r}.")
        return

    for place in places:
        print(
            f"{place.name}: {place.latitude}, {place.longitude} "
            f"({place.display_name})"
        )


if __name__ == "__main__":
    main()
