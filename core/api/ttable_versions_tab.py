from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from core.data.postgre import PgSqlDep
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.ttable_schema import CommitTtableVersionSchema, PreAcceptTimetableSchema
from core.utils.anything import Roles
from core.utils.lite_dependencies import role_require

router = APIRouter(prefix="/private/ttable/versions", tags=["Versions0️⃣1️⃣ !NOT TESTED & NOT CHECKED!"])

@router.put("/pre-commit", dependencies=[Depends(role_require(Roles.methodist))])
async def accept_ttable_version(body: PreAcceptTimetableSchema, db: PgSqlDep, _: JWTCookieDep):
    updating = await db.ttable.check_accept_constraints(body.ttable_id)
    if not updating:
        return {'success': True, 'message': 'Расписание подтверждено и активно!'}
    return JSONResponse(status_code=updating[0], content=updating[1])


@router.put("/commit", dependencies=[Depends(role_require(Roles.methodist))])
async def accept_ttable_version(body: CommitTtableVersionSchema, db: PgSqlDep, _: JWTCookieDep):
    await db.ttable.commit_version(body.pending_ver_id, body.target_ver_id)
    return {'success': True, 'message': 'Версии переключены!'}
