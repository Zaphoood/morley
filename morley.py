#!/usr/bin/env python3
from dataclasses import dataclass
from math import atan2, pi, tan
from typing import List, Optional, Tuple, TypeVar, cast

import pygame

WHITE = [255, 255, 255]
YELLOW = [255, 255, 0]
RED = [255, 0, 0]
BLACK = [0, 0, 0]

NODE_SIZE = 16


T = TypeVar("T")


def rotate(a: List[T], n: int = 1) -> List[T]:
    if len(a) == 0:
        return a

    m = n % len(a)

    return [*a[m:], *a[:m]]


@dataclass
class Point:
    x: int
    y: int

    def to_tuple(self) -> Tuple[int, int]:
        return self.x, self.y

    @classmethod
    def from_tuple(cls, t: Tuple[int, int]) -> "Point":
        return cls(t[0], t[1])

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __neg__(self) -> "Point":
        return Point(-self.x, -self.y)

    def __sub__(self, other: "Point") -> "Point":
        return self + (-other)


class Node:
    def __init__(self, x: int, y: int, size: int = NODE_SIZE) -> None:
        self.top_left = Point(x, y)
        self.size = size
        self.grab_offset: None | Point = None

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect([self.x, self.y, self.size, self.size])

    @property
    def x(self) -> int:
        return self.top_left.x

    @property
    def y(self) -> int:
        return self.top_left.y

    @property
    def center(self) -> Point:
        return Point(
            int(self.x + self.size / 2),
            int(self.y + self.size / 2),
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.get_rect().collidepoint(event.pos):
                self.grab_offset = Point.from_tuple(event.pos) - self.top_left
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.grab_offset = None
            return False

        return False

    def update(self) -> None:
        if self.grab_offset is not None:
            mouse_pos = pygame.mouse.get_pos()
            self.top_left = Point.from_tuple(mouse_pos) - self.grab_offset

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(
            screen, BLACK, self.get_rect(), 1 if self.grab_offset is None else 0
        )


class Triangle:
    def __init__(self) -> None:
        self.nodes = [
            Node(300, 100),
            Node(700, 400),
            Node(100, 400),
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        for node in self.nodes:
            consumed = node.handle_event(event)
            if consumed:
                break

    def update(self) -> None:
        for node in self.nodes:
            node.update()

    def draw(self, screen: pygame.Surface) -> None:
        for node1, node2 in zip(self.nodes, rotate(self.nodes)):
            pygame.draw.line(
                screen,
                BLACK,
                (node1.center.x, node1.center.y),
                (node2.center.x, node2.center.y),
            )

        self.draw_trisectors(screen)

        for node in self.nodes:
            node.draw(screen)

    def draw_trisectors(self, screen: pygame.Surface) -> None:
        thirds = []
        for i, node in enumerate(self.nodes):
            left = self.nodes[(i - 1) % len(self.nodes)]
            right = self.nodes[(i + 1) % len(self.nodes)]
            angle_left = atan2(
                left.center.y - node.center.y, left.center.x - node.center.x
            )
            angle_right = atan2(
                right.center.y - node.center.y, right.center.x - node.center.x
            )

            # Fix interpolated angle pointing outwards by adding full rotation to negative angle
            if angle_left * angle_right < 0 and abs(angle_left) + abs(angle_right) > pi:
                if angle_left < 0:
                    angle_left += 2 * pi
                else:
                    angle_right += 2 * pi

            onethird = (2 / 3) * angle_left + (1 / 3) * angle_right
            twothirds = (1 / 3) * angle_left + (2 / 3) * angle_right
            thirds.append([onethird, twothirds])

        intersections_maybe: List[Point | None] = []
        for i in range(len(self.nodes)):
            next_i = (i + 1) % 3
            this_node = self.nodes[i]
            next_node = self.nodes[next_i]
            inter = get_intersection(
                this_node.center,
                thirds[i][1],
                next_node.center,
                thirds[next_i][0],
            )
            intersections_maybe.append(inter)

        if all(point is not None for point in intersections_maybe):
            intersections = cast(List[Point], intersections_maybe)

            pygame.draw.polygon(
                screen, YELLOW, [inter.to_tuple() for inter in intersections]
            )
            pygame.draw.polygon(
                screen, BLACK, [inter.to_tuple() for inter in intersections], 1
            )

            for outer1, inner, outer2 in zip(
                self.nodes, intersections, rotate(self.nodes)
            ):
                points = [
                    outer1.center.to_tuple(),
                    inner.to_tuple(),
                    outer2.center.to_tuple(),
                ]
                pygame.draw.polygon(screen, RED, points)
                pygame.draw.polygon(screen, BLACK, points, 1)


def get_intersection(
    p1: Point, angle1: float, p2: Point, angle2: float
) -> Optional[Point]:
    if angle1 == angle2:
        return None

    tan1 = tan(angle1)
    tan2 = tan(angle2)

    x = (p1.y - p2.y + p2.x * tan2 - p1.x * tan1) / (tan2 - tan1)

    return Point(int(x), int(p1.y + tan1 * (x - p1.x)))


class App:
    def __init__(self) -> None:
        self.triangle = Triangle()

    def update(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            self.triangle.handle_event(event)

        self.triangle.update()

        return True

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(WHITE)
        self.triangle.draw(screen)


def main():
    pygame.init()
    screen = pygame.display.set_mode([800, 600])
    pygame.display.set_caption("Morley's trisector theorem")
    app = App()
    clock = pygame.time.Clock()

    while True:
        if not app.update():
            break
        clock.tick(60)
        app.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
