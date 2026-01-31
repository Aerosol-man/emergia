# backend/services/collision_response.py
import math

EPS = 1e-6

def _collision_normal(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    dist = math.hypot(dx, dy)
    if dist < EPS:
        return 0.0, 0.0, 0.0
    return dx / dist, dy / dist, dist


def _separate_positions(a, b, penetration):
    """
    Push agents apart so they no longer overlap.
    Each agent moves half the penetration distance.
    """
    nx, ny, _ = _collision_normal(a, b)
    if nx == 0 and ny == 0:
        return

    correction = penetration * 0.5
    a.x += nx * correction
    a.y += ny * correction
    b.x -= nx * correction
    b.y -= ny * correction


def apply_soft_separation(a, b, radius, strength=100):
    nx, ny, dist = _collision_normal(a, b)
    if dist <= 0:
        return

    penetration = max(0.0, radius - dist)
    _separate_positions(a, b, penetration)

    a.vx += nx * strength
    a.vy += ny * strength
    b.vx -= nx * strength
    b.vy -= ny * strength


def apply_neutral_bounce(a, b, radius, strength=2.0):
    nx, ny, dist = _collision_normal(a, b)
    if dist <= 0:
        return

    penetration = max(0.0, radius - dist)
    _separate_positions(a, b, penetration)

    a.vx += nx * strength
    a.vy += ny * strength
    b.vx -= nx * strength
    b.vy -= ny * strength


def apply_hard_bounce(a, b, radius, strength=6.0):
    nx, ny, dist = _collision_normal(a, b)
    if dist <= 0:
        return

    penetration = max(0.0, radius - dist)
    _separate_positions(a, b, penetration)

    a.vx += nx * strength
    a.vy += ny * strength
    b.vx -= nx * strength
    b.vy -= ny * strength
