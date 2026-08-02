import json
import math
from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Bus, Route, Schedule
from app.routers.deps import require_admin
from app.schemas import BusUpsertRequest, RouteUpsertRequest, ScheduleCreateRequest

router = APIRouter(tags=["transport"])


def generate_seat_layout(total_seats: int) -> list[str]:
    columns = ["A", "B", "C", "D"]
    rows = math.ceil(total_seats / len(columns))
    seats = [f"{r}{c}" for r in range(1, rows + 1) for c in columns]
    return seats[:total_seats]


@router.post("/buses")
def create_bus(payload: BusUpsertRequest, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    if db.query(Bus).filter(Bus.registration_number == payload.registration_number).first():
        raise HTTPException(status_code=400, detail="Bus registration number already exists")
    bus = Bus(
        registration_number=payload.registration_number,
        operator_name=payload.operator_name,
        bus_type=payload.bus_type,
        total_seats=payload.total_seats,
        seat_layout=json.dumps(generate_seat_layout(payload.total_seats)),
        bus_status=payload.bus_status,
        amenities=json.dumps(payload.amenities),
    )
    db.add(bus)
    db.commit()
    db.refresh(bus)
    return {"success": True, "message": "Bus created", "data": {"bus_id": bus.id}}


@router.get("/buses")
def list_buses(db: Session = Depends(get_db)):
    buses = db.query(Bus).all()
    return {
        "success": True,
        "data": [
            {
                "bus_id": b.id,
                "registration_number": b.registration_number,
                "operator_name": b.operator_name,
                "bus_type": b.bus_type,
                "total_seats": b.total_seats,
                "seat_layout": json.loads(b.seat_layout),
                "bus_status": b.bus_status,
                "amenities": json.loads(b.amenities),
            }
            for b in buses
        ],
    }


@router.put("/buses/{bus_id}")
def update_bus(bus_id: int, payload: BusUpsertRequest, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    bus = db.get(Bus, bus_id)
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    bus.registration_number = payload.registration_number
    bus.operator_name = payload.operator_name
    bus.bus_type = payload.bus_type
    bus.total_seats = payload.total_seats
    bus.bus_status = payload.bus_status
    bus.amenities = json.dumps(payload.amenities)
    bus.seat_layout = json.dumps(generate_seat_layout(payload.total_seats))
    db.commit()
    return {"success": True, "message": "Bus updated"}


@router.delete("/buses/{bus_id}")
def delete_bus(bus_id: int, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    bus = db.get(Bus, bus_id)
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    db.delete(bus)
    db.commit()
    return {"success": True, "message": "Bus deleted"}


@router.post("/routes")
def create_route(payload: RouteUpsertRequest, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    route = Route(
        source_city=payload.source_city,
        destination_city=payload.destination_city,
        intermediate_stops=json.dumps(payload.intermediate_stops),
        total_distance=payload.total_distance,
        estimated_travel_time=payload.estimated_travel_time,
        base_fare=payload.base_fare,
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return {"success": True, "message": "Route created", "data": {"route_id": route.id}}


@router.get("/routes")
def list_routes(db: Session = Depends(get_db)):
    routes = db.query(Route).all()
    return {
        "success": True,
        "data": [
            {
                "route_id": r.id,
                "source_city": r.source_city,
                "destination_city": r.destination_city,
                "intermediate_stops": json.loads(r.intermediate_stops),
                "total_distance": r.total_distance,
                "estimated_travel_time": r.estimated_travel_time,
                "base_fare": r.base_fare,
            }
            for r in routes
        ],
    }


@router.put("/routes/{route_id}")
def update_route(route_id: int, payload: RouteUpsertRequest, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    route = db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    route.source_city = payload.source_city
    route.destination_city = payload.destination_city
    route.intermediate_stops = json.dumps(payload.intermediate_stops)
    route.total_distance = payload.total_distance
    route.estimated_travel_time = payload.estimated_travel_time
    route.base_fare = payload.base_fare
    db.commit()
    return {"success": True, "message": "Route updated"}


@router.post("/schedules")
def create_schedule(payload: ScheduleCreateRequest, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    bus = db.get(Bus, payload.bus_id)
    route = db.get(Route, payload.route_id)
    if not bus or not route:
        raise HTTPException(status_code=400, detail="Invalid bus or route")
    schedule = Schedule(
        bus_id=payload.bus_id,
        route_id=payload.route_id,
        departure_datetime=payload.departure_datetime,
        arrival_datetime=payload.arrival_datetime,
        available_seats=bus.total_seats,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return {"success": True, "message": "Schedule created", "data": {"schedule_id": schedule.id}}


@router.get("/schedules")
def list_schedules(db: Session = Depends(get_db)):
    schedules = db.query(Schedule).all()
    return {
        "success": True,
        "data": [
            {
                "schedule_id": s.id,
                "bus_id": s.bus_id,
                "route_id": s.route_id,
                "departure_datetime": s.departure_datetime,
                "arrival_datetime": s.arrival_datetime,
                "available_seats": s.available_seats,
                "booking_status": s.booking_status,
            }
            for s in schedules
        ],
    }


@router.get("/schedules/search")
def search_schedules(
    source: str,
    destination: str,
    journey_date: date,
    bus_type: str | None = None,
    departure_time: time | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(Schedule, Bus, Route)
        .join(Bus, Schedule.bus_id == Bus.id)
        .join(Route, Schedule.route_id == Route.id)
        .filter(Route.source_city == source, Route.destination_city == destination)
    )
    if bus_type:
        query = query.filter(Bus.bus_type == bus_type)
    results = []
    for schedule, bus, route in query.all():
        if schedule.departure_datetime.date() != journey_date:
            continue
        if departure_time and schedule.departure_datetime.time().hour != departure_time.hour:
            continue
        duration = schedule.arrival_datetime - schedule.departure_datetime
        fare = route.base_fare
        results.append(
            {
                "schedule_id": schedule.id,
                "bus_name": bus.operator_name,
                "available_seats": schedule.available_seats,
                "departure_time": schedule.departure_datetime,
                "arrival_time": schedule.arrival_datetime,
                "fare": fare,
                "journey_duration": str(duration),
            }
        )
    return {"success": True, "data": results}
