import math
import time
from collections import deque
from argparse import ArgumentParser
from enum import Enum
from subprocess import Popen, PIPE, STDOUT
from random import random


class Passenger:
    def __init__(self, go: int):
        self.go = go
        self.waiting = True
        self.car = None

    def land(self, car: 'Carriage'):
        self.car = car
        self.waiting = False


class CarriageState(Enum):
    IDLE = 0
    UP = 1
    DOWN = 2
    FORCE_AUTONOMA = 3


class Carriage:
    def __init__(self, num: int, game: 'Game', capacity: int = 20):
        self.num = num
        self.floor = 0
        self.state = CarriageState.IDLE
        self.passengers = deque[Passenger]()
        self.capacity = capacity
        self.__game = game

    @property
    def riders(self):
        return len(self.passengers)

    @property
    def empty(self):
        return self.riders <= 0

    @property
    def full(self):
        return self.riders >= self.capacity

    def __get_next_floor(self):
        if self.state == CarriageState.UP:
            return self.floor + 1
        elif self.state == CarriageState.DOWN:
            return self.floor - 1
        else:
            return self.floor

    def __take_passengers(self):
        target = self.__game.floors[self.floor]
        free_space = self.capacity - self.riders
        while free_space > 0:
            comer = target.passengers.popleft()
            self.passengers.append(comer)
            comer.land(self)
            free_space -= 1

    def __get_next_state(self, floor: 'Floor'):
        if floor.num < self.num:
            return CarriageState.DOWN
        elif floor.num > self.num:
            return CarriageState.UP
        else:
            return CarriageState.IDLE

    def tick(self):
        if self.empty and self.state != CarriageState.FORCE_AUTONOMA:
            self.floor = self.__get_next_floor()
            # player can implicitly push the car to autonoma mode
            # when it's at the edge
            if self.floor < 0 or self.floor > len(self.__game.floors):
                self.floor = 0 if self.floor < 0 else len(self.__game.floors) - 1
                self.state = CarriageState.FORCE_AUTONOMA
        elif self.empty and self.state == CarriageState.FORCE_AUTONOMA:
            targetable_floors = filter(lambda f: f.waiting > 0, self.__game.floors)
            self.__take_passengers()
            if len(targetable_floors) > 0:
                target = min(targetable_floors, key=lambda f: abs(f.num - self.num))
                self.state = self.__get_next_state(target)
                self.floor = self.__get_next_floor()
            else:
                self.state = CarriageState.IDLE
        elif not self.empty:
            arrived = list(filter(lambda p: p.go == self.floor, self.passengers))
            for a in arrived:
                self.passengers.remove(a)
                a.land(None)

            self.__take_passengers()

            elevation = (passenger.go - self.floor for passenger in self.passengers)
            up_volts = sum(map(lambda go: 1 / go if go > 0 else 0, elevation))
            down_volts = sum(map(lambda go: -1 / go if go < 0 else 0, elevation))
            if up_volts > down_volts:
                self.state = CarriageState.UP
            else:
                self.state = CarriageState.DOWN


class Floor:
    def __init__(self, num: int, game: 'Game', popularity: int):
        self.num = num
        self.passengers = deque[Passenger]()
        self.unhappiness = 0
        self.popularity = popularity
        self.__game = game
        self.__luck = 0

    @property
    def waiting(self):
        return len(self.passengers)

    def tick(self):
        self.unhappiness += self.waiting
        self.__luck += random() * self.popularity / 60
        comers = round(self.__luck)
        if comers > 0:
            self.__luck = 0
            for i in range(comers):
                self.passengers.append(Passenger(math.ceil((random() * len(self.__game.floors)))))


class Scheduler:
    def __init__(self, game: 'Game', **kwargs):
        self._game = game

    def tick(self):
        pass


class StdIOScheduler(Scheduler):
    def __init__(self, executable: str, game: 'Game'):
        super().__init__(game)
        self.process = Popen(executable, text=True, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        self.__writelines(('N',))

    def __writelines(self, lines):
        for line in lines:
            self.process.stdin.write(f'{line}\n')
        self.process.stdin.flush()

    def tick(self):
        for floor in self._game.floors:
            ups = sum(1 for _ in filter(lambda p: p.go > floor.num, floor.passengers))
            downs = sum(1 for _ in filter(lambda p: p.go < floor.num, floor.passengers))
            has_up = '1' if ups > 0 else '0'
            has_down = '1' if downs else '0'
            self.__writelines([has_up, has_down, str(ups), str(downs)])  # buttons

        for car in self._game.cars:
            pressed = list('0' for _ in range(len(self._game.floors)))
            for p in car.passengers:
                pressed[p.go] = '1'

            self.__writelines([
                f'{1 if car.empty and car.state != CarriageState.FORCE_AUTONOMA else 0}{0 if car.state == CarriageState.DOWN else 1 if car.state == CarriageState.UP else 2}',
                f'{car.floor}',
                f'{1 if car.full else 0}',
                "".join(pressed)
            ])  # elevators

        sc = self.process.stdout.readline().split()
        for i, car in enumerate(self._game.cars):
            car.state = CarriageState.IDLE if sc[i] == 'S' else CarriageState.UP if sc[i] == 'U' else CarriageState.DOWN


class Game:
    def __init__(self, cars: int, floors: int, scheduler: type[Scheduler], **kwargs):
        self.floors = list(Floor(i, self, math.ceil(math.e ** (3 - i))) for i in range(floors))
        self.cars = list(Carriage(i, self) for i in range(cars))
        self.scheduler = scheduler(game=self, **kwargs)

    def tick(self):
        self.scheduler.tick()
        for car in self.cars:
            car.tick()
        for floor in self.floors:
            floor.tick()

    @property
    def unhappiness(self):
        return sum(floor.unhappiness for floor in self.floors)


def main(executable: str):
    game = Game(cars=5, floors=6, scheduler=StdIOScheduler, executable=executable)
    for i in range(600):
        print(f'tick#{i}: {" ".join(str(len(f.passengers)) for f in game.floors)}')
        game.tick()

    print(f'unhappiness: {game.unhappiness}')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('exec')
    args = parser.parse_args()
    main(args.exec)
