from time import monotonic
from simpy.rt import RealtimeEnvironment


class StoppableRealtimeEnvironment(RealtimeEnvironment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_time = None
        self.is_stopped = False
        self.process(self.tick(.1))

    def stop(self) -> None:
        self.stop_time = monotonic()
        self.is_stopped = True

    def resume(self):
        self.real_start += monotonic() - self.stop_time
        self.is_stopped = False

    def step(self):
        if self.is_stopped:
            return

        super().step()

    def tick(self, delay):
        while True:
            yield self.timeout(delay)