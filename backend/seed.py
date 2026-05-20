"""Seed script to populate the database with demo data."""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from app.core.database import async_session_factory, engine
from app.core.security import generate_api_key, hash_password
from app.models import Base
from app.models.api_key import ApiKey
from app.models.dashboard import Dashboard, Widget, WidgetType
from app.models.data_source import DataSource, DataSourceType
from app.models.event import Event
from app.models.membership import Membership, Role
from app.models.organization import Organization
from app.models.user import User


async def seed():
    # Create tables directly (for quick dev setup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # --- Organization ---
        org = Organization(name="Demo Corp", slug="demo-corp")
        db.add(org)
        await db.flush()

        # --- Users ---
        owner = User(email="owner@demo.com", hashed_password=hash_password("password123"), full_name="Alice Owner")
        analyst = User(email="analyst@demo.com", hashed_password=hash_password("password123"), full_name="Bob Analyst")
        viewer = User(email="viewer@demo.com", hashed_password=hash_password("password123"), full_name="Carol Viewer")
        db.add_all([owner, analyst, viewer])
        await db.flush()

        # --- Memberships ---
        db.add_all([
            Membership(user_id=owner.id, organization_id=org.id, role=Role.OWNER),
            Membership(user_id=analyst.id, organization_id=org.id, role=Role.ANALYST),
            Membership(user_id=viewer.id, organization_id=org.id, role=Role.VIEWER),
        ])

        # --- API Key ---
        raw_key, key_hash = generate_api_key()
        api_key = ApiKey(
            organization_id=org.id, name="Default Key", key_prefix=raw_key[:8],
            key_hash=key_hash, created_by=owner.id
        )
        db.add(api_key)

        # --- Data Sources ---
        web_source = DataSource(
            organization_id=org.id, name="Web App", source_type=DataSourceType.API,
            config={"app": "web"}, created_by=owner.id
        )
        mobile_source = DataSource(
            organization_id=org.id, name="Mobile App", source_type=DataSourceType.API,
            config={"app": "mobile"}, created_by=owner.id
        )
        db.add_all([web_source, mobile_source])
        await db.flush()

        # --- Events (last 30 days) ---
        event_names = ["page_view", "button_click", "signup", "purchase", "logout", "error", "api_call"]
        pages = ["/home", "/pricing", "/docs", "/dashboard", "/settings", "/login"]
        now = datetime.now(timezone.utc)
        events = []
        for day_offset in range(30):
            day = now - timedelta(days=day_offset)
            count = random.randint(50, 200)
            for _ in range(count):
                evt_name = random.choice(event_names)
                source = random.choice([web_source, mobile_source])
                ts = day + timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59),
                )
                props = {"page": random.choice(pages)}
                if evt_name == "purchase":
                    props["amount"] = round(random.uniform(9.99, 299.99), 2)
                if evt_name == "error":
                    props["code"] = random.choice([400, 404, 500, 502, 503])

                events.append(Event(
                    organization_id=org.id,
                    data_source_id=source.id,
                    event_name=evt_name,
                    properties=props,
                    timestamp=ts,
                ))

        db.add_all(events)

        # --- Dashboard ---
        dashboard = Dashboard(
            organization_id=org.id, name="Overview Dashboard",
            description="Main analytics overview", created_by=owner.id
        )
        db.add(dashboard)
        await db.flush()

        # --- Widgets ---
        db.add_all([
            Widget(
                dashboard_id=dashboard.id, name="Events Over Time",
                widget_type=WidgetType.LINE_CHART,
                config={"event_name": None, "interval": "day"},
                position={"x": 0, "y": 0, "w": 8, "h": 4},
            ),
            Widget(
                dashboard_id=dashboard.id, name="Top Events",
                widget_type=WidgetType.BAR_CHART,
                config={"limit": 7},
                position={"x": 8, "y": 0, "w": 4, "h": 4},
            ),
            Widget(
                dashboard_id=dashboard.id, name="Event Distribution",
                widget_type=WidgetType.PIE_CHART,
                config={"limit": 5},
                position={"x": 0, "y": 4, "w": 6, "h": 4},
            ),
            Widget(
                dashboard_id=dashboard.id, name="Total Events",
                widget_type=WidgetType.KPI_CARD,
                config={"event_name": None},
                position={"x": 6, "y": 4, "w": 3, "h": 2},
            ),
            Widget(
                dashboard_id=dashboard.id, name="Total Signups",
                widget_type=WidgetType.KPI_CARD,
                config={"event_name": "signup"},
                position={"x": 9, "y": 4, "w": 3, "h": 2},
            ),
        ])

        await db.commit()

        print("=" * 60)
        print("SEED DATA CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"Organization: {org.name} (ID: {org.id})")
        print(f"Owner:   owner@demo.com / password123")
        print(f"Analyst: analyst@demo.com / password123")
        print(f"Viewer:  viewer@demo.com / password123")
        print(f"API Key: {raw_key}")
        print(f"Events:  {len(events)} events over 30 days")
        print(f"Dashboard: {dashboard.name} (ID: {dashboard.id})")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
