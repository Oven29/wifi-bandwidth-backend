from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.core.minio_client import upload_file_to_minio
from src.db.session import get_db
from src.models.like import Like
from src.models.network_activity import ActivityStatus, NetworkActivity
from src.models.user import User
from src.schemas.network_activity import NetworkActivityPublish, NetworkActivityResponse

router = APIRouter(prefix="/api/network-activities", tags=["Network Activities"])


@router.get("", response_model=list[NetworkActivityResponse])
@router.get("/", response_model=list[NetworkActivityResponse])
async def list_activities(
    filter_traffic: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
):
    stmt = (
        select(NetworkActivity)
        .where(NetworkActivity.status == ActivityStatus.PUBLISHED)
        .order_by(NetworkActivity.id.asc())
    )
    if filter_traffic is not None:
        stmt = stmt.where(NetworkActivity.average_traffic_mbps <= filter_traffic)

    result = await db.execute(stmt)
    activities = result.scalars().all()

    response = []
    for act in activities:
        item = NetworkActivityResponse.model_validate(act)
        item.is_owner = 1 if act.creator_id == current_user_id else 0
        response.append(item)
    return response


@router.get("/feed")
async def get_feed(
    activity_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
):
    active_activity = None
    if activity_id is not None:
        result = await db.execute(
            select(NetworkActivity)
            .where(
                NetworkActivity.id == activity_id,
                NetworkActivity.status == ActivityStatus.PUBLISHED,
            )
            .limit(1)
        )
        active_activity = result.scalar_one_or_none()

    if active_activity is None:
        result = await db.execute(
            select(NetworkActivity)
            .where(NetworkActivity.status == ActivityStatus.PUBLISHED)
            .order_by(NetworkActivity.id.asc())
            .limit(1)
        )
        active_activity = result.scalar_one_or_none()

    if not active_activity:
        return {
            "activity": None,
            "next_id": None,
            "next_activity_id": None,
        }

    next_result = await db.execute(
        select(NetworkActivity.id)
        .where(
            NetworkActivity.id > active_activity.id,
            NetworkActivity.status == ActivityStatus.PUBLISHED,
        )
        .order_by(NetworkActivity.id.asc())
        .limit(1)
    )
    next_activity_id = next_result.scalar_one_or_none()

    if next_activity_id is None:
        wrap_result = await db.execute(
            select(NetworkActivity.id)
            .where(NetworkActivity.status == ActivityStatus.PUBLISHED)
            .order_by(NetworkActivity.id.asc())
            .limit(1)
        )
        next_activity_id = wrap_result.scalar_one_or_none()

    activity_resp = NetworkActivityResponse.model_validate(active_activity)
    activity_resp.is_owner = 1 if active_activity.creator_id == current_user_id else 0

    return {
        "activity": activity_resp,
        "next_id": next_activity_id,
        "next_activity_id": next_activity_id,
    }


@router.get("/draft", response_model=NetworkActivityResponse | None)
async def get_draft(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
):
    result = await db.execute(
        select(NetworkActivity)
        .where(
            NetworkActivity.creator_id == current_user_id,
            NetworkActivity.status == ActivityStatus.DRAFT,
        )
        .order_by(NetworkActivity.id.desc())
        .limit(1)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        return None

    resp = NetworkActivityResponse.model_validate(draft)
    resp.is_owner = 1
    return resp


@router.post("", response_model=NetworkActivityResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=NetworkActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    activity_title: str = Form(...),
    pic: UploadFile = File(...),
    video: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
):
    image_url = upload_file_to_minio(pic)
    video_url = upload_file_to_minio(video)

    new_activity = NetworkActivity(
        activity_title=activity_title,
        activity_description="",
        average_traffic_mbps=0,
        max_latency_ms=0,
        preview_image_url=image_url,
        preview_video_url=video_url,
        status=ActivityStatus.DRAFT,
        creator_id=current_user_id,
    )
    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)

    resp = NetworkActivityResponse.model_validate(new_activity)
    resp.is_owner = 1
    return resp


@router.put("/{id}/publish", response_model=NetworkActivityResponse)
async def publish_activity(
    id: int,
    data: NetworkActivityPublish,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
):
    result = await db.execute(
        select(NetworkActivity).where(NetworkActivity.id == id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )

    if activity.creator_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this activity",
        )

    if activity.status == ActivityStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish a deleted activity",
        )

    activity.activity_description = data.activity_description or data.description or ""
    activity.average_traffic_mbps = data.average_traffic_mbps
    activity.max_latency_ms = data.max_latency_ms
    activity.status = ActivityStatus.PUBLISHED

    await db.commit()
    await db.refresh(activity)

    resp = NetworkActivityResponse.model_validate(activity)
    resp.is_owner = 1
    return resp


@router.delete("/{id}")
async def delete_activity(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
):
    result = await db.execute(
        select(NetworkActivity).where(NetworkActivity.id == id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )

    if activity.creator_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this activity",
        )

    activity.status = ActivityStatus.DELETED
    await db.commit()
    return {"message": "deleted", "id": id}


@router.post("/{id}/like")
async def toggle_like(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
):
    act_result = await db.execute(
        select(NetworkActivity).where(NetworkActivity.id == id)
    )
    activity = act_result.scalar_one_or_none()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )

    like_result = await db.execute(
        select(Like).where(
            Like.activity_id == id,
            Like.user_id == current_user_id,
        )
    )
    existing_like = like_result.scalar_one_or_none()

    if existing_like:
        await db.delete(existing_like)
        await db.commit()
        return {"status": 0}

    new_like = Like(user_id=current_user_id, activity_id=id)
    db.add(new_like)
    await db.commit()
    return {"status": 1}
