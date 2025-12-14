from fastapi import APIRouter

from core.data.postgre import PgSqlDep
from core.schemas.specs_schema import SpecsPaginSchema

router = APIRouter(prefix='/v1/specs', tags=['Specs📖'])


@router.get('/specs_all')
async def specialties_all(pagin: SpecsPaginSchema, db: PgSqlDep):
    specs = await db.specialties.get_specialties(pagin.limit, pagin.offset)
    return {'specialties': specs}


@router.get('/specialties/{spec_id}')
async def specialties_get(spec_id: int, db: PgSqlDep):
    ext_spec = await db.specialties.get_spec_by_id(spec_id)
    return {'speciality': ext_spec}
