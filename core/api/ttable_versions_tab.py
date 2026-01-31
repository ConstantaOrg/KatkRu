from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from core.data.postgre import PgSqlDep
from core.response_schemas.ttable_versions_tab import TtableVersionsCommitResponse
from core.utils.response_model_utils import (
    TtableVersionsPreCommitResponse, TtableVersionsPreCommitSuccessResponse, TtableVersionsPreCommitConflictResponse,
    create_ttable_precommit_response, create_response_json
)
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.ttable_schema import CommitTtableVersionSchema, PreAcceptTimetableSchema
from core.utils.anything import Roles
from core.utils.lite_dependencies import role_require

router = APIRouter(prefix="/private/ttable/versions", tags=["Versions0️⃣1️⃣"])

@router.put("/pre-commit", dependencies=[Depends(role_require(Roles.methodist))], responses={
    200: {"model": TtableVersionsPreCommitSuccessResponse, "description": "Timetable version ready for commit"},
    202: {"model": TtableVersionsPreCommitConflictResponse, "description": "Timetable version has conflicts with existing schedule"},
    409: {"model": TtableVersionsPreCommitConflictResponse, "description": "Missing groups in timetable version"}
})
async def accept_ttable_version(body: PreAcceptTimetableSchema, db: PgSqlDep, _: JWTCookieDep):
    updating = await db.ttable.check_accept_constraints(body.ttable_id)
    
    if not updating:
        # Success case - use @overload function for type-safe response
        response = create_ttable_precommit_response(success=True)
        return create_response_json(response, status_code=200)
    
    # Conflict case - use @overload function for type-safe response
    status_code, error_data = updating
    response = create_ttable_precommit_response(
        success=False,
        needed_groups=error_data.get("needed_groups", []),
        ttable_id=error_data.get("ttable_id", body.ttable_id),
        message=error_data.get("message", "Conflicts detected in timetable version"),
        cur_active_ver=error_data.get("cur_active_ver"),
        pending_ver_id=error_data.get("pending_ver_id")
    )
    return create_response_json(response, status_code=status_code)


@router.put("/commit", dependencies=[Depends(role_require(Roles.methodist))], response_model=TtableVersionsCommitResponse)
async def accept_ttable_version(body: CommitTtableVersionSchema, db: PgSqlDep, _: JWTCookieDep):
    await db.ttable.commit_version(body.pending_ver_id, body.target_ver_id)
    return {'success': True, 'message': 'Версии переключены!'}
