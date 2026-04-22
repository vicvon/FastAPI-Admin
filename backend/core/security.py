from __future__ import annotations

import hashlib
import secrets
from base64 import b64encode
from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import Any
from uuid import uuid4

from captcha.image import ImageCaptcha
from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import get_settings
from core.cache import cache
from core.logger import get_logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = get_logger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    now = datetime.now(UTC).astimezone()
    expire = now + expires_delta
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "jti": uuid4().hex,
        "iss": settings.token_issuer,
        "aud": settings.token_audience,
        "token_type": "access",
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.refresh_token_expire_minutes)
    now = datetime.now(UTC).astimezone()
    expire = now + expires_delta
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "jti": uuid4().hex,
        "iss": settings.token_issuer,
        "aud": settings.token_audience,
        "token_type": "refresh",
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            audience=settings.token_audience,
            issuer=settings.token_issuer,
        )
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    return payload


def decode_access_token(token: str) -> dict[str, Any]:
    payload = decode_token(token)
    if payload.get("token_type") != "access":
        raise ValueError("Invalid token")
    return payload


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _captcha_cache_key(captcha_id: str) -> str:
    return f"auth:captcha:{captcha_id}"


def _normalize_captcha_code(code: str) -> str:
    return code.strip().upper()


def _generate_captcha_code(length: int) -> str:
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "".join(secrets.choice(alphabet) for _ in range(max(1, length)))


class CaptchaService:
    async def issue(self, ip: str | None, user_agent: str | None) -> dict[str, Any]:
        settings = get_settings()
        captcha_settings = settings.captcha
        captcha_id = uuid4().hex
        code = _generate_captcha_code(captcha_settings.length)
        payload = {
            "code": _normalize_captcha_code(code),
            "attempts": 0,
            "ip": ip,
            "ua": user_agent,
        }
        ok = await cache.set(
            _captcha_cache_key(captcha_id),
            payload,
            ttl=int(captcha_settings.ttl_seconds),
        )
        if not ok:
            raise RuntimeError("Captcha storage unavailable")

        generator = ImageCaptcha(width=120, height=44)
        buf = BytesIO()
        generator.write(code, buf)
        image = f"data:image/png;base64,{b64encode(buf.getvalue()).decode('ascii')}"
        return {
            "captcha_id": captcha_id,
            "image": image,
            "expires_in": int(captcha_settings.ttl_seconds),
        }

    async def verify(
        self,
        captcha_id: str | None,
        captcha_code: str | None,
        *,
        ip: str | None,
        user_agent: str | None,
    ) -> bool:
        settings = get_settings()
        captcha_settings = settings.captcha
        if not captcha_settings.enabled:
            return True

        if not captcha_id or not captcha_code:
            return False

        stored = await cache.get(_captcha_cache_key(captcha_id))
        if not stored:
            return False

        stored_code = str(stored.get("code", ""))
        attempts = int(stored.get("attempts", 0))
        stored_ip = stored.get("ip")
        stored_ua = stored.get("ua")

        if stored_ip and ip and stored_ip != ip:
            return False
        if stored_ua and user_agent and stored_ua != user_agent:
            return False

        if attempts >= int(captcha_settings.max_attempts):
            await cache.delete(_captcha_cache_key(captcha_id))
            return False

        ok = secrets.compare_digest(_normalize_captcha_code(captcha_code), stored_code)
        if ok:
            await cache.delete(_captcha_cache_key(captcha_id))
            return True

        stored["attempts"] = attempts + 1
        await cache.set(
            _captcha_cache_key(captcha_id),
            stored,
            ttl=int(captcha_settings.ttl_seconds),
        )
        return False


class TokenService:
    async def issue_token_pair(
        self, user_id: int, token_version: int
    ) -> tuple[str, str]:
        settings = get_settings()
        access_token = create_access_token(
            subject=user_id, extra_claims={"tv": token_version}
        )
        refresh_token = create_refresh_token(
            subject=user_id, extra_claims={"tv": token_version}
        )
        refresh_payload = decode_token(refresh_token)
        refresh_jti = refresh_payload.get("jti")
        if not refresh_jti:
            raise ValueError("Invalid token")
        ttl_seconds = int(settings.refresh_token_expire_minutes * 60)
        stored = {"uid": user_id, "tv": token_version, "h": _sha256_hex(refresh_token)}
        ok = await cache.set(f"auth:rt:{refresh_jti}", stored, ttl=ttl_seconds)
        if not ok:
            raise RuntimeError("Refresh token storage unavailable")
        return access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        payload = decode_token(refresh_token)
        if payload.get("token_type") != "refresh":
            raise ValueError("Invalid token")
        refresh_jti = payload.get("jti")
        if not refresh_jti:
            raise ValueError("Invalid token")

        stored = await cache.get(f"auth:rt:{refresh_jti}")
        if not stored or stored.get("h") != _sha256_hex(refresh_token):
            raise ValueError("Invalid token")

        await cache.delete(f"auth:rt:{refresh_jti}")

        user_id = int(payload["sub"])
        token_version = int(payload.get("tv", 0))
        return await self.issue_token_pair(user_id=user_id, token_version=token_version)

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token)
        if payload.get("token_type") != "refresh":
            raise ValueError("Invalid token")
        refresh_jti = payload.get("jti")
        if not refresh_jti:
            raise ValueError("Invalid token")
        stored = await cache.get(f"auth:rt:{refresh_jti}")
        if stored and stored.get("h") == _sha256_hex(refresh_token):
            await cache.delete(f"auth:rt:{refresh_jti}")

    async def revoke_access_token(self, access_token: str) -> None:
        payload = decode_access_token(access_token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            return
        now_ts = int(datetime.now(UTC).astimezone().timestamp())
        ttl_seconds = int(exp) - now_ts
        if ttl_seconds <= 0:
            return
        await cache.set(f"auth:bl:{jti}", "1", ttl=ttl_seconds)

    async def is_access_token_revoked(self, payload: dict[str, Any]) -> bool:
        jti = payload.get("jti")
        if not jti:
            return False
        try:
            return await cache.exists(f"auth:bl:{jti}")
        except Exception:
            logger.opt(exception=True).warning("auth.blacklist_check_failed")
            return False
