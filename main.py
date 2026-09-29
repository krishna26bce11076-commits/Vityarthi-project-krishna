"""Console interface for the Vehicle Parking Management System."""

import parking

VEHICLE_TYPES = {"1": "Bike", "2": "Car", "3": "Other"}
DISPLAY_TIME = "%d-%m-%Y %H:%M:%S"


def display_header():
    print("\n" + "=" * 50)
    print("      VEHICLE PARKING MANAGEMENT SYSTEM")
    print("=" * 50)


def park_vehicle_ui(conn):
    print("\n--- PARK VEHICLE ---")
    vehicle_number = input("Enter vehicle number: ")
    owner_name = input("Enter owner name: ")

    print("\nVehicle Types:")
    for key, name in VEHICLE_TYPES.items():
        print(f"{key}. {name}")
    vehicle_type = VEHICLE_TYPES.get(input("Select vehicle type: ").strip())

    try:
        v = parking.park_vehicle(conn, vehicle_number, owner_name, vehicle_type)
    except parking.ParkingError as error:
        print(error)
        return

    print("\nVehicle parked successfully!")
    print("Vehicle Number :", v["vehicle_number"])
    print("Owner Name     :", v["owner_name"])
    print("Vehicle Type   :", v["vehicle_type"])
    print("Parking Slot   :", v["slot_number"])
    print("Entry Time     :", v["entry_time"])


def remove_vehicle_ui(conn):
    print("\n--- REMOVE VEHICLE ---")
    try:
        bill = parking.remove_vehicle(conn, input("Enter vehicle number: "))
    except parking.ParkingError as error:
        print(error)
        return

    entry = parking.datetime.strptime(bill["entry_time"], parking.TIME_FORMAT)
    print("\n--- PARKING BILL ---")
    print("Vehicle Number :", bill["vehicle_number"])
    print("Owner Name     :", bill["owner_name"])
    print("Vehicle Type   :", bill["vehicle_type"])
    print("Parking Slot   :", bill["slot_number"])
    print("Entry Time     :", entry.strftime(DISPLAY_TIME))
    print("Exit Time      :", bill["exit_time"].strftime(DISPLAY_TIME))
    print("Duration       :", round(bill["hours"], 2), "hours")
    print("Parking Fee    : Rs.", bill["fee"])
    print("Vehicle removed successfully.")
    print("Parking slot is now available.")


def search_vehicle_ui(conn):
    print("\n--- SEARCH VEHICLE ---")
    try:
        v = parking.search_vehicle(conn, input("Enter vehicle number: "))
    except parking.ParkingError as error:
        print(error)
        return

    print("\nVehicle Found!")
    print("Vehicle Number :", v["vehicle_number"])
    print("Owner Name     :", v["owner_name"])
    print("Vehicle Type   :", v["vehicle_type"])
    print("Parking Slot   :", v["slot_number"])
    print("Entry Time     :", v["entry_time"])


def display_vehicles_ui(conn):
    print("\n--- PARKED VEHICLES ---")
    vehicles = parking.get_parked_vehicles(conn)
    if not vehicles:
        print("No vehicles are currently parked.")
        return

    print("-" * 75)
    print(f"{'Vehicle':<15}{'Owner':<20}{'Type':<10}{'Slot':<10}{'Entry Time':<20}")
    print("-" * 75)
    for v in vehicles:
        print(
            f"{v['vehicle_number']:<15}{v['owner_name']:<20}"
            f"{v['vehicle_type']:<10}{v['slot_number']:<10}{v['entry_time']:<20}"
        )
    print("-" * 75)


def display_slots_ui(conn):
    print("\n--- PARKING SLOTS ---")
    for slot_number, vehicle_number, occupied in parking.get_slots(conn):
        if occupied:
            print(f"Slot {slot_number:02d} : OCCUPIED - {vehicle_number}")
        else:
            print(f"Slot {slot_number:02d} : AVAILABLE")


def parking_statistics_ui(conn):
    print("\n--- PARKING STATISTICS ---")
    s = parking.get_statistics(conn)
    print("Total Slots     :", s["total"])
    print("Occupied Slots  :", s["occupied"])
    print("Available Slots :", s["available"])
    print("Occupancy Rate  :", s["occupancy_rate"], "%")


def main():
    conn = parking.connect()
    actions = {
        "1": park_vehicle_ui,
        "2": remove_vehicle_ui,
        "3": search_vehicle_ui,
        "4": display_vehicles_ui,
        "5": display_slots_ui,
        "6": parking_statistics_ui,
    }

    while True:
        display_header()
        print("1. Park Vehicle")
        print("2. Remove Vehicle")
        print("3. Search Vehicle")
        print("4. Display Parked Vehicles")
        print("5. Display Parking Slots")
        print("6. Parking Statistics")
        print("7. Exit")
        choice = input("\nEnter your choice: ").strip()

        if choice in actions:
            actions[choice](conn)
        elif choice == "7":
            print("\nThank you for using the system!")
            conn.close()
            break
        else:
            print("\nInvalid choice. Please enter 1 to 7.")


if __name__ == "__main__":
    main()
