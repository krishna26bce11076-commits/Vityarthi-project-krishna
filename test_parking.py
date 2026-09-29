import os
import sys
import sqlite3
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import parking  # noqa: E402


class ParkingTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        parking.init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_twenty_slots_created(self):
        self.assertEqual(parking.get_statistics(self.conn)["total"], 20)

    def test_first_free_slot_assigned(self):
        a = parking.park_vehicle(self.conn, "mp04ab1234", "Rahul", "Car")
        b = parking.park_vehicle(self.conn, "MP04AB9999", "Asha", "Bike")
        self.assertEqual((a["slot_number"], b["slot_number"]), (1, 2))
        self.assertEqual(a["vehicle_number"], "MP04AB1234")  # upper-cased

    def test_duplicate_vehicle_rejected(self):
        parking.park_vehicle(self.conn, "MP04AB1234", "Rahul", "Car")
        with self.assertRaises(parking.VehicleAlreadyParked):
            parking.park_vehicle(self.conn, "mp04ab1234", "Rahul", "Car")

    def test_invalid_input_rejected(self):
        with self.assertRaises(parking.InvalidInput):
            parking.park_vehicle(self.conn, "   ", "Rahul", "Car")
        with self.assertRaises(parking.InvalidInput):
            parking.park_vehicle(self.conn, "MP04AB1234", "Rahul", None)

    def test_parking_full(self):
        for i in range(20):
            parking.park_vehicle(self.conn, f"V{i}", "Owner", "Car")
        with self.assertRaises(parking.ParkingFull):
            parking.park_vehicle(self.conn, "EXTRA", "Owner", "Car")

    def test_fee_rates_and_rounding(self):
        self.assertEqual(parking.calculate_fee("Bike", 1), 10)
        self.assertEqual(parking.calculate_fee("Car", 2.2), 60)    # 3 h x 20
        self.assertEqual(parking.calculate_fee("Other", 0.1), 30)  # minimum 1 h

    def test_remove_bills_and_frees_slot(self):
        start = datetime(2026, 9, 19, 14, 30)
        parking.park_vehicle(self.conn, "MP04AB1234", "Rahul", "Car", start)
        bill = parking.remove_vehicle(
            self.conn, "MP04AB1234", start + timedelta(hours=2, minutes=12)
        )
        self.assertEqual(bill["fee"], 60)
        self.assertEqual(parking.get_statistics(self.conn)["occupied"], 0)
        with self.assertRaises(parking.VehicleNotFound):
            parking.search_vehicle(self.conn, "MP04AB1234")

    def test_freed_slot_is_reused(self):
        parking.park_vehicle(self.conn, "A", "x", "Car")
        parking.park_vehicle(self.conn, "B", "x", "Car")
        parking.remove_vehicle(self.conn, "A")
        c = parking.park_vehicle(self.conn, "C", "x", "Car")
        self.assertEqual(c["slot_number"], 1)

    def test_missing_vehicle(self):
        with self.assertRaises(parking.VehicleNotFound):
            parking.remove_vehicle(self.conn, "NOPE")

    def test_statistics(self):
        for i in range(4):
            parking.park_vehicle(self.conn, f"V{i}", "x", "Bike")
        s = parking.get_statistics(self.conn)
        self.assertEqual(
            (s["occupied"], s["available"], s["occupancy_rate"]), (4, 16, 20.0)
        )

    def test_parked_vehicles_in_slot_order(self):
        parking.park_vehicle(self.conn, "B", "x", "Car")
        parking.park_vehicle(self.conn, "A", "x", "Car")
        slots = [v["slot_number"] for v in parking.get_parked_vehicles(self.conn)]
        self.assertEqual(slots, sorted(slots))


if __name__ == "__main__":
    unittest.main()
