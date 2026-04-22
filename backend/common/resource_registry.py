from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceAction:
    resource_type: str
    action: str
    primary_resource: str
    related_resources: tuple[str, ...] = ()


class ResourceRegistry:
    def __init__(self):
        self._mapping: dict[tuple[str, str], ResourceAction] = {}

    def register(self, path_pattern: str, method: str, action: ResourceAction) -> None:
        normalized_path = path_pattern.strip()
        normalized_method = method.strip().upper()
        self._mapping[(normalized_path, normalized_method)] = action

    def resolve(self, path_pattern: str, method: str) -> ResourceAction | None:
        normalized_path = path_pattern.strip()
        normalized_method = method.strip().upper()
        return self._mapping.get((normalized_path, normalized_method))

    def list_registered_keys(self) -> list[tuple[str, str]]:
        return sorted(self._mapping.keys())

    def find_unregistered(
        self, candidates: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        unknown: list[tuple[str, str]] = []
        for path_pattern, method in candidates:
            key = (path_pattern.strip(), method.strip().upper())
            if key not in self._mapping:
                unknown.append(key)
        return sorted(unknown)
