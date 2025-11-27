from starlette.requests import Request
from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
import sqlalchemy
import json
import datetime

from api.database import player_database, accounts, results, devices, whitelists, blacklists, batch_tokens, binds, webs, logs, is_admin, read_user_save_file, write_user_save_file
from api.misc import crc32_decimal

TABLE_MAP = {
        "accounts": (accounts, ["id", "username", "password_hash", "save_crc", "save_timestamp", "save_id", "coin_mp", "title", "avatar", "mobile_delta", "arcade_delta", "total_delta", "created_at", "updated_at"]),
        "results": (results, ["id", "device_id", "stts", "song_id", "mode", "avatar", "score", "high_score", "play_rslt", "item", "os", "os_ver", "ver", "created_at"]),
        "devices": (devices, ["device_id", "user_id", "my_stage", "my_avatar", "item", "daily_day", "coin", "lvl", "title", "avatar", "created_at", "updated_at", "last_login_at"]),
        "whitelist": (whitelists, ["id", "device_id"]),
        "blacklist": (blacklists, ["id", "ban_terms", "reason"]),
        "batch_tokens": (batch_tokens, ["id", "batch_token", "expire_at", "uses_left", "auth_id", "created_at", "updated_at"]),
        "binds": (binds, ["id", "user_id", "bind_account", "bind_code", "is_verified", "auth_token", "bind_date"]),
        "webs": (webs, ["id", "user_id", "permission", "web_token", "last_save_export", "created_at", "updated_at"]),
        "logs": (logs, ["id", "user_id", "filename", "filesize", "timestamp"]),
    }

async def web_admin_page(request: Request):
    adm = await is_admin(request.cookies.get("token"))
    if not adm:
        response = RedirectResponse(url="/login")
        response.delete_cookie("token")
        return response
    with open("web/admin.html", "r", encoding="utf-8") as file:
        html_template = file.read()
    return HTMLResponse(content=html_template)

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
    adm = await is_admin(request.cookies.get("token"))
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
    total = await player_database.fetch_val(count_query)
    last_page = max(1, (total + size - 1) // size)

    # Fetch data
    rows = await player_database.fetch_all(query)
    data = [serialize_row(row, allowed_fields) for row in rows]

    response_data = {"data": data, "last_page": last_page, "total": total}

    return JSONResponse(response_data)

async def web_admin_table_set(request: Request):
    params = await request.json()
    adm = await is_admin(request.cookies.get("token"))
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
        for pk in ["id"]:
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
            if (value == "" or value is None) and table.c[key].nullable:
                continue  # Allow null or empty for nullable fields
            
            if expected_type.startswith("INTEGER"):
                if not isinstance(value, int):
                    try:
                        value = int(value)
                    except:
                        raise ValueError(f"Field '{key}' must be an integer.")
                    
            elif expected_type.startswith("FLOAT"):
                try:
                    value = float(value)
                except:
                    raise ValueError(f"Field '{key}' must be a float.")

            elif expected_type.startswith("BOOLEAN"):
                try:
                    if isinstance(value, str):
                        if value.lower() in ["true", "1"]:
                            value = True
                        elif value.lower() in ["false", "0"]:
                            value = False
                        else:
                            raise ValueError
                    elif isinstance(value, int):
                        value = bool(value)
                except:
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
    for upd_data in update_data:
        if upd_data == "" or upd_data is None:
            if not table.c[upd_data].nullable:
                return JSONResponse({"status": "failed", "message": f"Field '{upd_data}' cannot be null."}, status_code=403)
            else:
                update_data[upd_data] = None
    update_query = table.update().where(getattr(table.c, id_field) == row_data[id_field]).values(**update_data)
    await player_database.execute(update_query)

    return JSONResponse({"status": "success", "message": "Row updated successfully."})

async def web_admin_table_delete(request: Request):
    params = await request.json()
    adm = await is_admin(request.cookies.get("token"))
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

    result = await player_database.execute(delete_query)

    return JSONResponse({"status": "success", "message": "Row deleted successfully."})

async def web_admin_table_insert(request: Request):
    params = await request.json()
    adm = await is_admin(request.cookies.get("token"))
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
    result = await player_database.execute(insert_query)
    return JSONResponse({"status": "success", "message": "Row inserted successfully.", "inserted_id": result})

async def web_admin_data_get(request: Request):
    adm = await is_admin(request.cookies.get("token"))
    if not adm:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=400)
    
    params = request.query_params
    uid = int(params.get("id"))

    data = await read_user_save_file(uid)

    return JSONResponse({"status": "success", "data": data})

async def web_admin_data_save(request: Request):
    adm = await is_admin(request.cookies.get("token"))
    if not adm:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=400)
    
    params = await request.json()
    uid = int(params['id'])
    save_data = params['data']

    crc = crc32_decimal(save_data)
    formatted_time = datetime.datetime.now()

    query = accounts.update().where(accounts.c.id == uid).values(save_crc=crc, save_timestamp=formatted_time)
    await player_database.execute(query)
    await write_user_save_file(uid, save_data)

    return JSONResponse({"status": "success", "message": "Data saved successfully."})

routes = [
    Route("/admin", web_admin_page, methods=["GET"]),
    Route("/admin/", web_admin_page, methods=["GET"]),
    Route("/admin/table", web_admin_get_table, methods=["GET"]),
    Route("/admin/table/update", web_admin_table_set, methods=["POST"]),
    Route("/admin/table/delete", web_admin_table_delete, methods=["POST"]),
    Route("/admin/table/insert", web_admin_table_insert, methods=["POST"]),
    Route("/admin/data", web_admin_data_get, methods=["GET"]),
    Route("/admin/data/save", web_admin_data_save, methods=["POST"]),
]