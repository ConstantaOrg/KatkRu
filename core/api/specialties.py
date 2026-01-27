from fastapi import APIRouter

from core.data.postgre import PgSqlDep
from core.schemas.specs_schema import SpecsPaginSchema
from core.response_schemas.specialties import SpecialtiesAllResponse, SpecialtyGetResponse

router = APIRouter(prefix='/public/specialties', tags=['Specs📖'])


@router.post('/all', response_model=SpecialtiesAllResponse)
async def specialties_all(pagen: SpecsPaginSchema, db: PgSqlDep):
    specs = await db.specialties.get_specialties(pagen.limit, pagen.offset)
    return {'specialties': [dict(spec) for spec in specs]}


@router.get('/{spec_id}', response_model=SpecialtyGetResponse)
async def specialties_get(spec_id: int, db: PgSqlDep):
    ext_spec = await db.specialties.get_spec_by_id(spec_id)
    return {'speciality': dict(ext_spec)}
