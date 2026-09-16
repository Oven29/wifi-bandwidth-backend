from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from src.data.collections import network_activity_profiles_db


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/network-profiles/feed")
def get_feed(request: Request, profile_id: int | None = None, next: bool = False):
    published = [
        p for p in network_activity_profiles_db if p["profile_status"] == "published"]

    current_index = 0
    if profile_id is not None:
        for i, p in enumerate(published):
            if p["profile_id"] == profile_id:
                current_index = i
                break

    if next:
        current_index = (current_index + 1) % len(published)

    active_profile = published[current_index]

    next_index = (current_index + 1) % len(published)
    next_profile_id = published[next_index]["profile_id"]

    likes_count = len(active_profile["liked_user_ids"])

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "profile": active_profile,
            "likes_count": likes_count,
            "next_profile_id": next_profile_id
        }
    )


@router.get("/network-profiles/draft")
def get_draft(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="draft.html",
    )


@router.get("/network-profiles/catalog")
def get_catalog(request: Request, min_bandwidth: int | None = None):
    filtered_profiles = []

    for p in network_activity_profiles_db:
        if p["profile_status"] == "published":
            if min_bandwidth is None or p["required_bandwidth_mbps"] >= min_bandwidth:
                profile_copy = p.copy()
                profile_copy["likes_count"] = len(p["liked_user_ids"])
                filtered_profiles.append(profile_copy)

    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context={
            "profiles": filtered_profiles,
            "filter_bandwidth": min_bandwidth if min_bandwidth is not None else ""
        }
    )
