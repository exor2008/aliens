import uuid
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass, field


@dataclass
class Item:
    name: str
    world: 'World'
    env: 'simpy.Environment'
    items: List['Item'] = field(default_factory=list)
    owner: 'Item' = None

    def add_component(self, Component, *args, **kwargs):
        name = Component.__name__.replace('Component', '').lower()
        setattr(self, name, Component(self, *args, **kwargs))

    def __post_init__(self):
        self.name = self.name + uuid.uuid4().hex[:5]