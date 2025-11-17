"""QKD 네트워크 라우팅 알고리즘 모음.

baseline_route: 거리 기반 최단 경로.
crosslayer_route: 거리 + 가용성 가중 혼합.
rl_route: 간단한 Q-learning을 통한 경로 탐색(교육용, 소규모 그래프 전제).
"""
from __future__ import annotations
import math
import random
from typing import List, Tuple, Dict, Any
import networkx as nx

# ----------------------------- 기본/크로스레이어 라우팅 ----------------------------- #

def baseline_route(G: nx.Graph, src: str, dst: str) -> List[str]:
    """길이(length_km) 가중 최단 경로."""
    return nx.shortest_path(G, src, dst, weight="length_km")


def crosslayer_route(G: nx.Graph, src: str, dst: str) -> List[str]:
    """거리 + (1-가용성) 가중 결합.
    낮은 availability(불안정 링크)에 패널티를 부여해 우회하도록 유도.
    weight = length_km * (1 + (1 - availability))
    """
    def weight(u: str, v: str, data: Dict[str, Any]) -> float:
        length = data.get("length_km", 1.0)
        availability = data.get("availability", 0.95)
        return length * (1.0 + (1.0 - availability))
    return nx.shortest_path(G, src, dst, weight=weight)

# ----------------------------- 간단한 RL 라우팅 ----------------------------- #

class RLAgent:
    """아주 단순한 Q-learning 기반 경로 탐색.

    상태: 현재 노드
    행동: 인접 노드로 이동
    보상: -length_km + availability * 0.5 (도착 시 추가 +5)
    """
    def __init__(self, G: nx.Graph, src: str, dst: str, alpha: float = 0.3, gamma: float = 0.9):
        self.G = G
        self.src = src
        self.dst = dst
        self.alpha = alpha
        self.gamma = gamma
        self.Q: Dict[Tuple[str, str], float] = {}

    def _reward(self, u: str, v: str) -> float:
        data = self.G.get_edge_data(u, v)
        if not data:
            return -10.0
        length = data.get("length_km", 1.0)
        availability = data.get("availability", 0.95)
        r = -length + availability * 0.5
        if v == self.dst:
            r += 5.0
        return r

    def choose_action(self, state: str, epsilon: float) -> str:
        neighbors = list(self.G.neighbors(state))
        if not neighbors:
            return state
        if random.random() < epsilon:
            return random.choice(neighbors)
        # exploit
        best_v = neighbors[0]
        best_q = self.Q.get((state, best_v), 0.0)
        for v in neighbors[1:]:
            q = self.Q.get((state, v), 0.0)
            if q > best_q:
                best_q = q
                best_v = v
        return best_v

    def train(self, episodes: int = 300, max_steps: int = 20) -> None:
        for ep in range(episodes):
            state = self.src
            epsilon = max(0.05, 1.0 - ep / episodes)  # 선형 감소 탐욕
            for _ in range(max_steps):
                if state == self.dst:
                    break
                action = self.choose_action(state, epsilon)
                reward = self._reward(state, action)
                # 다음 상태의 최대 Q
                next_neighbors = list(self.G.neighbors(action))
                max_next_q = 0.0
                if next_neighbors:
                    max_next_q = max(self.Q.get((action, vv), 0.0) for vv in next_neighbors)
                old_q = self.Q.get((state, action), 0.0)
                new_q = old_q + self.alpha * (reward + self.gamma * max_next_q - old_q)
                self.Q[(state, action)] = new_q
                state = action

    def best_path(self) -> List[str]:
        path = [self.src]
        state = self.src
        visited = set([state])
        for _ in range(30):
            if state == self.dst:
                break
            neighbors = list(self.G.neighbors(state))
            if not neighbors:
                break
            # greedy 선택
            best_v = None
            best_q = -math.inf
            for v in neighbors:
                q = self.Q.get((state, v), 0.0)
                if q > best_q and v not in visited:
                    best_q = q
                    best_v = v
            if best_v is None:  # 모두 방문했거나 Q 동일 → 탈출
                break
            path.append(best_v)
            visited.add(best_v)
            state = best_v
        if path[-1] != self.dst:
            # 실패 시 fallback 최단 경로
            try:
                return baseline_route(self.G, self.src, self.dst)
            except Exception:
                return path
        return path


def rl_route(G: nx.Graph, src: str, dst: str, episodes: int = 300) -> List[str]:
    agent = RLAgent(G, src, dst)
    agent.train(episodes=episodes)
    return agent.best_path()

__all__ = ["baseline_route", "crosslayer_route", "rl_route", "RLAgent"]
