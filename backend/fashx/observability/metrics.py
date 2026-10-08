from dataclasses import dataclass, field


@dataclass(slots=True)
class Counter:
    name: str
    value: int = 0

    def increment(
        self,
        amount: int = 1,
    ) -> None:
        self.value += amount


@dataclass(slots=True)
class MetricsRegistry:
    counters: dict[str, Counter] = field(default_factory=dict)

    def counter(
        self,
        name: str,
    ) -> Counter:
        if name not in self.counters:
            self.counters[name] = Counter(name=name)
        return self.counters[name]
