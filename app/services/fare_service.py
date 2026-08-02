from app.models import Bus, Route

BUS_TYPE_CHARGES = {
    "ac": 75.0,
    "non-ac": 25.0,
    "sleeper": 100.0,
    "semi-sleeper": 60.0,
}


def calculate_fare(route: Route, bus: Bus, discount: float = 0.0) -> dict:
    base_fare = route.base_fare
    distance_cost = route.total_distance * 0.5
    bus_type_charges = BUS_TYPE_CHARGES.get(bus.bus_type.lower(), 40.0)
    taxes = 0.05 * (base_fare + distance_cost + bus_type_charges)
    final_fare = max(base_fare + distance_cost + bus_type_charges + taxes - discount, 0)
    return {
        "base_fare": round(base_fare, 2),
        "distance_cost": round(distance_cost, 2),
        "bus_type_charges": round(bus_type_charges, 2),
        "taxes": round(taxes, 2),
        "discount": round(discount, 2),
        "final_fare": round(final_fare, 2),
    }
