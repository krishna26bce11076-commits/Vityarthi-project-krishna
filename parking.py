"""Core logic for the Vehicle Parking Management System.

All database work lives here. Functions take an open SQLite connection and
return plain data (dicts / lists) or raise ParkingError, so the same code can
be used by the CLI (main.py) and by the unit tests.
"""

import math
import sqlite3
from datetime import datetime

DB_NAME = "parking.db"
TOTAL_SLOTS = 20
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
RATES = {"Bike": 10, "Car": 20, "Other": 30}  # Rs. per hour


class ParkingError(Exception):
    """Base class for all expected parking errors."""


class InvalidInput(ParkingError):
    pass


class VehicleAlreadyParked(ParkingError):
    pass


class VehicleNotFound(ParkingError):
    pass


class ParkingFull(ParkingError):
    pass


# --------------------------------------------------------------------------
# Database setup
# --------------------------------------------------------------------------
def connect(db_path=DB_NAME):
    """Open a database connection and make sure tables and slots exist."""
    conn = sqlite3.connect(db_path)
    init_db(conn)
    return conn


def init_db(conn):
    """Create tables (if missing) and the parking slots."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS parking_slots (
            slot_number    INTEGER PRIMARY KEY,
            vehicle_number TEXT,
            occupied       INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT UNIQUE,
            owner_name     TEXT,
            vehicle_type   TEXT,
            slot_number    INTEGER,
            entry_time     TEXT
        )
    """)
    for slot in range(1, TOTAL_SLOTS + 1):
        conn.execute(
            "INSERT OR IGNORE INTO parking_slots "
            "(slot_number, vehicle_number, occupied) VALUES (?, ?, ?)",
            (slot, None, 0),
        )
    conn.commit()


# --------------------------------------------------------------------------
# Operations
# --------------------------------------------------------------------------
def find_available_slot(conn):
    """Return the lowest free slot number, or None if parking is full."""
    row = conn.execute(
        "SELECT slot_number FROM parking_slots "
        "WHERE occupied = 0 ORDER BY slot_number LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def park_vehicle(conn, vehicle_number, owner_name, vehicle_type, entry_time=None):
    """Park a vehicle in the first free slot and return its record."""
    vehicle_number = vehicle_number.strip().upper()
    owner_name = owner_name.strip()

    if not vehicle_number:
        raise InvalidInput("Vehicle number cannot be empty.")
    if vehicle_type not in RATES:
        raise InvalidInput("Invalid vehicle type.")

    if conn.execute(
        "SELECT 1 FROM vehicles WHERE vehicle_number = ?", (vehicle_number,)
    ).fetchone():
        raise VehicleAlreadyParked("This vehicle is already parked.")

    slot = find_available_slot(conn)
    if slot is None:
        raise ParkingFull("Sorry! Parking is full.")

    entry_time_string = (entry_time or datetime.now()).strftime(TIME_FORMAT)

    with conn:  # one transaction: both tables change together or not at all
        conn.execute(
            "INSERT INTO vehicles "
            "(vehicle_number, owner_name, vehicle_type, slot_number, entry_time) "
            "VALUES (?, ?, ?, ?, ?)",
            (vehicle_number, owner_name, vehicle_type, slot, entry_time_string),
        )
        conn.execute(
            "UPDATE parking_slots SET vehicle_number = ?, occupied = 1 "
            "WHERE slot_number = ?",
            (vehicle_number, slot),
        )

    return {
        "vehicle_number": vehicle_number,
        "owner_name": owner_name,
        "vehicle_type": vehicle_type,
        "slot_number": slot,
        "entry_time": entry_time_string,
    }


def calculate_fee(vehicle_type, hours):
    """Fee = rate x hours, partial hours rounded up, minimum one hour."""
    billed_hours = max(1, math.ceil(hours))
    return billed_hours * RATES.get(vehicle_type, RATES["Other"])


def search_vehicle(conn, vehicle_number):
    """Return the record of a parked vehicle; raise VehicleNotFound if absent."""
    vehicle_number = vehicle_number.strip().upper()
    row = conn.execute(
        "SELECT vehicle_number, owner_name, vehicle_type, slot_number, entry_time "
        "FROM vehicles WHERE vehicle_number = ?",
        (vehicle_number,),
    ).fetchone()
    if row is None:
        raise VehicleNotFound("Vehicle not found.")
    keys = ("vehicle_number", "owner_name", "vehicle_type", "slot_number", "entry_time")
    return dict(zip(keys, row))


def remove_vehicle(conn, vehicle_number, exit_time=None):
    """Bill the vehicle, free its slot and return the bill as a dict."""
    vehicle = search_vehicle(conn, vehicle_number)

    entry_time = datetime.strptime(vehicle["entry_time"], TIME_FORMAT)
    exit_time = exit_time or datetime.now()
    hours = (exit_time - entry_time).total_seconds() / 3600
    fee = calculate_fee(vehicle["vehicle_type"], hours)

    with conn:
        conn.execute(
            "UPDATE parking_slots SET vehicle_number = NULL, occupied = 0 "
            "WHERE slot_number = ?",
            (vehicle["slot_number"],),
        )
        conn.execute(
            "DELETE FROM vehicles WHERE vehicle_number = ?",
            (vehicle["vehicle_number"],),
        )

    return {**vehicle, "exit_time": exit_time, "hours": hours, "fee": fee}


def get_parked_vehicles(conn):
    """Return all parked vehicles ordered by slot number."""
    rows = conn.execute(
        "SELECT vehicle_number, owner_name, vehicle_type, slot_number, entry_time "
        "FROM vehicles ORDER BY slot_number"
    ).fetchall()
    keys = ("vehicle_number", "owner_name", "vehicle_type", "slot_number", "entry_time")
    return [dict(zip(keys, row)) for row in rows]


def get_slots(conn):
    """Return (slot_number, vehicle_number, occupied) for every slot."""
    return conn.execute(
        "SELECT slot_number, vehicle_number, occupied "
        "FROM parking_slots ORDER BY slot_number"
    ).fetchall()


def get_statistics(conn):
    """Return total / occupied / available slots and the occupancy rate."""
    occupied = conn.execute(
        "SELECT COUNT(*) FROM parking_slots WHERE occupied = 1"
    ).fetchone()[0]
    available = conn.execute(
        "SELECT COUNT(*) FROM parking_slots WHERE occupied = 0"
    ).fetchone()[0]
    total = occupied + available
    rate = round(occupied / total * 100, 2) if total else 0.0
    return {
        "total": total,
        "occupied": occupied,
        "available": available,
        "occupancy_rate": rate,
    }
