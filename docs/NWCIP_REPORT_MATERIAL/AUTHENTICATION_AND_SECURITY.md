# Authentication and Security

## Overview
The platform uses **JWT (JSON Web Tokens)** for stateless authentication and **role‑based access control (RBAC)** to protect endpoints.

## JWT Creation
```python
# backend/app/services/auth_service.py (excerpt)
payload = {
    "sub": user.email,
    "role": role_name,
    "user_id": user.id,
    "username": user.username,
    "approval_status": getattr(user, "approval_status", "APPROVED"),
    "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
}
access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

* `sub` – user email (principal)
* `role` – one of `ADMIN`, `RESEARCHER`, `FOREST_OFFICER`, `NGO`, `CITIZEN`
* `exp` – expiration time (default 30 min, configurable via `settings.ACCESS_TOKEN_EXPIRE_MINUTES`)

## Token Validation
```python
# backend/app/dependencies.py – get_current_user
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials or token expired",
    headers={"WWW-Authenticate": "Bearer"},
)
if not token:
    raise credentials_exception

token_data = AuthService.decode_access_token(token)
if token_data is None or token_data.email is None:
    raise credentials_exception
user = db.query(User).filter(User.email == token_data.email).first()
if not user or not user.is_active:
    raise credentials_exception
```

## RBAC Guard
```python
# backend/app/dependencies.py – require_roles
allowed_set = {str(r).upper() for r in flattened}

def role_checker(current_user: User = Depends(get_current_user)) -> User:
    approval_status = getattr(current_user, "approval_status", "APPROVED")
    if approval_status in {"PENDING", "REJECTED"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not approved")
    user_role = current_user.role.name.upper() if current_user.role else "VIEWER"
    if user_role not in allowed_set and "ADMIN" not in user_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden: requires one of roles [{', '.join(allowed_set)}]. User is '{user_role}'.")
    return current_user
```

### Protected Endpoints
* `/spatial/*` – requires no special role for read, but precise‑location data is only returned to `ADMIN`, `FOREST_OFFICER`, `RESEARCHER` (checked via `_is_authorized_for_precise_locations`).
* `/auth/*` – registration, login, token issuance.
* `/ml/*`, `/rag/*` – protected by `require_roles(["ADMIN", "RESEARCHER"])`.

## Password Storage
* Passwords are hashed with **bcrypt** via `passlib` (`AuthService.hash_password`).
* `passlib[bcrypt]` is listed in `backend/requirements.txt`.

## Security Controls
* **HTTPS** should be enforced in production (not part of the repo). 
* **Rate‑limiting** on `/auth/register/resend` via `AuthService.resend_verification` (cool‑down logic).
* **Coordinate fuzzing** for CR/EN species (see GIS implementation) to protect sensitive locations.
* **Secrets** (JWT secret, DB credentials) are loaded from `.env` and never committed.

---
*All file references are relative to the repository root.*

