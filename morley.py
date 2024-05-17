#!/usr/bin/env python3
from math import atan2, cos, pi, sin, tan
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


class Node:
    def __init__(self, x: int, y: int, size: int = NODE_SIZE) -> None:
        self.x = x
        self.y = y
        self.size = size
        self.grab_offset: None | Tuple[int, int] = None

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect([self.x, self.y, self.size, self.size])

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.get_rect().collidepoint(event.pos):
                self.grab_offset = (event.pos[0] - self.x, event.pos[1] - self.y)
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.grab_offset = None
            return False

        return False

    def update(self) -> None:
        if self.grab_offset is not None:
            mouse_pos = pygame.mouse.get_pos()
            self.x = mouse_pos[0] - self.grab_offset[0]
            self.y = mouse_pos[1] - self.grab_offset[1]

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(
            screen, BLACK, self.get_rect(), 1 if self.grab_offset is None else 0
        )


class Triangle:
    def __init__(self) -> None:
        self.nodes = [
            Node(100, 100),
            Node(200, 200),
            Node(200, 100),
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
            pygame.draw.line(screen, BLACK, (node1.x, node1.y), (node2.x, node2.y))

        self.draw_trisectors(screen)

        for node in self.nodes:
            node.draw(screen)

    def draw_trisectors(self, screen: pygame.Surface) -> None:
        thirds = []
        for i, node in enumerate(self.nodes):
            left = self.nodes[(i - 1) % len(self.nodes)]
            right = self.nodes[(i + 1) % len(self.nodes)]
            angle_left = atan2(left.y - node.y, left.x - node.x)
            angle_right = atan2(right.y - node.y, right.x - node.x)

            # Fix interpolated angle pointing outwards by adding full rotation to negative angle
            if angle_left * angle_right < 0 and abs(angle_left) + abs(angle_right) > pi:
                if angle_left < 0:
                    angle_left += 2 * pi
                else:
                    angle_right += 2 * pi

            onethird = (2 / 3) * angle_left + (1 / 3) * angle_right
            twothirds = (1 / 3) * angle_left + (2 / 3) * angle_right
            thirds.append([onethird, twothirds])

        intersections_maybe: List[Tuple[int, int] | None] = []
        for i in range(len(self.nodes)):
            next_i = (i + 1) % 3
            this_node = self.nodes[i]
            next_node = self.nodes[next_i]
            inter = get_intersection(
                (this_node.x, this_node.y),
                thirds[i][1],
                (next_node.x, next_node.y),
                thirds[next_i][0],
            )
            intersections_maybe.append(inter)

        if all(point is not None for point in intersections_maybe):
            intersections = cast(List[Tuple[int, int]], intersections_maybe)

            pygame.draw.polygon(screen, YELLOW, intersections)
            pygame.draw.polygon(screen, BLACK, intersections, 1)

            for outer1, inner, outer2 in zip(
                self.nodes, intersections, rotate(self.nodes)
            ):
                points = [
                    (outer1.x, outer1.y),
                    inner,
                    (outer2.x, outer2.y),
                ]
                pygame.draw.polygon(screen, RED, points)
                pygame.draw.polygon(screen, BLACK, points, 1)


def get_polar(base: Tuple[int, int], angle: float, length: float):
    return (base[0] + cos(angle) * length, base[1] + sin(angle) * length)


def get_intersection(
    base1: Tuple[int, int], angle1: float, base2: Tuple[int, int], angle2: float
) -> Optional[Tuple[int, int]]:
    if angle1 == angle2:
        return None

    tan1 = tan(angle1)
    tan2 = tan(angle2)

    (x1, y1) = base1
    (x2, y2) = base2

    x = (y1 - y2 + x2 * tan2 - x1 * tan1) / (tan2 - tan1)

    return int(x), int(y1 + tan1 * (x - x1))


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
