import sys
import time
import queue
import os
import copy
import pygame
from datetime import datetime
from main import Maze
import random
import logging


EASY = (11, 7)
NORMAL = (31, 17)
HARD = (51, 27)
FULL_VIEW = (15, 9)


# function that finds the shortest path between two given points in the maze
def path_finder(maze_object: Maze, start_pos: tuple, end: str, wall_block: str = "w"):
    maze = maze_object.maze
    q = queue.Queue()
    q.put((start_pos, [start_pos]))
    visited = set()

    while not q.empty():
        current_pos, path = q.get()
        col, row = current_pos

        if maze_object.is_tile(row, col, end):
            return path

        neighbours = find_neighbours(maze, row, col)
        for neighbour in neighbours:
            # removing paths that backtrack or lead to walls
            if neighbour in visited:
                continue
            r, c = neighbour
            if maze[r][c] == wall_block:
                continue

            new_path = path + [neighbour]
            q.put((neighbour, new_path))
            visited.add(neighbour)
    raise ValueError("path not found")


# sub function for the path_finder func
def find_neighbours(maze: list, row: int, col: int):
    neighbours = []
    if row > 0:
        neighbours.append((col, row - 1))
    if row < len(maze[0]) - 1:
        neighbours.append((col, row + 1))
    if col > 0:
        neighbours.append((col - 1, row))
    if col < len(maze) - 1:
        neighbours.append((col + 1, row))

    return neighbours


def main():
    global best_best_easy

    pygame.quit()
    best_best_easy = {"total": 10000}
    best_best_normal = {"total": 10000}
    best_best_full_view = {"total": 10000}
    best_best_hard = {"total": 10000}
    best_easy = {"mode": "easy"}
    best_normal = {"mode": "normal"}
    best_hard = {"mode": "hard"}
    best_full_view = {"mode": "full_view"}
    target_time = int(input("enter target time: "))
    end = time.time() + target_time
    end = datetime.fromtimestamp(end).strftime("%H:%M:%S")
    print(f"finishes at {end}")
    elapsed_time = 0
    while elapsed_time < target_time:
        start_time = time.time()
        seed = random.randint(-sys.maxsize, sys.maxsize)

        rng = random.Random(seed)
        width, height = EASY
        maze = Maze(width, height, rng)
        best_easy["seed"] = seed
        for i in range(5):
            start = maze.start[1], maze.start[0]
            current = 0
            best_easy[i + 1] = 0
            required = len(maze.q_location) // 2
            while current < required:
                path = path_finder(maze, start, "Q")

                y, x = path[-1]
                maze.change_tile(x, y, "c")
                start = (y, x)
                current += 1
                best_easy[i + 1] += len(path)
            path = path_finder(maze, start, "F")
            best_easy[i + 1] += len(path)

            width += 4
            height += 2
            maze = Maze(width, height, rng)
        best_easy["total"] = sum(best_easy[i + 1] for i in range(5))
        if best_easy["total"] < best_best_easy["total"]:
            best_best_easy = copy.deepcopy(best_easy)

        """
        rng = random.Random(seed)
        width, height = NORMAL
        maze = Maze(width, height, rng)
        best_normal["seed"] = seed
        for i in range(5):
            start = maze.start[1], maze.start[0]
            current = 0
            best_normal[i + 1] = 0
            required = len(maze.q_location) // 2
            while current < required:
                path = path_finder(maze, start, "Q")

                y, x = path[-1]
                maze.change_tile(x, y, "c")
                start = (y, x)
                current += 1
                best_normal[i + 1] += len(path)
            path = path_finder(maze, start, "F")
            best_normal[i + 1] += len(path)

            width += 4
            height += 2
            maze = Maze(width, height, rng)
        best_normal["total"] = sum(best_normal[i + 1] for i in range(5))
        if best_normal["total"] < best_best_normal["total"]:
            best_best_normal = copy.deepcopy(best_normal)

        rng = random.Random(seed)
        width, height = HARD
        maze = Maze(width, height, rng)
        best_hard["seed"] = seed
        for i in range(5):
            start = maze.start[1], maze.start[0]
            current = 0
            best_hard[i + 1] = 0
            required = len(maze.q_location) // 2
            while current < required:
                path = path_finder(maze, start, "Q")

                y, x = path[-1]
                maze.change_tile(x, y, "c")
                start = (y, x)
                current += 1
                best_hard[i + 1] += len(path)
            path = path_finder(maze, start, "F")
            best_hard[i + 1] += len(path)

            width += 4
            height += 2
            maze = Maze(width, height, rng)
        best_hard["total"] = sum(best_hard[i + 1] for i in range(5))
        if best_hard["total"] < best_best_hard["total"]:
            best_best_hard = copy.deepcopy(best_hard)

        rng = random.Random(seed)
        width, height = FULL_VIEW
        maze = Maze(width, height, rng)
        best_full_view["seed"] = seed
        for i in range(5):
            start = maze.start[1], maze.start[0]
            current = 0
            best_full_view[i + 1] = 0
            required = len(maze.q_location) // 2
            while current < required:
                path = path_finder(maze, start, "Q")

                y, x = path[-1]
                maze.change_tile(x, y, "c")
                start = (y, x)
                current += 1
                best_full_view[i + 1] += len(path)
            path = path_finder(maze, start, "F")
            best_full_view[i + 1] += len(path)

            width += 12
            height += 6
            maze = Maze(width, height, rng)
        best_full_view["total"] = sum(best_full_view[i + 1] for i in range(5))
        if best_full_view["total"] < best_best_full_view["total"]:
            best_best_full_view = copy.deepcopy(best_full_view)
        """

        end_time = time.time()
        elapsed_time += end_time - start_time

    with open(os.path.join(os.path.dirname(os.path.abspath(os.path.abspath(__file__))), "seeds.txt"),
              "at", encoding="utf-8") as file:
        file.write(str(best_best_easy))
        file.write("\n")
        """
        file.write(str(best_best_normal))
        file.write("\n")
        file.write(str(best_best_hard))
        file.write("\n")
        file.write(str(best_best_full_view))
        file.write("\n")
        """


# logging to file
def logging_setup():
    global logger
    logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), "errors.txt"))
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    logger.addHandler(handler)


# catches exceptions idk, stackoverflow
def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    with open(os.path.join(os.path.dirname(os.path.abspath(os.path.abspath(__file__))), "seeds.txt"),
              "at", encoding="utf-8") as file:
        file.write(str(best_best_easy))
        file.write("\n")


if __name__ == "__main__":
    sys.excepthook = handle_exception
    logging_setup()
    main()

