from dataclasses import dataclass


@dataclass(frozen=True)  # frozen=True makes it immutable like a Java record
class PredictionResult:
    class_id: int
    label: str
    probability: str