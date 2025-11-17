"""QKD 네트워크 경로 시각화 유틸리티."""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")  # 안전한 비표시(back-end)
import matplotlib.pyplot as plt
import networkx as nx
from typing import List


def plot_network_path(G: nx.Graph, path: List[str], outfile: str) -> str:
    """그래프와 선택된 경로를 PNG로 저장.
    반환: 저장된 파일 경로
    """
    pos = {n: (G.nodes[n]["x"], G.nodes[n]["y"]) for n in G.nodes}
    plt.figure(figsize=(6, 4), dpi=120)
    # 전체 그래프
    nx.draw_networkx_nodes(G, pos, node_color="#246", node_size=500)
    nx.draw_networkx_labels(G, pos, font_color="white")
    nx.draw_networkx_edges(G, pos, edge_color="#999")

    # 경로 강조
    if path and len(path) > 1:
        path_edges = list(zip(path[:-1], path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color="red", width=3)

    # 간선 라벨 (길이 km)
    edge_labels = { (u,v): f"{d.get('length_km',0):.2f}km" for u,v,d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    plt.title("QKD Network Path")
    plt.tight_layout()
    plt.savefig(outfile)
    plt.close()
    return outfile

__all__ = ["plot_network_path"]
