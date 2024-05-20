import math
import pygame
from pygame.locals import *
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

    def __get_next_floor(self, overflow: bool = False):
        floors = len(self.__game.floors)
        if self.state == CarriageState.UP:
            return self.floor + 1 if self.floor < floors - 1 or overflow else self.floor
        elif self.state == CarriageState.DOWN:
            return self.floor - 1 if self.floor > 0 or overflow else self.floor
        else:
            return self.floor

    def __take_passengers(self):
        target = self.__game.floors[self.floor]
        free_space = self.capacity - self.riders
        while free_space > 0 and len(target.passengers) > 0:
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
        if self.empty and self.state != CarriageState.IDLE:
            self.floor = self.__get_next_floor(overflow=True)
            # player can implicitly push the car to autonoma mode
            # when it's at the edge
            if self.floor < 0 or self.floor >= len(self.__game.floors):
                self.floor = 0 if self.floor < 0 else len(self.__game.floors) - 1
                self.state = CarriageState.IDLE
        elif self.empty and self.state == CarriageState.IDLE:
            targetable_floors = list(filter(lambda f: f.waiting > 0, self.__game.floors))
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

            self.floor = self.__get_next_floor()


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
                go = round((random() * (len(self.__game.floors) - 1)))
                while go == self.num:
                    go = round((random() * (len(self.__game.floors) - 1)))
                self.passengers.append(Passenger(go))


class Scheduler:
    def __init__(self, game: 'Game', **kwargs):
        self._game = game

    def tick(self):
        pass


class FullAutonomaScheduler(Scheduler):
    def __init__(self, game: 'Game'):
        super().__init__(game)

    def tick(self):
        for car in self._game.cars:
            if car.state == CarriageState.IDLE:
                car.state = CarriageState.IDLE
            print(car.num, car.floor, car.state)


class StdIOScheduler(Scheduler):
    def __init__(self, executable: str, game: 'Game'):
        super().__init__(game)
        self.process = Popen(executable, text=True, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        self.writelines(('N',))
        self.__first = False

    def writelines(self, lines):
        for line in lines:
            self.process.stdin.write(f'{line}\n')
        self.process.stdin.flush()

    def tick(self):
        if not self.__first:
            self.__first = True
        else:
            self.writelines(['C'])

        for floor in self._game.floors:
            ups = sum(1 for _ in filter(lambda p: p.go > floor.num, floor.passengers))
            downs = sum(1 for _ in filter(lambda p: p.go < floor.num, floor.passengers))
            has_up = 1 if ups > 0 else 0
            has_down = 1 if downs > 0 else 0
            self.writelines([f'{has_up}{has_down}', str(ups), str(downs)])  # buttons

        for car in self._game.cars:
            pressed = list('0' for _ in range(len(self._game.floors)))
            for p in car.passengers:
                pressed[p.go] = '1'

            occupied = 0 if car.empty and car.state != CarriageState.IDLE else 1
            state = 0 if car.state == CarriageState.DOWN else 1 if car.state == CarriageState.UP else 2
            is_full = 1 if car.full else 0
            self.writelines([
                f'{occupied}{state}',
                f'{car.floor + 1}',
                f'{is_full}',
                "".join(pressed)
            ])  # elevators

        sc = self.process.stdout.readline().split()
        for i, car in enumerate(self._game.cars):
            car.state = CarriageState.IDLE if sc[i] == 'S' else CarriageState.UP if sc[i] == 'U' else CarriageState.DOWN
            print(car.num, car.floor, car.state)


SEPARATOR_X = 200
LINE_WIDTH = 8
BG_COLOR = 0xffffff
LINE_COLOR = 0x0
FLOOR_COLORS = [0xf1184c, 0xfffc40, 0xfaba61, 0xff8172, 0x006fff, 0x3a579a, 0x36244f]
PASSENGER_RADIUS = 10
CAR_COLOR = 0x666666


class Game:
    __display: pygame.Surface
    __font: pygame.font.Font

    def __init__(self, cars: int, floors: int, scheduler: type[Scheduler], **kwargs):
        self.floors = list(Floor(i, self, 100 if i % 2 == 0 else 0) for i in range(floors))
        self.cars = list(Carriage(i, self) for i in range(cars))
        self.scheduler = scheduler(game=self, **kwargs)

        self.fps = 0
        self.size = self.width, self.height = 1280, 720
        self.running = False
        self.iter = 0
        self.speed = 2

    def init(self):
        pygame.init()
        self.__display = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.__font = pygame.font.SysFont(size=32, name=pygame.font.get_default_font())
        self.running = True

    def run_blocking(self, fps: int = 60):
        self.fps = fps
        clock = pygame.time.Clock()
        frame = 0
        while self.running:
            for event in pygame.event.get():
                self.__on_event(event)
            self.__update()
            pygame.display.update()
            if self.speed > 0 and frame % int(fps / self.speed) == 0:
                self.__tick()
            clock.tick(fps)
            frame += 1

    def __tick(self):
        self.scheduler.tick()
        for car in self.cars:
            car.tick()
        for floor in self.floors:
            floor.tick()
        self.iter += 1

    def __update(self):
        dp = self.__display
        dp.fill(BG_COLOR)

        dp.fill(LINE_COLOR, (SEPARATOR_X, 0, LINE_WIDTH, self.height))
        floor_height = self.height / len(self.floors)
        car_height = floor_height
        car_width = (self.width - SEPARATOR_X - LINE_WIDTH) / len(self.cars)
        for i, floor in enumerate(self.floors):
            floor_y = self.height - floor_height * i
            dp.fill(LINE_COLOR, (0, floor_y, SEPARATOR_X, LINE_WIDTH))
            dp.fill(FLOOR_COLORS[i], (0, floor_y - floor_height + LINE_WIDTH, 20, 20))
            if len(floor.passengers) > 0:
                passenger_width = SEPARATOR_X / len(floor.passengers)
                for j, passenger in enumerate(floor.passengers):
                    pygame.draw.circle(dp, FLOOR_COLORS[passenger.go],
                                       (SEPARATOR_X - PASSENGER_RADIUS - passenger_width * j,
                                        floor_y - PASSENGER_RADIUS),
                                       PASSENGER_RADIUS)

        for i, car in enumerate(self.cars):
            car_x = SEPARATOR_X + car_width * i + LINE_WIDTH * 1.5
            car_y = self.height - car_height * (car.floor + 1)
            pygame.draw.rect(dp, CAR_COLOR, (car_x, car_y, car_width - 2 * LINE_WIDTH, car_height), LINE_WIDTH)

            if len(car.passengers) > 0:
                passenger_width = (car_width - 4 * LINE_WIDTH) / len(car.passengers)
                for j, passenger in enumerate(car.passengers):
                    pygame.draw.circle(dp, FLOOR_COLORS[passenger.go],
                                       (car_x + passenger_width * j + PASSENGER_RADIUS + LINE_WIDTH,
                                        car_y + car_height - PASSENGER_RADIUS - LINE_WIDTH),
                                       PASSENGER_RADIUS)

        pygame.display.set_caption(f'speed {self.speed}')

    def __on_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYUP:
            code = event.dict['key']
            print(code)
            if code == 61:
                self.speed = (self.speed + 1) % self.fps
            elif code == 45:
                self.speed = (self.speed - 1) % self.fps

    @property
    def unhappiness(self):
        return sum(floor.unhappiness for floor in self.floors)


def main(executable: str):
    game = Game(cars=5, floors=6, scheduler=StdIOScheduler, executable=executable)
    # game = Game(cars=5, floors=6, scheduler=FullAutonomaScheduler)
    game.init()
    game.run_blocking()

    print(f'iter: {game.iter} unhappiness: {game.unhappiness}')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('exec')
    args = parser.parse_args()
    main(args.exec)
