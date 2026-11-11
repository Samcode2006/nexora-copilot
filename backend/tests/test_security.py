import base64
import json
import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import APIRouter

from app.api.deps import CurrentUser, get_token_verifier
from app.core.config import get_settings
from app.core.security import TokenVerifier

S = get_settings()
HS_SECRET = S.supabase_jwt_secret


class FakeJWKS:
    def __init__(self, key=None):
        self.key = key

    def get_signing_key_from_jwt(self, token):
        return SimpleNamespace(key=self.key)


def claims(**over):
    base = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "a@example.com",
        "aud": S.supabase_jwt_audience,
        "iss": S.jwt_issuer,
        "exp": int(time.time()) + 600,
    }
    base.update(over)
    return {k: v for k, v in base.items() if v is not None}


@pytest.fixture(scope="module")
def ec_key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="module")
def rsa_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def hs(payload=None):
    return jwt.encode(payload or claims(), HS_SECRET, algorithm="HS256")


async def test_valid_hs256():
    user = await TokenVerifier(S, FakeJWKS()).verify(hs())
    assert user.id == claims()["sub"]
    assert user.email == "a@example.com"


async def test_valid_es256(ec_key):
    token = jwt.encode(claims(), ec_key, algorithm="ES256", headers={"kid": "k1"})
    user = await TokenVerifier(S, FakeJWKS(ec_key.public_key())).verify(token)
    assert user.id == claims()["sub"]


async def test_valid_rs256(rsa_key):
    token = jwt.encode(claims(), rsa_key, algorithm="RS256", headers={"kid": "k1"})
    user = await TokenVerifier(S, FakeJWKS(rsa_key.public_key())).verify(token)
    assert user.id == claims()["sub"]


def _bad_tokens(ec_key):
    other = ec.generate_private_key(ec.SECP256R1())
    b64 = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
    none_token = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64(claims())}."
    return {
        "expired": hs(claims(exp=int(time.time()) - 10)),
        "wrong_aud": hs(claims(aud="other")),
        "wrong_iss": hs(claims(iss="https://evil.example/auth/v1")),
        "missing_sub": hs(claims(sub=None)),
        "missing_exp": hs(claims(exp=None)),
        "bad_signature_hs": jwt.encode(claims(), "x" * 40, algorithm="HS256"),
        "bad_signature_es": jwt.encode(claims(), other, algorithm="ES256"),
        "alg_none": none_token,
        "garbage": "not.a.jwt",
        "empty": "x",
    }


async def test_negative_cases_all_401(ec_key):
    verifier = TokenVerifier(S, FakeJWKS(ec_key.public_key()))
    for name, token in _bad_tokens(ec_key).items():
        with pytest.raises(Exception) as ei:
            await verifier.verify(token)
        assert getattr(ei.value, "status_code", None) == 401, name
        assert ei.value.code == "UNAUTHENTICATED", name


async def test_hs256_rejected_when_not_configured():
    s = S.model_copy(update={"supabase_jwt_secret": None})
    with pytest.raises(Exception) as ei:
        await TokenVerifier(s, FakeJWKS()).verify(hs())
    assert ei.value.status_code == 401


async def test_algorithm_confusion_rejected(ec_key):
    """An HS256 token signed with the PUBLIC key bytes must not verify via the JWKS path."""
    from cryptography.hazmat.primitives import serialization

    pub = ec_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    s = S.model_copy(update={"supabase_jwt_secret": "different-secret-0123456789abcdef!!"})
    # PyJWT refuses to HMAC-sign with PEM keys; forge the token with a raw HMAC instead.
    import hashlib
    import hmac

    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    head = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = b64(json.dumps(claims()).encode())
    sig = hmac.new(pub, f"{head}.{body}".encode(), hashlib.sha256).digest()
    forged = f"{head}.{body}.{b64(sig)}"
    with pytest.raises(Exception) as ei:
        await TokenVerifier(s, FakeJWKS(ec_key.public_key())).verify(forged)
    assert ei.value.status_code == 401


@pytest.fixture
def protected(app):
    router = APIRouter()

    @router.get("/api/v1/_whoami")
    async def whoami(user: CurrentUser):
        return {"id": user.id}

    app.include_router(router)
    app.dependency_overrides[get_token_verifier] = lambda: TokenVerifier(S, FakeJWKS())
    return app


async def test_endpoint_missing_header_401(protected, client):
    r = await client.get("/api/v1/_whoami")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_endpoint_malformed_header_401(protected, client):
    for h in ("Basic abc", "Bearer", "Bearer   ", "token"):
        r = await client.get("/api/v1/_whoami", headers={"Authorization": h})
        assert r.status_code == 401, h


async def test_endpoint_valid_token(protected, client):
    r = await client.get("/api/v1/_whoami", headers={"Authorization": f"Bearer {hs()}"})
    assert r.status_code == 200
    assert r.json() == {"id": claims()["sub"]}


async def test_401_does_not_leak_cause(protected, client):
    r = await client.get(
        "/api/v1/_whoami", headers={"Authorization": f"Bearer {hs(claims(aud='x'))}"}
    )
    assert r.status_code == 401
    assert "aud" not in r.text.lower() and "audience" not in r.text.lower()
