from fastapi import APIRouter, Response, Request, HTTPException

from core.api.users.rate_limiter import rate_limit
from core.data.postgre import PgSqlDep
from core.config_dir.config import encryption
from core.schemas.cookie_settings_schema import AccToken, RtToken, JWTCookieDep
from core.schemas.users_schema import TokenPayloadSchema, UserRegSchema, UserLogInSchema, UpdatePasswSchema
from core.utils.anything import hide_log_param
from core.utils.jwt_factory import issue_aT_rT
from core.utils.logger import log_event
from core.utils.response_model_utils import (
    UserRegistrationSuccessResponse, UserRegistrationConflictResponse,
    UserLoginSuccessResponse, UserLoginUnauthorizedResponse,
    create_user_registration_response, create_user_login_response, create_response_json
)

router = APIRouter(tags=['Users👤'])



@router.post('/server/users/sign_up', summary="Регистрация", responses={
    200: {"model": UserRegistrationSuccessResponse, "description": "User registered successfully"},
    409: {"model": UserRegistrationConflictResponse, "description": "User already exists"}
})
async def registration_user(creds: UserRegSchema, db: PgSqlDep, request: Request):
    insert_attempt = await db.users.reg_user(creds.email, creds.passw, creds.name)

    if not insert_attempt:
        log_event(f"Пользователь с email: {hide_log_param(creds.email)} Уже существует", request=request, level='WARNING')
        # Use @overload function for type-safe conflict response
        response = create_user_registration_response(success=False)
        return create_response_json(response, status_code=409)

    log_event(f"Новый пользователь! email: {hide_log_param(creds.email)}", request=request)
    # Use @overload function for type-safe success response
    response = create_user_registration_response(success=True)
    return create_response_json(response, status_code=200)


@router.post('/public/users/login', summary="Вход в аккаунт", responses={
    200: {"model": UserLoginSuccessResponse, "description": "User logged in successfully"},
    401: {"model": UserLoginUnauthorizedResponse, "description": "Invalid credentials"}
})
@rate_limit(5, 300)
async def log_in(creds: UserLogInSchema, response: Response, db: PgSqlDep, request: Request):
    db_user = await db.users.select_user(creds.email)

    if db_user and encryption.verify(creds.passw, db_user['passw']):
        token_schema = TokenPayloadSchema(
            id=db_user['id'],
            role=db_user['role'],
            user_agent=request.headers.get('user-agent'),
            ip=request.state.client_ip,
        )
        access_token, refresh_token = await issue_aT_rT(db, token_schema)

        response.set_cookie('access_token', access_token, **AccToken().model_dump())
        response.set_cookie('refresh_token', refresh_token, **RtToken().model_dump())
        log_event("Пользователь Вошёл в акк | user_id: %s", db_user['id'], request=request)
        # Use @overload function for type-safe success response
        login_response = create_user_login_response(success=True)
        return create_response_json(login_response, status_code=200)
    
    log_event(f"Пользователь с email: {hide_log_param(creds.email)} Не смог войти", request=request, level='WARNING')
    # Use @overload function for type-safe unauthorized response
    login_response = create_user_login_response(success=False)
    return create_response_json(login_response, status_code=401)


@router.put('/private/users/logout')
async def log_out(request: Request, response: Response, db: PgSqlDep, _: JWTCookieDep):
    await db.auth.session_termination(request.state.user_id, request.state.session_id)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    log_event("Пользователь разлогинился | user_id: %s; s_id: %s", request.state.user_id, request.state.session_id, request=request)
    return {'success': True, 'message': 'Пользователь вне аккаунта'}


@router.post('/private/users/seances', summary='Все Устройства аккаунта')
async def show_seances(request: Request, db: PgSqlDep, _: JWTCookieDep):
    log_event("Запрос всех Устройств с акка | user_id: %s; s_id: %s", request.state.user_id, request.state.session_id, request=request, level='INFO')
    seances = await db.auth.all_seances_user(request.state.user_id, request.state.session_id)
    return {'seances': seances}


@router.put('/server/users/passw/set_new_passw')
async def reset_password(update_secrets: UpdatePasswSchema, db: PgSqlDep, request: Request):
    hashed_passw = encryption.hash(update_secrets.passw)
    await db.users.set_new_passw(update_secrets.user_id, hashed_passw)
    log_event(f"Юзер сменил Пароль | user_id: {update_secrets.user_id}", request=request, level='WARNING')
    return {'success': True, 'message': 'Пароль обновлён!'}
