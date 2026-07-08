"""Synthetic vehicle and driver data generator for fleet-ops-copilot."""

import csv
import random
from pathlib import Path

from faker import Faker
from pydantic import BaseModel

SEED = 42
NUM_VEHICLES = 500
NUM_DRIVERS = 50

CSV_DIR = Path(__file__).resolve().parents[2] / "data" / "csv"
VEHICLES_CSV_PATH = CSV_DIR / "vehicles.csv"
DRIVERS_CSV_PATH = CSV_DIR / "drivers.csv"

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
    driver_id: str


class Driver(BaseModel):
    id: str
    name: str
    license_number: str
    license_state: str
    hire_date: str
    safety_score: float
    violations_90d: int
    phone: str
    email: str


def generate_drivers(count: int, faker: Faker) -> list[Driver]:
    drivers: list[Driver] = []
    for i in range(1, count + 1):
        safety_score = round(random.uniform(40.0, 100.0), 1)
        # Lower safety scores skew toward more recent violations; clamped at 0.
        violations_90d = max(0, round(random.gauss((100 - safety_score) / 20, 1)))
        driver = Driver(
            id=f"DRV-{i:04d}",
            name=faker.name(),
            license_number=faker.bothify(text="??#######").upper(),
            license_state=faker.state_abbr(),
            hire_date=faker.date_between(start_date="-8y", end_date="today").isoformat(),
            safety_score=safety_score,
            violations_90d=violations_90d,
            phone=faker.phone_number(),
            email=faker.email(),
        )
        drivers.append(driver)
    return drivers


def generate_vehicles(count: int, faker: Faker, drivers: list[Driver]) -> list[Vehicle]:
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
            driver_id=random.choice(drivers).id,
        )
        vehicles.append(vehicle)
    return vehicles


def write_csv(records: list[BaseModel], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(type(records[0]).model_fields.keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.model_dump())


if __name__ == "__main__":
    random.seed(SEED)
    fake = Faker()
    Faker.seed(SEED)

    drivers = generate_drivers(NUM_DRIVERS, fake)
    write_csv(drivers, DRIVERS_CSV_PATH)
    print(f"Wrote {len(drivers)} drivers to {DRIVERS_CSV_PATH}")

    vehicles = generate_vehicles(NUM_VEHICLES, fake, drivers)
    write_csv(vehicles, VEHICLES_CSV_PATH)
    print(f"Wrote {len(vehicles)} vehicles to {VEHICLES_CSV_PATH}")
