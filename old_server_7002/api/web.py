from starlette.requests import Request
from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
import secrets
import bcrypt
import sqlalchemy
import json
import datetime

from api.database import database, user, daily_reward, result, whitelist, blacklist, batch_token, admins
from api.misc import crc32_decimal

TABLE_MAP = {
        "users": (user, ["id", "username", "password_hash", "device_id", "crc", "timestamp", "coin_mp", "save_id"]),
        "results": (result, ["rid", "vid", "tid", "sid", "stts", "id", "mode", "avatar", "score", "high_score", "play_rslt", "item", "os", "os_ver", "ver"]),
        "daily_rewards": (daily_reward, ["id", "device_id", "timestamp", "day", "my_stage", "my_avatar", "coin", "item", "lvl", "title", "avatar"]),
        "whitelist": (whitelist, ["id"]),
        "blacklist": (blacklist, ["id", "reason"]),
        "batch_tokens": (batch_token, ["id", "token", "sid", "verification_name", "verification_id", "expire_at"]),
        "admins": (admins, ["id", "username", "password", "token"]),
    }

async def is_admin(request: Request):
    token = request.cookies.get("token")
    if not token:
        return False
    query = admins.select().where(admins.c.token == token)
    admin = await database.fetch_one(query)
    if not admin:
        return False
    return True

async def web_login_page(request: Request):
    with open("web/login.html", "r", encoding="utf-8") as file:
        html_template = file.read()
    return HTMLResponse(content=html_template)

async def web_admin_page(request: Request):
    adm = await is_admin(request)
    if not adm:
        response = RedirectResponse(url="/Login")
        response.delete_cookie("token")
        return response
    with open("web/admin.html", "r", encoding="utf-8") as file:
        html_template = file.read()
    return HTMLResponse(content=html_template)

async def web_login_login(request: Request):
    form_data = await request.json()
    username = form_data.get("username")
    password = form_data.get("password")

    query = admins.select().where(admins.c.username == username)
    admin = await database.fetch_one(query)

    if not admin:
        return JSONResponse({"status": "failed", "message": "Invalid username or password."}, status_code=400)
    
    if not bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8')):
        return JSONResponse({"status": "failed", "message": "Invalid username or password."}, status_code=400)
    
    token = secrets.token_hex(64)
    admin_update = admins.update().where(admins.c.id == admin["id"]).values(token=token)
    await database.execute(admin_update)

    return JSONResponse({"status": "success", "message": token})

def serialize_row(row, allowed_fields):
    result = {}
    for field in allowed_fields:
        value = row[field]
        if hasattr(value, "isoformat"):  # Check if it's a datetime object
            result[field] = value.isoformat()
        else:
            result[field] = value
    return result

async def web_admin_get_table(request: Request):
    params = request.query_params
    adm = await is_admin(request)
    if not adm:
        return JSONResponse({"data": [], "last_page": 1, "total": 0}, status_code=400)
    
    table_name = params.get("table")
    page = int(params.get("page", 1))
    size = int(params.get("size", 25))
    sort = params.get("sort")
    dir_ = params.get("dir", "asc")
    search = params.get("search", "").strip()
    schema = params.get("schema", "0") == "1"

    if schema:
        table, _ = TABLE_MAP[table_name]
        columns = table.columns  # This is a ColumnCollection
        schema = {col.name: str(col.type).upper() for col in columns}
        return JSONResponse(schema)

    # Validate table
    if table_name not in TABLE_MAP:
        return JSONResponse({"data": [], "last_page": 1, "total": 0}, status_code=400)

    # Validate size
    if size < 10:
        size = 10
    if size > 100:
        size = 100

    table, allowed_fields = TABLE_MAP[table_name]

    # Build query
    query = table.select()

    # Search
    if search:
        search_clauses = []
        for field in allowed_fields:
            col = getattr(table.c, field, None)
            if col is not None:
                search_clauses.append(col.like(f"%{search}%"))
        if search_clauses:
            query = query.where(sqlalchemy.or_(*search_clauses))

    # Sort
    if sort in allowed_fields:
        col = getattr(table.c, sort, None)
        if col is not None:
            if isinstance(col.type, sqlalchemy.types.String):
                if dir_ == "desc":
                    query = query.order_by(sqlalchemy.func.lower(col).desc())
                else:
                    query = query.order_by(sqlalchemy.func.lower(col).asc())
            else:
                if dir_ == "desc":
                    query = query.order_by(col.desc())
                else:
                    query = query.order_by(col.asc())

    # Pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    # total count
    count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(table)
    if search:
        search_clauses = []
        for field in allowed_fields:
            col = getattr(table.c, field, None)
            if col is not None:
                search_clauses.append(col.like(f"%{search}%"))
        if search_clauses:
            count_query = count_query.where(sqlalchemy.or_(*search_clauses))
    total = await database.fetch_val(count_query)
    last_page = max(1, (total + size - 1) // size)

    # Fetch data
    rows = await database.fetch_all(query)
    data = [serialize_row(row, allowed_fields) for row in rows]

    response_data = {"data": data, "last_page": last_page, "total": total}

    print(response_data)

    return JSONResponse(response_data)

async def web_admin_table_set(request: Request):
    params = await request.json()
    adm = await is_admin(request)
    if not adm:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=400)

    table_name = params.get("table")
    row = params.get("row")

    if table_name not in TABLE_MAP:
        return JSONResponse({"status": "failed", "message": "Invalid table name."}, status_code=401)
    
    table, _ = TABLE_MAP[table_name]
    columns = table.columns  # This is a ColumnCollection

    schema = {col.name: str(col.type) for col in columns}

    try:
        row_data = row
        if not isinstance(row_data, dict):
            raise ValueError("Row data must be a JSON object.")
        id_field = None
        # Find primary key field (id or objectId)
        for pk in ["id", "objectId"]:
            if pk in row_data:
                id_field = pk
                break
        if not id_field:
            raise ValueError("Row data must contain a primary key ('id' or 'objectId').")
        for key, value in row_data.items():
            if key not in schema:
                raise ValueError(f"Field '{key}' does not exist in table schema.")
            # Type checking
            expected_type = schema[key]
            if expected_type.startswith("INTEGER"):
                if not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be an integer.")
            elif expected_type.startswith("FLOAT"):
                if not isinstance(value, float) and not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be a float.")
            elif expected_type.startswith("BOOLEAN"):
                if not isinstance(value, bool):
                    raise ValueError(f"Field '{key}' must be a boolean.")
            elif expected_type.startswith("JSON"):
                if not isinstance(value, dict) and not isinstance(value, list):
                    raise ValueError(f"Field '{key}' must be a JSON object or array.")
            elif expected_type.startswith("VARCHAR") or expected_type.startswith("STRING"):
                if not isinstance(value, str):
                    raise ValueError(f"Field '{key}' must be a string.")
            elif expected_type.startswith("DATETIME"):
                # Try to convert to datetime object
                try:
                    if isinstance(value, str):
                        dt_obj = datetime.datetime.fromisoformat(value)
                        row_data[key] = dt_obj
                    elif isinstance(value, (int, float)):
                        dt_obj = datetime.datetime.fromtimestamp(value)
                        row_data[key] = dt_obj
                    elif isinstance(value, datetime.datetime):
                        pass  # already datetime
                    else:
                        raise ValueError
                except Exception:
                    raise ValueError(f"Field '{key}' must be a valid ISO datetime string or timestamp.")
    except Exception as e:
        return JSONResponse({"status": "failed", "message": f"Invalid row data: {str(e)}"}, status_code=402)

    update_data = {k: v for k, v in row_data.items() if k != id_field}
    update_query = table.update().where(getattr(table.c, id_field) == row_data[id_field]).values(**update_data)
    await database.execute(update_query)

    return JSONResponse({"status": "success", "message": "Row updated successfully."})

async def web_admin_table_delete(request: Request):
    params = await request.json()
    adm = await is_admin(request)
    if not adm:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=400)

    table_name = params.get("table")
    row_id = params.get("id")

    if table_name not in TABLE_MAP:
        return JSONResponse({"status": "failed", "message": "Invalid table name."}, status_code=401)
    
    if not row_id:
        return JSONResponse({"status": "failed", "message": "Row ID is required."}, status_code=402)
    
    table, _ = TABLE_MAP[table_name]

    if table_name in ["results"]:
        delete_query = table.delete().where(table.c.rid == row_id)
    else:
        delete_query = table.delete().where(table.c.id == row_id)

    result = await database.execute(delete_query)

    return JSONResponse({"status": "success", "message": "Row deleted successfully."})

async def web_admin_table_insert(request: Request):
    params = await request.json()
    adm = await is_admin(request)
    if not adm:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=400)

    table_name = params.get("table")
    row = params.get("row")

    if table_name not in TABLE_MAP:
        return JSONResponse({"status": "failed", "message": "Invalid table name."}, status_code=401)
    
    table, _ = TABLE_MAP[table_name]
    columns = table.columns

    schema = {col.name: str(col.type) for col in columns}

    # VERIFY that the row data conforms to the schema
    try:
        row_data = row
        if not isinstance(row_data, dict):
            raise ValueError("Row data must be a JSON object.")
        for key, value in row_data.items():
            if key not in schema:
                raise ValueError(f"Field '{key}' does not exist in table schema.")
            expected_type = schema[key]
            if expected_type.startswith("INTEGER"):
                if not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be an integer.")
            elif expected_type.startswith("FLOAT"):
                if not isinstance(value, float) and not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be a float.")
            elif expected_type.startswith("BOOLEAN"):
                if not isinstance(value, bool):
                    raise ValueError(f"Field '{key}' must be a boolean.")
            elif expected_type.startswith("JSON"):
                try:
                    json.loads(value)
                except:
                    raise ValueError(f"Field '{key}' must be a valid JSON string.")
            elif expected_type.startswith("VARCHAR") or expected_type.startswith("STRING"):
                if not isinstance(value, str):
                    raise ValueError(f"Field '{key}' must be a string.")
            elif expected_type.startswith("DATETIME"):
                try:
                    if isinstance(value, str):
                        dt_obj = datetime.datetime.fromisoformat(value)
                        row_data[key] = dt_obj
                    elif isinstance(value, (int, float)):
                        dt_obj = datetime.datetime.fromtimestamp(value)
                        row_data[key] = dt_obj
                    elif isinstance(value, datetime.datetime):
                        pass
                    else:
                        raise ValueError
                except Exception:
                    raise ValueError(f"Field '{key}' must be a valid ISO datetime string or timestamp.")
    except Exception as e:
        return JSONResponse({"status": "failed", "message": f"Invalid row data: {str(e)}"}, status_code=402)

    insert_data = {k: v for k, v in row_data.items() if k in schema}
    insert_query = table.insert().values(**insert_data)
    result = await database.execute(insert_query)
    return JSONResponse({"status": "success", "message": "Row inserted successfully.", "inserted_id": result})

async def web_admin_data_get(request: Request):
    adm = await is_admin(request)
    if not adm:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=400)
    
    params = request.query_params
    uid = params.get("id")

    query = user.select().where(user.c.id == uid)
    data = await database.fetch_one(query)

    return JSONResponse({"status": "success", "data": data['data']})

async def web_admin_data_save(request: Request):
    adm = await is_admin(request)
    if not adm:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=400)
    
    params = await request.json()
    uid = params['id']
    save_data = params['data']

    crc = crc32_decimal(save_data)
    formatted_time = datetime.datetime.now()

    query = user.update().where(user.c.id == uid).values(data=save_data, crc=crc, timestamp=formatted_time)
    await database.execute(query)

    return JSONResponse({"status": "success", "message": "Data saved successfully."})

routes = [
    Route("/Login", web_login_page, methods=["GET"]),
    Route("/Login/", web_login_page, methods=["GET"]),
    Route("/Login/Login", web_login_login, methods=["POST"]),
    Route("/Admin", web_admin_page, methods=["GET"]),
    Route("/Admin/", web_admin_page, methods=["GET"]),
    Route("/Admin/Table", web_admin_get_table, methods=["GET"]),
    Route("/Admin/Table/Update", web_admin_table_set, methods=["POST"]),
    Route("/Admin/Table/Delete", web_admin_table_delete, methods=["POST"]),
    Route("/Admin/Table/Insert", web_admin_table_insert, methods=["POST"]),
    Route("/Admin/Data", web_admin_data_get, methods=["GET"]),
    Route("/Admin/Data/Save", web_admin_data_save, methods=["POST"]),
]