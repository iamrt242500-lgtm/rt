"""QKD 네트워크 토폴로지 모델.

기본(default_topology)은 소규모 교육용 그래프로 노드간 물리 길이(km), 감쇠(dB), 가용성(availability)
등의 속성을 포함한다.
"""
from __future__ import annotations
import math
import random
import networkx as nx

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


def _attenuation_db(length_km: float, fiber_db_per_km: float = 0.2) -> float:
    """간단한 광섬유 감쇠 모델 (dB)."""
    return round(length_km * fiber_db_per_km, 3)


def default_topology() -> nx.Graph:
    """학습용 기본 토폴로지 그래프를 생성한다.

    노드: A,B,C,D,E,F
    위치(임의 배치)를 통해 노드간 유클리드 거리로 링크 길이를 계산하고, 감쇠 및 가용성 값을 부여한다.
    """
    G = nx.Graph()
    # 고정 좌표 (x,y km 단위 가정)
    coords = {
        "A": (0, 0),
        "B": (3, 1),
        "C": (6, 0.5),
        "D": (2.5, 4),
        "E": (5.5, 3.5),
        "F": (8, 2),
    }
    for n, (x, y) in coords.items():
        G.add_node(n, x=x, y=y)

    def add_link(u: str, v: str):
        x1, y1 = coords[u]
        x2, y2 = coords[v]
        length = math.hypot(x2 - x1, y2 - y1)
        length_km = round(length, 3)
        attenuation = _attenuation_db(length_km)
        # 가용성: 0.90~0.99 범위 임의
        availability = round(random.uniform(0.90, 0.99), 3)
        G.add_edge(
            u,
            v,
            length_km=length_km,
            attenuation_db=attenuation,
            availability=availability,
        )

    # 간선 정의 (약간 그물형)
    links = [
        ("A", "B"), ("B", "C"), ("C", "F"),
        ("B", "D"), ("D", "E"), ("E", "F"),
        ("C", "E"), ("A", "D")
    ]
    for u, v in links:
        add_link(u, v)
    return G

__all__ = ["default_topology"]
