import enum
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum, func

from src.db.base import Base


class ActivityStatus(str, enum.Enum):
    # Enumeration for activity status replacing simple boolean
    PUBLISHED = "published"
    DELETED = "deleted"
    DRAFT = "draft"


class NetworkActivity(Base):
    __tablename__ = "network_activities"

    id = Column(Integer, primary_key=True, index=True)
    activity_title = Column(String(100), nullable=False)
    activity_description = Column(String(500), nullable=False)
    average_traffic_mbps = Column(Integer, nullable=False)
    max_latency_ms = Column(Integer, nullable=False)
    preview_image_url = Column(String(255), nullable=False)
    preview_video_url = Column(String(255), nullable=False)

    status = Column(Enum(ActivityStatus),
                    default=ActivityStatus.PUBLISHED, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now(), nullable=True)
