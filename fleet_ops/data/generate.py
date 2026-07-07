"""Synthetic vehicle data generator for fleet-ops-copilot."""

import csv
import random
from pathlib import Path

from faker import Faker
from pydantic import BaseModel

SEED = 42
NUM_VEHICLES = 500

CSV_DIR = Path(__file__).resolve().parents[2] / "data" / "csv"
VEHICLES_CSV_PATH = CSV_DIR / "vehicles.csv"

MAKES_MODELS: dict[str, list[str]] = {
    "Ford": ["F-150", "Transit", "E-Series", "Explorer"],
    "Chevrolet": ["Silverado", "Express", "Equinox", "Tahoe"],
    "Freightliner": ["Cascadia", "M2 106", "Sprinter"],
    "RAM": ["1500", "2500", "ProMaster"],
    "Toyota": ["Tacoma", "Tundra", "Camry", "RAV4"],
    "Volvo": ["VNL", "VNR"],
    "Kenworth": ["T680", "T880"],
}

FUEL_TYPES = ["gasoline", "diesel", "electric", "hybrid"]
STATUSES = ["active", "maintenance", "out_of_service", "idle"]


class Vehicle(BaseModel):
    id: str
    vin: str
    make: str
    model: str
    year: int
    license_plate: str
    state: str
    fuel_type: str
    odometer_miles: int
    status: str


def generate_vehicles(count: int, faker: Faker) -> list[Vehicle]:
    vehicles: list[Vehicle] = []
    for i in range(1, count + 1):
        make = random.choice(list(MAKES_MODELS.keys()))
        model = random.choice(MAKES_MODELS[make])
        vehicle = Vehicle(
            id=f"VEH-{i:05d}",
            vin=faker.vin(),
            make=make,
            model=model,
            year=random.randint(2015, 2026),
            license_plate=faker.license_plate(),
            state=faker.state_abbr(),
            fuel_type=random.choice(FUEL_TYPES),
            odometer_miles=random.randint(500, 250_000),
            status=random.choice(STATUSES),
        )
        vehicles.append(vehicle)
    return vehicles


def write_vehicles_csv(vehicles: list[Vehicle], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(Vehicle.model_fields.keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for vehicle in vehicles:
            writer.writerow(vehicle.model_dump())


if __name__ == "__main__":
    random.seed(SEED)
    fake = Faker()
    Faker.seed(SEED)

    vehicles = generate_vehicles(NUM_VEHICLES, fake)
    write_vehicles_csv(vehicles, VEHICLES_CSV_PATH)
    print(f"Wrote {len(vehicles)} vehicles to {VEHICLES_CSV_PATH}")
