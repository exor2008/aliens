import numpy as np

from aliens.tasks import Task, GoToTask, MoveTask


class CollectResourceTask(Task):
    def execute(self):
        pass


class RoamTask(Task):
    def execute(self):
        try:
            return self.env.process(MoveTask(*self.next_dest()).execute())
        except simpy.Interrupt:
            pass

    def next_dest(self):
        if np.random.rand() >= 0.75:
            if np.random.rand() >= 0.5:
                self.item.direction.turn_cw()
            else:
                self.item.direction.turn_ccw()

        off_x, off_y = *self.item.direction.cell_offsets
        x, y = *self.item.position.pos

        if self.world.is_block_pass(x + off_x, y + off_y):
            if np.random.rand() >= 0.5:
                turn_f = self.item.direction.turn_cw
            else:
                turn_f = self.item.direction.turn_ccw

            for i in range(len(self.item.direction.directions)):
                turn_f()
                off_x, off_y = *self.item.direction.cell_offsets
                if not self.world.is_block_pass(x + off_x, y + off_y):
                    break

        return x + off_x, y + off_y


class SearchResourceTask(Task):
    def execute(self):
        pass


class GoToResourceTask(Task):
    def execute(self):
        pass


class PickUpResourceTask(Task):
    def execute(self):
        pass


class BringResourceToHiveTask(Task):
    def execute(self):
        pass


class DropResourceToHiveTask(Task):
    def execute(self):
        pass


class SearchForEnemiesTask(Task):
    def execute(self):
        pass


class FleeTask(Task):
    def execute(self):
        pass