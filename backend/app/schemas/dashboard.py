from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DashboardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class DashboardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class DashboardResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_public: bool
    share_token: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    widgets: list[WidgetResponse] = []

    model_config = {"from_attributes": True}


class DashboardListResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_public: bool
    created_at: datetime
    widget_count: int = 0

    model_config = {"from_attributes": True}


class WidgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    widget_type: str = Field(pattern="^(line_chart|bar_chart|pie_chart|kpi_card|table)$")
    config: dict = Field(default_factory=dict)
    position: dict = Field(default_factory=lambda: {"x": 0, "y": 0, "w": 6, "h": 4})


class WidgetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    widget_type: str | None = Field(default=None, pattern="^(line_chart|bar_chart|pie_chart|kpi_card|table)$")
    config: dict | None = None
    position: dict | None = None


class WidgetResponse(BaseModel):
    id: uuid.UUID
    dashboard_id: uuid.UUID
    name: str
    widget_type: str
    config: dict
    position: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WidgetLayoutUpdate(BaseModel):
    layouts: list[WidgetPositionUpdate]


class WidgetPositionUpdate(BaseModel):
    widget_id: uuid.UUID
    position: dict


class AggregationQuery(BaseModel):
    event_name: str | None = None
    data_source_id: uuid.UUID | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    group_by: str | None = None  # property key to group by
    interval: str = Field(default="day", pattern="^(hour|day|week|month)$")
    limit: int = Field(default=10, ge=1, le=1000)


class TimeSeriesPoint(BaseModel):
    timestamp: str
    value: float


class AggregationResponse(BaseModel):
    data: list[dict]
    total: int
