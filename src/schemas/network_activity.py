from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator
from src.models.network_activity import ActivityStatus


class NetworkActivityResponse(BaseModel):
    id: int
    activity_title: str
    activity_description: str | None = None
    average_traffic_mbps: int | None = None
    max_latency_ms: int | None = None
    preview_image_url: str
    preview_video_url: str
    status: ActivityStatus | str
    creator_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_owner: int = 0

    model_config = ConfigDict(from_attributes=True)


class NetworkActivityPublish(BaseModel):
    description: str | None = None
    activity_description: str | None = None
    average_traffic_mbps: int
    max_latency_ms: int

    @model_validator(mode="after")
    def populate_description(self) -> "NetworkActivityPublish":
        if not self.activity_description and self.description:
            self.activity_description = self.description
        elif not self.description and self.activity_description:
            self.description = self.activity_description
        return self
