import simpy
import numpy as np
import logging

from tcod.path import AStar

from aliens.logging_helper import get_logger
from aliens.tasks.tasks import Task, GoToTask, MoveTask

INTERACT_RESOURCE_TIME = .5

logger = get_logger('aliens.tasks.alien_drone', logging.DEBUG)


class CollectResourceTask(Task):
    def execute(self):
        logger.debug('CollectResourceTask begins')

        try:
            while True:
                roaming = self.env.process(RoamTask(self.item, 10).execute())
                searching = self.env.process(SearchResourceTask(self.item, 10).execute())
                resources = yield searching

                if resources:
                    roaming.interrupt('Resources found')
                else:
                    continue

                reached = yield self.env.process(GoToResourceTask(self.item, resources, 10).execute())
                if not reached:
                    continue

                pickedup = yield self.env.process(PickUpResourceTask(self.item, 10).execute())
                if not pickedup:
                    continue

                yield self.env.process(BringResourceToHiveTask(self.item, 10).execute())
                yield self.env.process(DropResourceToHiveTask(self.item, 10).execute())
        except simpy.Interrupt:
            pass
        logger.debug('CollectResourceTask ends')


class RoamTask(Task):
    def execute(self):
        logger.debug('RoamTask begins')        
        try:
            while True:
                yield self.env.process(MoveTask(self.item, *self.next_dest()).execute())
        except simpy.Interrupt:
            logger.debug('RoamTask interrupted')  
        logger.debug('RoamTask begins')            

    def next_dest(self):
        if np.random.rand() >= 0.75:
            if np.random.rand() >= 0.5:
                self.item.direction.turn_cw()
            else:
                self.item.direction.turn_ccw()

        off_x, off_y = self.item.direction.cell_in_front
        x, y = self.item.position.pos

        if self.world.is_block_pass(x + off_x, y + off_y):
            if np.random.rand() >= 0.5:
                turn_f = self.item.direction.turn_cw
            else:
                turn_f = self.item.direction.turn_ccw

            for i in range(len(self.item.direction.directions)):
                turn_f()
                off_x, off_y = self.item.direction.cell_in_front
                if not self.world.is_block_pass(x + off_x, y + off_y):
                    break

        return x + off_x, y + off_y


class SearchResourceTask(Task):
    def execute(self):
        logger.debug('SearchResourceTask begins')
        try:
            while True:
                yield self.env.timeout(1)
                items = self.item.sensor.scan('alienresource')
                if items:
                    logger.debug('Resource found')
                    return items
                logger.debug('Resource not found')
        except simpy.Interrupt:
            pass
        logger.debug('SearchResourceTask ends')


class GoToResourceTask(Task):
    def __init__(self, item, items, priority: int = 10, preempt: bool = False):
        super().__init__(item, priority, preempt)
        self.items = items

    def execute(self):
        logger.debug('GoToResourceTask begins')
        try:
            item, path = self.determine(self.items)
            if path.size != 0:
                yield self.env.process(GoToTask(self.item, *item.position.pos, 10, path=path).execute())
                logger.debug('GoToResourceTask ends Success')
                return True
            else:
                logger.debug('GoToResourceTask ends Fail')
                return False
        except simpy.Interrupt:
            logger.debug('GoToResourceTask interrupted')

    def determine(self, items):
        for item in items:
            astar = AStar(self.world.walk_mask, diagonal=1.41)
            path = np.asarray(
                astar.get_path(
                    self.item.position.x,
                    self.item.position.y,
                    item.position.x,
                    item.position.y))
            return item, path


class PickUpResourceTask(Task):
    def execute(self):
        logger.debug('PickUpResourceTask begins')
        yield self.env.timeout(INTERACT_RESOURCE_TIME)
        items = self.world.get_items_with_component(*self.item.position.pos, 'alienresource')
        if items:
            self.item.aliendrone.pickup_resource(items[0])
            logger.debug('PickUpResourceTask ends Seccess')
            return True
        logger.debug('PickUpResourceTask ends Fail')
        return False


class BringResourceToHiveTask(Task):
    def execute(self):
        logger.debug('BringResourceToHiveTask begins')
        success = False
        x, y = self.item.aliendrone.hive.item.position.pos
        while not success:
            success = yield self.env.process(
                GoToTask(self.item, x, y, priority=10, preempt=True).execute())
            yield self.env.timeout(5)
        logger.debug('BringResourceToHiveTask ends')


class DropResourceToHiveTask(Task):
    def execute(self):
        logger.debug('DropResourceToHiveTask begins')
        yield self.env.timeout(INTERACT_RESOURCE_TIME)
        if item := self.item.aliendrone.resource:
            self.item.aliendrone.hive.mass += item.alienresource.value
            self.item.aliendrone.destroy_resource()
            logger.debug('DropResourceToHiveTask ends')


class SearchForEnemiesTask(Task):
    def execute(self):
        pass


class FleeTask(Task):
    def execute(self):
        pass