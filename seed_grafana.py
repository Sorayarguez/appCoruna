#!/usr/bin/env python3
"""Seed CrateDB with synthetic time-series data derived from the existing URBS zone model."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import sin, pi
from time import sleep
import os
import random
import requests

from seed_data import ZONES


CRATEDB_URL = os.environ.get("CRATEDB_URL", "http://localhost:4200").rstrip("/")
SQL_URL = f"{CRATEDB_URL}/_sql"


def quote(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    if hasattr(value, "isoformat"):
        return f"'{value.isoformat()}'"
    text = str(value).replace("'", "''")
    return f"'{text}'"


def sql(stmt: str) -> dict:
    response = requests.post(SQL_URL, json={"stmt": stmt}, timeout=15)
    response.raise_for_status()
    return response.json() if response.content else {}


def ensure_ready(retries: int = 60) -> None:
    last_error = None
    for _ in range(retries):
        try:
            sql("SELECT 1")
            return
        except Exception as exc:
            last_error = exc
            sleep(2)
    raise RuntimeError(f"CrateDB not ready after retries: {last_error}")


def peak_factor(hour_offset: int) -> float:
    hour = (datetime.now(timezone.utc).hour + hour_offset) % 24
    if 7 <= hour <= 9 or 17 <= hour <= 20:
        return 1.25
    if 0 <= hour <= 5:
        return 0.7
    return 0.95


def build_rows() -> tuple[list[str], list[str]]:
    impact_rows: list[str] = []
    flow_rows: list[str] = []
    base_time = datetime.now(timezone.utc) - timedelta(hours=5)

    for hour_offset in range(6):
        timestamp = base_time + timedelta(hours=hour_offset)
        factor = peak_factor(hour_offset)
        wave = 1 + 0.05 * sin((hour_offset / 6) * pi)

        for zone_index, zone in enumerate(ZONES):
            traffic = round(zone["base_traffic"] * factor * wave * random.uniform(0.92, 1.08), 2)
            no2 = round(zone["base_no2"] * factor * wave * random.uniform(0.9, 1.12), 2)
            pm25 = round(zone["base_pm25"] * factor * wave * random.uniform(0.9, 1.1), 2)
            pm10 = round(pm25 * random.uniform(1.55, 1.95), 2)
            co2 = round(no2 * random.uniform(3.6, 4.8), 2)
            noise = round(zone["base_noise"] * factor * random.uniform(0.94, 1.06), 2)
            speed = round(max(8, 58 - traffic / 32 + random.uniform(-3.5, 3.5)), 1)
            occupancy = round(min(98, traffic / 11.5 + random.uniform(-4, 4)), 1)
            aqi = round(no2 * 2.0 + pm25 * 1.45, 1)
            green_score = round(max(0, min(100, 100 - (no2 * 0.36 + pm25 * 0.28 + noise * 0.11 + traffic / 12))), 1)

            entity_id = zone["id"]
            time_literal = quote(timestamp)
            name_literal = quote(zone["name"])
            id_literal = quote(entity_id)

            flow_rows.append(
                "(" + ", ".join([
                    time_literal,
                    id_literal,
                    name_literal,
                    quote(zone["lon"]),
                    quote(zone["lat"]),
                    quote(traffic),
                    quote(speed),
                    quote(occupancy),
                ]) + ")"
            )
            impact_rows.append(
                "(" + ", ".join([
                    time_literal,
                    id_literal,
                    name_literal,
                    quote(zone["lon"]),
                    quote(zone["lat"]),
                    quote(no2),
                    quote(pm25),
                    quote(pm10),
                    quote(co2),
                    quote(noise),
                    quote(aqi),
                    quote(green_score),
                ]) + ")"
            )

    return impact_rows, flow_rows


def add_alert_rows(impact_rows: list[str]) -> None:
    """Append a few high-NO2 alert rows to ensure dashboards show active alerts."""
    now = datetime.now(timezone.utc)
    alert_no2 = 120.0
    # pick a couple of zones likely to be monitored
    alert_zones = [z for z in ZONES if z["id"] in ("cuatroCaminos", "asXubias", "centro")]
    for zone in alert_zones:
        time_literal = quote(now)
        id_literal = quote(zone["id"])
        name_literal = quote(zone["name"])
        impact_rows.append(
            "(" + ", ".join([
                time_literal,
                id_literal,
                name_literal,
                quote(zone["lon"]),
                quote(zone["lat"]),
                quote(alert_no2),
                quote(45.0),
                quote(60.0),
                quote(alert_no2 * 3.5),
                quote(85.0),
                quote(250.0),
                quote(5.0),
            ]) + ")"
        )


def main() -> None:
    ensure_ready()

    sql("DROP TABLE IF EXISTS ettrafficenvironmentimpact")
    sql("DROP TABLE IF EXISTS ettrafficflowobserved")

    sql(
        "CREATE TABLE ettrafficenvironmentimpact ("
        "time_index TIMESTAMP WITH TIME ZONE, "
        "entity_id TEXT, "
        "zone_name TEXT, "
        "longitude DOUBLE PRECISION, "
        "latitude DOUBLE PRECISION, "
        "NO2Concentration DOUBLE PRECISION, "
        "PM25Concentration DOUBLE PRECISION, "
        "PM10Concentration DOUBLE PRECISION, "
        "CO2Concentration DOUBLE PRECISION, "
        "noiseLevel DOUBLE PRECISION, "
        "aqi DOUBLE PRECISION, "
        "greenScore DOUBLE PRECISION"
        ")"
    )
    sql(
        "CREATE TABLE ettrafficflowobserved ("
        "time_index TIMESTAMP WITH TIME ZONE, "
        "entity_id TEXT, "
        "zone_name TEXT, "
        "longitude DOUBLE PRECISION, "
        "latitude DOUBLE PRECISION, "
        "intensity DOUBLE PRECISION, "
        "averageVehicleSpeed DOUBLE PRECISION, "
        "occupancy DOUBLE PRECISION"
        ")"
    )

    impact_rows, flow_rows = build_rows()
    # ensure a few explicit alert rows exist for dashboards
    add_alert_rows(impact_rows)

    sql(
        "INSERT INTO ettrafficenvironmentimpact ("
        "time_index, entity_id, zone_name, longitude, latitude, NO2Concentration, PM25Concentration, "
        "PM10Concentration, CO2Concentration, noiseLevel, aqi, greenScore"
        ") VALUES " + ", ".join(impact_rows)
    )
    sql(
        "INSERT INTO ettrafficflowobserved ("
        "time_index, entity_id, zone_name, longitude, latitude, intensity, averageVehicleSpeed, occupancy"
        ") VALUES " + ", ".join(flow_rows)
    )

    print(f"Seeded CrateDB with {len(impact_rows)} impact rows and {len(flow_rows)} traffic rows.")


if __name__ == "__main__":
    main()