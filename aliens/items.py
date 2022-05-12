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
        self.name = '_'.join([self.name, uuid.uuid4().hex[:5]])

    def add_item(self, item):
        self.items.append(item)
        item.owner = self
        if hasattr(self, 'position') and hasattr(item, 'position'):
            item.position.move(*self.position.pos)
        if hasattr(item, 'render'):
            item.render.visible = False

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
