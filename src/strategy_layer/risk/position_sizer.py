from dataclasses import dataclass


@dataclass(frozen=True)
class PositionSizer:
    fractional_kelly: float = 0.5
    max_position: float = 1.0

    def __post_init__(self):
        if not 0 < self.fractional_kelly <= 1 or self.max_position <= 0:
            raise ValueError("fractional_kelly muss in (0, 1] liegen.")

    def kelly(self, win_probability: float, win_loss_ratio: float) -> float:
        if not 0 <= win_probability <= 1 or win_loss_ratio <= 0:
            raise ValueError("Ungültige Kelly-Parameter.")
        raw = win_probability - (1 - win_probability) / win_loss_ratio
        return min(self.max_position, max(0.0, raw * self.fractional_kelly))
