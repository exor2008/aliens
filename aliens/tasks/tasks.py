from typing import Optional
from functools import wraps
from abc import ABC, abstractmethod

import simpy
import numpy as np
from tcod.path import AStar

from aliens.items import Item


class Task(ABC):
    def __init__(self, item: Item, priority: int, preempt: bool = False):
        self.item = item
        self.world = item.world
        self.env = item.env
        self.priority = priority
        self.preempt = preempt        
        self.actor = item.actor.actor

    @abstractmethod
    def execute(self):
        pass


class GoToTask(Task):
    def __init__(self, item: Item, target_x: int, target_y: int, 
        priority, preempt: bool = True, path: Optional[np.ndarray] = None):

        super().__init__(item, priority, preempt)
        self.target_x = target_x
        self.target_y = target_y
        self._path = path

    def execute(self):
        with self.actor.request(priority=self.priority, preempt=self.preempt) as req:
            try:
                yield req
                current_x, current_y = self.item.position.pos

                while (self.target_x, self.target_y) != (current_x, current_y):
                    for current_x, current_y in self.next_dest():
                        yield self.env.process(
                            MoveTask(self.item, current_x, current_y).execute())

            except UnreachableDestination:
                return False
            except simpy.Interrupt as interrupt:
                return False
            else:
                return True

    @property
    def path(self):
        if self._path is None:
            astar = AStar(self.world.walk_mask, diagonal=1.41)
            _path = astar.get_path(
                self.item.position.x,
                self.item.position.y,
                self.target_x,
                self.target_y)
            self._path = np.asarray(_path)
            if self._path.size == 0:
                raise UnreachableDestination(
                    self.item.position.x, self.item.position.y)
        return self._path

    def next_dest(self):
        for x, y in self.path:
            if self.world.cells[x, y].is_block_pass():
                self._path = None
                return
            else:
                yield x, y


class IdleTask(Task):
    def execute(self):
        with self.actor.request(priority=self.priority, preempt=self.preempt) as req:
            try:
                yield req
                while True:
                    yield self.env.timeout(100.0)
            except simpy.Interrupt as interrupt:
                self.env.process(self.execute())


class MoveTask(Task):
    def __init__(self, item: Item, target_x: int, target_y: int, priority: int = 10, preempt: bool = True):
        super().__init__(item, priority, preempt)
        self.target_x = target_x
        self.target_y = target_y

    def execute(self):
        try:
            yield self.env.timeout(1 / self.item.navigate.speed)
            self.item.position.move(self.target_x, self.target_y)
        except simpy.Interrupt:
            pass


class UnreachableDestination(Exception):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"[{self.x} {self.y}] is unreachable destination"