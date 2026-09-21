from dataclasses import dataclass, field


@dataclass(frozen=True)
class BasicProfileInput:
    display_name: str


@dataclass(frozen=True)
class PreferenceInput:
    styles: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    colors: tuple[str, ...] = ()
    occasions: tuple[str, ...] = ()
    fit_preferences: tuple[str, ...] = ()
    shopping_preferences: tuple[str, ...] = ()
    discovery_preferences: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextInput:
    region: str | None = None


@dataclass(frozen=True)
class UserContext:
    user_id: str
    region: str | None
    styles: tuple[str, ...] = field(default_factory=tuple)
    categories: tuple[str, ...] = field(default_factory=tuple)
    colors: tuple[str, ...] = field(default_factory=tuple)
