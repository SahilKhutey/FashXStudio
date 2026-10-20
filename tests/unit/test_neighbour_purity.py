from __future__ import annotations

import numpy as np


def test_neighbour_purity_perfect_clustering() -> None:
    # 5 items of category 'tops' and 5 items of category 'bottoms'
    cats = ["tops"] * 5 + ["bottoms"] * 5

    # Tops cluster around [1, 0, 0, ...], bottoms cluster around [0, 1, 0, ...]
    vectors = []
    for _ in range(5):
        v = np.zeros(512)
        v[0] = 1.0
        v += np.random.normal(0, 0.05, 512)
        v /= np.linalg.norm(v)
        vectors.append(v)

    for _ in range(5):
        v = np.zeros(512)
        v[1] = 1.0
        v += np.random.normal(0, 0.05, 512)
        v /= np.linalg.norm(v)
        vectors.append(v)

    E = np.array(vectors)
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    S = E @ E.T
    np.fill_diagonal(S, -1.0)
    top = np.argsort(-S, axis=1)[:, :4]

    purity = float(np.mean([[cats[j] == cats[i] for j in top[i]] for i in range(len(cats))]))
    _, counts = np.unique(cats, return_counts=True)
    chance = float(((counts / counts.sum()) ** 2).sum())

    assert purity == 1.0
    assert chance == 0.5
    assert purity > chance
