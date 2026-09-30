from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text

from src.db.session import get_db
from src.models.network_activity import NetworkActivity, ActivityStatus
from src.models.like import Like

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/network-activities/feed")
async def get_feed(
    request: Request,
    activity_id: int | None = None,
    page: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NetworkActivity)
        .where(NetworkActivity.status == ActivityStatus.PUBLISHED)
        .order_by(NetworkActivity.id)
    )
    published = result.scalars().all()

    if not published:
        return templates.TemplateResponse(
            request=request,
            name="feed.html",
            context={
                "activity": None,
                "likes_count": 0,
                "next_activity_id": None,
            },
        )

    total = len(published)

    current_index = 0

    if activity_id is not None:
        for i, a in enumerate(published):
            if a.id == activity_id:
                current_index = i
                break
        else:
            current_index = 0
    elif page is not None and 0 <= page < total:
        current_index = page

    active_activity = published[current_index]

    next_index = (current_index + 1) % total
    next_activity_id = published[next_index].id

    likes_result = await db.execute(
        select(func.count(Like.id)).where(
            Like.activity_id == active_activity.id)
    )
    likes_count = likes_result.scalar_one()

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "activity": active_activity,
            "likes_count": likes_count,
            "next_activity_id": next_activity_id if total > 1 else None,
        },
    )


@router.get("/network-activities/draft")
async def get_draft(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NetworkActivity).where(
            NetworkActivity.status == ActivityStatus.DRAFT)
    )
    draft_activity = result.scalar_one_or_none()

    return templates.TemplateResponse(
        request=request,
        name="draft.html",
        context={
            "activity": draft_activity
        }
    )


@router.post("/network-activities/create")
async def create_activity(
    activity_title: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    new_activity = NetworkActivity(
        activity_title=activity_title,
        activity_description="",
        average_traffic_mbps=0,
        max_latency_ms=0,
        preview_image_url="http://localhost:9000/media/telek.png",
        preview_video_url="http://localhost:9000/media/telek.mp4",
        status=ActivityStatus.DRAFT
    )
    db.add(new_activity)
    await db.commit()
    return RedirectResponse(url="/network-activities/draft", status_code=303)


@router.post("/network-activities/publish")
async def publish_activity(
    activity_id: int = Form(...),
    activity_description: str = Form(...),
    average_traffic_mbps: int = Form(...),
    max_latency_ms: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(NetworkActivity).where(NetworkActivity.id == activity_id)
    )
    activity = result.scalar_one_or_none()

    if activity:
        activity.activity_description = activity_description
        activity.average_traffic_mbps = average_traffic_mbps
        activity.max_latency_ms = max_latency_ms
        activity.status = ActivityStatus.PUBLISHED
        await db.commit()

    return RedirectResponse(url="/network-activities/catalog", status_code=303)


@router.get("/network-activities/catalog")
async def get_catalog(
    request: Request,
    search: str = "",
    filter_traffic: int | None = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NetworkActivity).where(
        NetworkActivity.status == ActivityStatus.PUBLISHED)

    if search:
        stmt = stmt.where(NetworkActivity.activity_title.ilike(f"%{search}%"))

    if filter_traffic is not None:
        stmt = stmt.where(
            NetworkActivity.average_traffic_mbps <= filter_traffic)

    result = await db.execute(stmt)
    activities = result.scalars().all()

    filtered_activities = []
    for a in activities:
        likes_result = await db.execute(
            select(Like).where(Like.activity_id == a.id)
        )
        likes_count = len(likes_result.scalars().all())

        activity_copy = {
            "activity_id": a.id,
            "activity_title": a.activity_title,
            "activity_description": a.activity_description,
            "average_traffic_mbps": a.average_traffic_mbps,
            "max_latency_ms": a.max_latency_ms,
            "preview_image_url": a.preview_image_url or "http://localhost:9000/media/telek.png",
            "preview_video_url": a.preview_video_url or "http://localhost:9000/media/telek.mp4",
            "likes_count": likes_count
        }
        filtered_activities.append(activity_copy)

    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context={
            "activities": filtered_activities,
            "search": search,
            "filter_traffic": filter_traffic if filter_traffic is not None else ""
        }
    )


@router.post("/network-activities/{activity_id}/delete")
async def delete_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    update_query = """
        UPDATE network_activities 
        SET status = 'DELETED' 
        WHERE id = :id
    """
    await db.execute(text(update_query), {"id": activity_id})
    await db.commit()

    return RedirectResponse(url="/network-activities/catalog", status_code=303)
