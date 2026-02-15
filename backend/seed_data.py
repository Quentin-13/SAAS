"""Seed script to populate database with demo data."""
import uuid
import random
from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models.user import User, Organization
from app.models.site import Site, Zone
from app.models.device import Device
from app.models.energy import EnergyReading, EnergyForecast
from app.models.action import AutopilotAction
from app.models.subscription import Subscription
from app.utils.security import get_password_hash


def seed():
    """Create demo data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(User).first():
            # Ensure demo user password is valid and has admin role
            demo_user = db.query(User).filter(User.email == "demo@energy-autopilot.fr").first()
            if demo_user:
                demo_user.hashed_password = get_password_hash("demo1234")
                demo_user.is_superuser = True
                if hasattr(User, "role"):
                    demo_user.role = "admin"

            # Ensure admin user exists
            admin_user = db.query(User).filter(User.email == "admin@energy-autopilot.fr").first()
            if not admin_user:
                admin_org = db.query(Organization).first()
                admin_user = User(
                    id=str(uuid.uuid4()),
                    email="admin@energy-autopilot.fr",
                    hashed_password=get_password_hash("admin123"),
                    full_name="Admin Energy",
                    is_active=True,
                    is_superuser=True,
                    organization_id=admin_org.id if admin_org else None,
                )
                if hasattr(User, "role"):
                    admin_user.role = "admin"
                db.add(admin_user)
                print("Admin user created: admin@energy-autopilot.fr (password: admin123)")
            else:
                admin_user.hashed_password = get_password_hash("admin123")
                admin_user.is_superuser = True
                if hasattr(User, "role"):
                    admin_user.role = "admin"
                print("Admin user password refreshed.")

            db.commit()
            print("Database already seeded. Passwords refreshed.")
            return

        # Organization
        org = Organization(
            id=str(uuid.uuid4()),
            name="Demo Entreprise SAS",
            subscription_tier="pro",
            subscription_status="active",
        )
        db.add(org)
        db.flush()

        # User (demo user is also admin so /admin auto-login works)
        user = User(
            id=str(uuid.uuid4()),
            email="demo@energy-autopilot.fr",
            hashed_password=get_password_hash("demo1234"),
            full_name="Jean Dupont",
            phone="+33 6 12 34 56 78",
            is_active=True,
            is_superuser=True,
            organization_id=org.id,
        )
        if hasattr(User, "role"):
            user.role = "admin"
        db.add(user)
        db.flush()

        # Admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            email="admin@energy-autopilot.fr",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin Energy",
            is_active=True,
            is_superuser=True,
            organization_id=org.id,
        )
        if hasattr(User, "role"):
            admin_user.role = "admin"
        db.add(admin_user)
        db.flush()

        # Subscription
        sub = Subscription(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            plan="pro",
            status="active",
            monthly_price_eur=200.0,
        )
        db.add(sub)

        # Sites
        sites_data = [
            {
                "name": "Bureau Paris 11e",
                "address": "42 Rue de la Roquette",
                "postal_code": "75011",
                "city": "Paris",
                "latitude": 48.855,
                "longitude": 2.376,
                "surface_area": 850,
                "building_type": "office",
                "autopilot_enabled": True,
            },
            {
                "name": "Agence Lyon Part-Dieu",
                "address": "15 Boulevard Vivier Merle",
                "postal_code": "69003",
                "city": "Lyon",
                "latitude": 45.760,
                "longitude": 4.859,
                "surface_area": 420,
                "building_type": "office",
                "autopilot_enabled": True,
            },
            {
                "name": "Boutique Bordeaux",
                "address": "8 Rue Sainte-Catherine",
                "postal_code": "33000",
                "city": "Bordeaux",
                "latitude": 44.837,
                "longitude": -0.573,
                "surface_area": 180,
                "building_type": "retail",
                "autopilot_enabled": False,
            },
        ]

        sites = []
        for s_data in sites_data:
            site = Site(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                organization_id=org.id,
                **s_data,
            )
            db.add(site)
            sites.append(site)
        db.flush()

        # Zones for first site
        zones_data = [
            {"name": "Open Space", "zone_type": "office", "surface_area": 400, "target_temp_min": 20.0, "target_temp_max": 22.0},
            {"name": "Salle de Réunion A", "zone_type": "meeting_room", "surface_area": 50, "target_temp_min": 19.0, "target_temp_max": 23.0},
            {"name": "Accueil", "zone_type": "common_area", "surface_area": 80, "target_temp_min": 19.0, "target_temp_max": 22.0},
        ]

        zones = []
        for z_data in zones_data:
            zone = Zone(
                id=str(uuid.uuid4()),
                site_id=sites[0].id,
                occupancy_schedule={
                    "monday": [{"start": "08:00", "end": "19:00"}],
                    "tuesday": [{"start": "08:00", "end": "19:00"}],
                    "wednesday": [{"start": "08:00", "end": "19:00"}],
                    "thursday": [{"start": "08:00", "end": "19:00"}],
                    "friday": [{"start": "08:00", "end": "18:00"}],
                },
                **z_data,
            )
            db.add(zone)
            zones.append(zone)
        db.flush()

        # Devices
        devices_data = [
            {"name": "Thermostat Open Space", "device_type": "thermostat", "brand": "nest", "is_controllable": True, "zone": zones[0], "site": sites[0],
             "current_state": {"temperature": 21.2, "target_temperature": 21.0, "mode": "heat", "humidity": 45}},
            {"name": "Thermostat Réunion", "device_type": "thermostat", "brand": "netatmo", "is_controllable": True, "zone": zones[1], "site": sites[0],
             "current_state": {"temperature": 20.8, "target_temperature": 21.0, "mode": "heat", "humidity": 50}},
            {"name": "Compteur Linky Principal", "device_type": "meter", "brand": "linky", "is_controllable": False, "zone": None, "site": sites[0],
             "current_state": {"power_kw": 12.5, "daily_kwh": 85.3}},
            {"name": "Thermostat Lyon", "device_type": "thermostat", "brand": "nest", "is_controllable": True, "zone": None, "site": sites[1],
             "current_state": {"temperature": 20.5, "target_temperature": 21.0, "mode": "heat", "humidity": 48}},
        ]

        devices = []
        for d_data in devices_data:
            zone = d_data.pop("zone")
            site = d_data.pop("site")
            device = Device(
                id=str(uuid.uuid4()),
                site_id=site.id,
                zone_id=zone.id if zone else None,
                external_id=f"ext-{uuid.uuid4().hex[:8]}",
                is_active=True,
                capabilities={"heating": True, "cooling": False, "modes": ["heat", "eco", "off"]},
                **d_data,
            )
            db.add(device)
            devices.append(device)
        db.flush()

        # Energy Readings (last 30 days, every 15 min for meter device)
        now = datetime.utcnow()
        meter_device = devices[2]  # Linky meter
        readings = []
        for day_offset in range(30, 0, -1):
            for hour in range(24):
                for minute in [0, 15, 30, 45]:
                    t = now - timedelta(days=day_offset, hours=23 - hour, minutes=59 - minute)
                    weekday = t.weekday()
                    is_weekend = weekday >= 5
                    is_business_hours = 8 <= hour <= 19 and not is_weekend

                    # Base power pattern
                    if is_business_hours:
                        base_power = random.gauss(8, 1.5)  # 8kW avg during business
                    elif is_weekend:
                        base_power = random.gauss(2, 0.5)  # 2kW weekends
                    else:
                        base_power = random.gauss(3, 0.8)  # 3kW nights

                    base_power = max(0.5, base_power)

                    # Tariff
                    if 8 <= hour <= 13 or 17 <= hour <= 20:
                        tariff = "peak"
                        cost_per_kwh = 0.27
                    elif 22 <= hour or hour <= 6:
                        tariff = "super_off_peak"
                        cost_per_kwh = 0.12
                    else:
                        tariff = "off_peak"
                        cost_per_kwh = 0.147

                    energy_kwh = base_power * 0.25  # 15-min interval
                    cost = energy_kwh * cost_per_kwh

                    readings.append(EnergyReading(
                        time=t,
                        device_id=meter_device.id,
                        power_kw=round(base_power, 2),
                        energy_kwh=round(energy_kwh, 3),
                        cost_eur=round(cost, 4),
                        tariff_type=tariff,
                        outdoor_temp=round(random.gauss(8, 4), 1),
                        is_occupied=is_business_hours,
                    ))

        db.bulk_save_objects(readings)

        # Autopilot Actions (last 7 days)
        action_types = ["temperature_adjustment", "mode_change", "schedule_override"]
        reasons = [
            "Pic tarifaire détecté, réduction température de 0.5°C",
            "Zone inoccupée, passage en mode éco",
            "Soleil prévu, compensation gain solaire",
            "Pré-chauffage avant arrivée occupants",
            "Nuit : passage en mode réduit 16°C",
        ]

        actions = []
        for day_offset in range(7, 0, -1):
            num_actions = random.randint(2, 6)
            for _ in range(num_actions):
                hour = random.choice([6, 7, 8, 12, 13, 17, 18, 19, 20])
                t = now - timedelta(days=day_offset, hours=random.randint(0, 23))
                action = AutopilotAction(
                    id=str(uuid.uuid4()),
                    site_id=sites[0].id,
                    device_id=random.choice(devices[:2]).id,
                    action_type=random.choice(action_types),
                    action_params={
                        "previous_temp": round(random.uniform(20, 22), 1),
                        "new_temp": round(random.uniform(19, 21), 1),
                    },
                    reasoning=random.choice(reasons),
                    predicted_savings_eur=round(random.uniform(0.1, 2.5), 2),
                    predicted_savings_kwh=round(random.uniform(0.5, 8), 2),
                    confidence_score=round(random.uniform(0.7, 0.95), 2),
                    status="executed",
                    executed_at=t,
                    comfort_impact=random.choice(["none", "minimal"]),
                    created_at=t,
                )
                actions.append(action)

        db.bulk_save_objects(actions)

        db.commit()
        print(f"Seed complete!")
        print(f"  - 1 organization: {org.name}")
        print(f"  - 1 user: {user.email} (password: demo1234)")
        print(f"  - {len(sites)} sites")
        print(f"  - {len(zones)} zones")
        print(f"  - {len(devices)} devices")
        print(f"  - {len(readings)} energy readings (30 days)")
        print(f"  - {len(actions)} autopilot actions (7 days)")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
