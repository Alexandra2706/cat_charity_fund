from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import current_superuser, current_user
from app.crud.donation import donation_crud
from app.models import User
from app.schemas.donation import DonationAllDB, DonationDB, DonationCreate
from app.utils.donation_processing import donation_processing

router = APIRouter()


@router.post(
    '/',
    response_model=DonationDB,
    response_model_exclude_none=True)
async def create_new_donation(
        donation: DonationCreate,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_user),
):
    """Создание нового пожертвования."""
    """Только для зарегистрованных пользователей."""
    new_donation = await donation_crud.create(donation, session, user)
    new_donation = await donation_processing(new_donation, session)
    return new_donation


@router.get(
    '/',
    response_model=List[DonationAllDB],
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)], )
async def get_all_donations(
        session: AsyncSession = Depends(get_async_session)
):
    donations = await donation_crud.get_multi(session)
    return donations


@router.get(
    '/my',
    response_model=List[DonationDB])
async def get_my_donation(
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_user),
):
    donations = await donation_crud.get_by_user(session=session, user=user)
    return donations
