from __future__ import annotations

import hashlib


_P = 2**255 - 19
_Q = 2**252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_I = pow(2, (_P - 1) // 4, _P)
_IDENTITY = (0, 1)


def verify_ed25519_signature(public_key: bytes, signature: bytes, message: bytes) -> bool:
    try:
        public_key = bytes(public_key)
        signature = bytes(signature)
        message = bytes(message)
        if len(public_key) != 32 or len(signature) != 64:
            return False

        r_encoded = signature[:32]
        s = int.from_bytes(signature[32:], "little")
        if s >= _Q:
            return False

        public_point = _decode_point(public_key)
        r_point = _decode_point(r_encoded)
        h = int.from_bytes(hashlib.sha512(r_encoded + public_key + message).digest(), "little") % _Q

        left = _scalarmult(_BASE_POINT, s)
        right = _edwards_add(r_point, _scalarmult(public_point, h))
        return _encode_point(left) == _encode_point(right)
    except Exception:
        return False


def _inv(x: int) -> int:
    return pow(x, _P - 2, _P)


def _recover_x(y: int) -> int:
    xx = ((y * y - 1) * _inv(_D * y * y + 1)) % _P
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P != 0:
        x = (x * _I) % _P
    if x & 1:
        x = _P - x
    return x


def _is_on_curve(point: tuple[int, int]) -> bool:
    x, y = point
    return (-x * x + y * y - 1 - _D * x * x * y * y) % _P == 0


def _decode_point(encoded: bytes) -> tuple[int, int]:
    y = int.from_bytes(encoded, "little") & ((1 << 255) - 1)
    sign = encoded[31] >> 7
    if y >= _P:
        raise ValueError("bad Ed25519 point")
    x = _recover_x(y)
    if (x & 1) != sign:
        x = _P - x
    point = (x, y)
    if not _is_on_curve(point):
        raise ValueError("bad Ed25519 point")
    return point


def _encode_point(point: tuple[int, int]) -> bytes:
    x, y = point
    encoded = bytearray((y % _P).to_bytes(32, "little"))
    encoded[31] |= (x & 1) << 7
    return bytes(encoded)


def _edwards_add(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
    x1, y1 = left
    x2, y2 = right
    xyxy = x1 * x2 * y1 * y2
    x3 = ((x1 * y2 + x2 * y1) * _inv(1 + _D * xyxy)) % _P
    y3 = ((y1 * y2 + x1 * x2) * _inv(1 - _D * xyxy)) % _P
    return x3, y3


def _scalarmult(point: tuple[int, int], scalar: int) -> tuple[int, int]:
    result = _IDENTITY
    addend = point
    scalar = int(scalar)
    while scalar > 0:
        if scalar & 1:
            result = _edwards_add(result, addend)
        addend = _edwards_add(addend, addend)
        scalar >>= 1
    return result


_BASE_POINT = (_recover_x(4 * _inv(5) % _P), 4 * _inv(5) % _P)


__all__ = ["verify_ed25519_signature"]
