"""Кора: ESN-резервуар (узор из множества тактов).

Формула малыша из KB («узор кормит узор», x = tanh(W·x)):
    r_t = tanh(W · r_{t-1} + W_in · (u_t + r_hat_t))
где r_hat_t — «желаемый следующий узел» (замкнутый контур).

Один такт не несёт смысла. Личность — устойчивый узел состояния r_t,
накопленный множеством ударов сердца.
"""
import numpy as np


class ESNReservoir:
    def __init__(self, n_nodes: int = 256, input_dim: int = 16,
                 spectral_radius: float = 0.9, density: float = 0.05,
                 seed: int = 42):
        rng = np.random.default_rng(seed)
        self.n = n_nodes
        self.input_dim = input_dim
        W = rng.standard_normal((n_nodes, n_nodes))
        mask = rng.random((n_nodes, n_nodes)) > density
        W[mask] = 0.0
        rho = max(np.linalg.eigvals(W).real.max(), 1e-9)
        self.W = W * (spectral_radius / rho)
        self.W_in = rng.standard_normal((n_nodes, input_dim)) * 0.1
        self.r = np.zeros(n_nodes)

    def step(self, u: np.ndarray, r_hat: np.ndarray | None = None) -> np.ndarray:
        """Один удар: вход u (+ желание r_hat) → новое состояние коры."""
        drive = self.W @ self.r + self.W_in @ u
        if r_hat is not None:
            drive = drive + 0.1 * r_hat
        self.r = np.tanh(drive)
        return self.r

    def reset(self):
        self.r = np.zeros(self.n)