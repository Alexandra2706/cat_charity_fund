from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators import (
    check_close, check_close_before_update, check_invested_amount,
    check_name_duplicate, check_project_exists, check_value)
from app.core.db import get_async_session
from app.core.user import current_superuser
from app.crud.charity_project import charity_project_crud
from app.schemas.charity_project import (
    CharityProjectCreate, CharityProjectDB, CharityProjectUpdate)
from app.utils.donation_processing import donation_processing

router = APIRouter()


@router.post(
        '/',
        response_model=CharityProjectDB,
        response_model_exclude_none=True,
        dependencies=[Depends(current_superuser)],)
async def create_new_charity_project(
        charity_project: CharityProjectCreate,
        session: AsyncSession=Depends(get_async_session),
):
    """Создание нового проекта."""
    """Только для суперюзеров."""
    await check_name_duplicate(charity_project.name, session)
    new_project = await charity_project_crud.create(charity_project, session)
    new_project = await donation_processing(new_project, session)
    return new_project


@router.get(
    '/',
    response_model=List[CharityProjectDB],
    response_model_exclude_none=True,
)
async def get_all_project(
        session: AsyncSession=Depends(get_async_session),
):
    """Возвращает список всех проектов."""
    all_projects = await charity_project_crud.get_multi(session)
    return all_projects


@router.patch(
    '/{project_id}',
    response_model=CharityProjectDB,
    dependencies=[Depends(current_superuser)],
)
async def partially_update_project(
        project_id: int,
        obj_in: CharityProjectUpdate,
        session: AsyncSession=Depends(get_async_session),
):
    """Редактирование проекта."""
    """Только для суперюзеров."""
    project = await check_project_exists(project_id, session)
    await check_close_before_update(project.fully_invested)
    if obj_in.name is not None:
        await check_name_duplicate(obj_in.name, session)
    if obj_in.full_amount is not None:
        await check_value(obj_in.full_amount, project.invested_amount)
    project = await charity_project_crud.update(
       project, obj_in, session
    )
    return project


@router.delete(
    '/{project_id}',
    response_model=CharityProjectDB,
    dependencies=[Depends(current_superuser)],
)
async def remove_project(
        project_id: int,
        session: AsyncSession=Depends(get_async_session),
):
    """Удаление проекта."""
    """Только для суперюзеров."""
    project = await check_project_exists(project_id, session)
    await check_close(project.fully_invested)
    await check_invested_amount(project.invested_amount)
    project = await charity_project_crud.remove(project, session)
    return project
