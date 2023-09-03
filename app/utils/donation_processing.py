from datetime import datetime
from typing import Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CharityProject, Donation


async def close_object(obj: Union[CharityProject, Donation]):
    """Изменение статуса проекта/пожертвования на закрытый"""
    obj.invested_amount = obj.full_amount
    obj.fully_invested = True
    obj.close_date = datetime.now()


async def donation_processing(
        obj_in: Union[CharityProject, Donation],
        session: AsyncSession
):
    if isinstance(obj_in, Donation):
        obj_model = CharityProject
    else:
        obj_model = Donation
    objs_db = await session.execute(
        select(obj_model).where(
            obj_model.fully_invested == 0).order_by(
            obj_model.id.desc()))
    objs_db = objs_db.scalars().all()

    while obj_in.full_amount > obj_in.invested_amount and objs_db:
        obj_db = objs_db.pop()
        required_amount = obj_in.full_amount - obj_in.invested_amount
        available_amount = obj_db.full_amount - obj_db.invested_amount
        if required_amount > available_amount:
            await close_object(obj_db)
            obj_in.invested_amount += available_amount
        elif required_amount < available_amount:
            await close_object(obj_in)
            obj_db.invested_amount += required_amount
        else:
            await close_object(obj_db)
            await close_object(obj_in)

    session.add(obj_in)
    await session.commit()
    await session.refresh(obj_in)
    return obj_in
