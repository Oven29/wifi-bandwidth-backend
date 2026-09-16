from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from src.data.collections import network_activities_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/network-activities/feed")
def get_feed(request: Request, activity_id: int | None = None, next: bool = False):
    published = [
        a for a in network_activities_db if a["activity_status"] == "published"
    ]

    current_index = 0
    if activity_id is not None:
        for i, a in enumerate(published):
            if a["activity_id"] == activity_id:
                current_index = i
                break

    if next:
        current_index = (current_index + 1) % len(published)

    active_activity = published[current_index]

    next_index = (current_index + 1) % len(published)
    next_activity_id = published[next_index]["activity_id"]

    likes_count = len(active_activity["liked_user_ids"])

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "activity": active_activity,
            "likes_count": likes_count,
            "next_activity_id": next_activity_id
        }
    )


@router.get("/network-activities/draft")
def get_draft(request: Request):
    draft_activity = None
    for a in network_activities_db:
        if a["activity_status"] == "draft":
            draft_activity = a
            break

    return templates.TemplateResponse(
        request=request,
        name="draft.html",
        context={
            "activity": draft_activity
        }
    )


@router.get("/network-activities/catalog")
def get_catalog(request: Request, filter_traffic: int | None = None):
    filtered_activities = []

    for a in network_activities_db:
        if a["activity_status"] == "published":
            if filter_traffic is None or a["average_traffic_mbps"] <= filter_traffic:
                activity_copy = a.copy()
                activity_copy["likes_count"] = len(a["liked_user_ids"])
                filtered_activities.append(activity_copy)

    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context={
            "activities": filtered_activities,
            "filter_traffic": filter_traffic if filter_traffic is not None else ""
        }
    )
