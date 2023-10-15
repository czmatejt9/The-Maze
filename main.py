import copy
import sys
import os
import random
import queue
import json
import socket
from datetime import datetime, timezone
import webbrowser
import logging
import pygame
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient

pygame.init()
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "variables.env"))

# for type hints
RGB = tuple[int, int, int]

# constants, game settings
VERSION = "2.0.2"
CONNECTED = False
ERROR_MESSAGE = "Oops... Looks like an error occurred, please send the error data. Then you can try restarting the app"
IP_ADDRESS = socket.gethostbyname(socket.gethostname())
CONNECTION_TO_DATABASE = os.environ["CONECTION_TO_DATABASE"]
WIDTH = 1376
HEIGHT = 774
MAX_MAZE_WIDTH = 67
MAX_MAZE_HEIGHT = 35
MAX_NAME_LENGTH = 20
MOVE = pygame.USEREVENT + 1
NPC_MOVE = pygame.USEREVENT + 2
NPC_UPDATE_POS = pygame.USEREVENT + 3
NPC_RENDER = pygame.USEREVENT + 4
COLORS = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "purple": (255, 0, 255),
    "cyan": (0, 255, 255),
    "yellow": (255, 255, 0),
    "light_grey": (211, 211, 211),
    "dark_grey": (50, 50, 50),
    "dark_yellow": (246, 190, 0)
}

# creating game window, and other stuff
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SRCALPHA)
pygame.display.set_caption(f"THE MAZE {VERSION}")

# sounds
ALARM_SOUND = pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              "game_files", "sounds", "ALARM.wav"))
CORRECT_QUESTION = pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "game_files", "sounds", "correct_q.wav"))
WRONG_QUESTION = pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                 "game_files", "sounds", "incorrect_q.wav"))
LEVEL_WIN = pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "game_files", "sounds", "win_level.wav"))
LEVEL_LOSE = pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "game_files", "sounds", "prohra.wav"))


# class for some other global variables and settings so that funcs dont need global if they need to change some variable
class Main:
    pause_image = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                 "game_files", "images", "pause_button.png"))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24)
    # highscores
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files", "jsons", "highscores.json"),
                  "rt", encoding="utf-8") as file:
            highscores = json.load(file)
    except FileNotFoundError:
        highscores = {
            "endless_all": [{"_id": 10 - i, "place": 10 - i, "name": f"bot{i}", "score": 1000 * i, "seed": 0,
                             "start": 0, "end": 0, "token": 0} for i in range(9, 0, -1)],
            "endless_all_custom": [
                {"_id": 10 - i, "place": 10 - i, "name": f"bot{i}", "score": 5000 + 1000 * i, "seed": 0,
                 "start": 0, "end": 0, "token": 0} for i in range(9, 0, -1)],
            "speedrun_easy": [{"_id": i, "place": i, "name": f"bot{i}", "time": 75 + 15 * i, "seed": 0,
                               "start": 0, "end": 0, "level times": "", "token": 0} for i in range(1, 10)],
            "speedrun_easy_custom": [{"_id": i, "place": i, "name": f"bot{i}", "time": 60 + 15 * i, "seed": 0,
                                      "start": 0, "end": 0, "level times": "", "token": 0} for i in range(1, 10)],
            "speedrun_normal": [{"_id": i, "place": i, "name": f"bot{i}", "time": 400 + 30 * i, "seed": 0,
                                 "start": 0, "end": 0, "level times": "", "token": 0} for i in range(1, 10)],
            "speedrun_normal_custom": [{"_id": i, "place": i, "name": f"bot{i}", "time": 300 + 30 * i, "seed": 0,
                                        "start": 0, "end": 0, "level times": "", "token": 0} for i in range(1, 10)],
            "speedrun_hard": [{"_id": i, "place": i, "name": f"bot{i}", "time": 900 + 60 * i, "seed": 0,
                               "start": 0, "end": 0, "level times": "", "token": 0} for i in range(1, 10)],
            "speedrun_hard_custom": [{"_id": i, "place": i, "name": f"bot{i}", "time": 800 + 60 * i, "seed": 0,
                                      "start": 0, "end": 0, "level times": "", "token": 0} for i in range(1, 10)],
            "speedrun_full view": [{"_id": i, "place": i, "name": f"bot{i}", "time": 400 + 30 * i, "seed": 0,
                                    "start": 0, "end": 0, "level times": "", "token": 0} for i in range(1, 10)],
            "speedrun_full view_custom": [{"_id": i, "place": i, "name": f"bot{i}", "time": 300 + 30 * i, "seed": 0,
                                           "start": 0, "end": 0, "level times": "", "token": 0} for i in range(1, 10)]
        }
    # settings
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files", "jsons", "settings.json"),
                  "rt", encoding="utf-8") as file:
            settings = json.load(file)
    except FileNotFoundError:  # default settings
        settings = {
            "difficulty": "Easy",
            "player speed": "Normal",
            "sounds": "on",
            "max fps": 140
        }
    diff_to_number = {
        "Easy": 4,
        "Normal": 3,
        "Hard": 2,
        "Full view": 0
    }
    speed_to_length = {
        "Slow": 200,
        "Normal": 150,
        "Fast": 100
    }
    # loading Qs
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files", "texts", "otazky.txt"), "r",
              encoding="utf-8") as file_q:
        questions = [x[:-1].split("=") for x in file_q]

    can_move = {
        "all": True,
        "left": True,
        "right": True,
        "up": True,
        "down": True
    }
    circle_square = True
    switch = True
    elapsed_movement = 0
    animation_length = speed_to_length[settings["player speed"]]  # in milliseconds
    x = 0
    y = 0

    cache = ""

    mode: str
    mode_start: datetime  # start time of run as date time object
    mode_end: datetime  # end time of run as date time object
    seed = "random"  # random/custom
    seed_value = ""
    level_start: float
    level_time: float
    total_start: float
    total_time: float
    each_level_times: list
    score: int = 0
    keys: int
    required_keys: int
    current_level: int
    total_levels: int or str

    @classmethod
    def seed_input(cls, none: None):
        diff_button = Button(WIDTH // 2 - 200 // 2, 300, 200, 50, COLORS["black"], COLORS["black"], 0, COLORS["black"],
                             f"Difficulty: {Main.settings['difficulty']}", 24)
        info_button = Button(WIDTH // 2 - 200 // 2, 350, 200, 50, COLORS["black"], COLORS["black"], 0, COLORS["black"],
                             "start typing your seed below (numbers only) or leave it empty for random seed", 24)
        seed_button = Button(WIDTH // 2 - 200 // 2 - 170, 400, 200, 30, COLORS["black"], COLORS["black"], 5,
                             COLORS["black"], "Seed: ", 24)
        seed = InputBox(WIDTH // 2 - 270 // 2, 400, 270, 30, COLORS["black"], COLORS["black"], 5, COLORS["white"],
                        str(cls.seed_value), 24, True)
        clear_button = Button(WIDTH // 2 - 200 // 2 + 250, 400, 60, 30, COLORS["black"], COLORS["light_grey"], 5,
                              COLORS["white"], "Clear", 24)

        seed.active = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            seed.handle_event(event)

        seed_button.draw(WINDOW)
        info_button.draw(WINDOW)
        diff_button.draw(WINDOW)
        seed.draw(WINDOW)
        clear_button.draw(WINDOW)
        if clear_button.is_over(WINDOW, pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            seed.text = ""
        cls.seed_value = seed.text
        return False

    @classmethod
    def make_token(cls):
        i = random.randint(1, 9)
        seconds_start = cls.mode_start.replace(tzinfo=timezone.utc).timestamp()
        seconds_end = cls.mode_end.replace(tzinfo=timezone.utc).timestamp()
        total = round(seconds_start) * (i + 10) ** 2 // (round(seconds_end % 31536000))
        total = total * 10 + i
        return str(total)

    @classmethod
    def level_info(cls, maze, update_level_time: bool = True):  # todo redo the time counting
        fps_text = cls.font.render(f"FPS: {min(round(cls.clock.get_fps()), cls.settings['max fps'])}", True,
                                   COLORS["white"])
        if update_level_time:
            cls.level_time = pygame.time.get_ticks() / 1000 - cls.level_start
        cls.total_time = pygame.time.get_ticks() / 1000 - cls.total_start
        level_time = datetime.fromtimestamp(cls.level_time)
        total_time = datetime.fromtimestamp(cls.total_time)
        total_text = cls.font.render(f"TOTAL TIME: {total_time.strftime('%M: %S.')}", True, COLORS["white"])
        level_text = cls.font.render(f"level time: {level_time.strftime('%M: %S.')}", True, COLORS["white"])
        score_text = cls.font.render(f"Total Score: {round(cls.score)}", True, COLORS["white"])
        level_count_text = cls.font.render(f"Level: {cls.current_level} / {cls.total_levels}", True, COLORS["white"])
        npc_count_text = cls.font.render(f"Guards: {len(Npc.npcs)}", True, COLORS["white"])
        mode_text = cls.font.render(f"Mode: {cls.mode}", True, COLORS["white"])
        diff_text = cls.font.render(f"Difficulty: {cls.settings['difficulty']}", True, COLORS["white"])
        keys_text = cls.font.render(f"Keys: {cls.keys} / {cls.required_keys}    Remaining keys: {len(maze.q_location)}",
                                    True, COLORS["white"])

        font = pygame.font.SysFont("arial", 18)
        total_milli = font.render(total_time.strftime("%f")[:-3], True, COLORS["white"])
        level_milli = font.render(level_time.strftime("%f")[:-3], True, COLORS["white"])

        pygame.draw.rect(WINDOW, COLORS["black"], (0, 0, WIDTH, 60))
        if cls.mode == "Speedrun":
            WINDOW.blit(level_text, (WIDTH - level_text.get_width() - 10 - 30, 30 // 2 - level_text.get_height() // 2))
            WINDOW.blit(total_text,
                        (WIDTH - total_text.get_width() - 10 - 30, 30 // 2 + 30 - total_text.get_height() // 2))
            WINDOW.blit(level_milli, (WIDTH - 10 - 29, 14 + level_text.get_height() // 2 - level_milli.get_height()))
            WINDOW.blit(total_milli, (WIDTH - 10 - 29, 44 + level_text.get_height() // 2 - total_milli.get_height()))
        else:
            WINDOW.blit(score_text, (WIDTH - score_text.get_width() - 10, 60 // 2 - score_text.get_height() // 2))
        WINDOW.blit(fps_text, (60, 60 // 2 - fps_text.get_height() // 2))
        WINDOW.blit(npc_count_text,
                    (WIDTH * 3 / 4 - npc_count_text.get_width() // 2, 45 - npc_count_text.get_height() // 2))
        WINDOW.blit(level_count_text, (WIDTH * 3 / 4 - level_count_text.get_width() // 2,
                                       15 - level_count_text.get_height() // 2))
        WINDOW.blit(diff_text, (WIDTH * 1 / 4 - diff_text.get_width() // 2, 60 // 2 + 15 - diff_text.get_height() // 2))
        WINDOW.blit(mode_text, (WIDTH * 1 / 4 - mode_text.get_width() // 2, 60 // 2 - 15 - diff_text.get_height() // 2))
        WINDOW.blit(keys_text, (WIDTH // 2 - keys_text.get_width() // 2, 30 // 2 - keys_text.get_height() // 2))
        for i in range(cls.required_keys):
            pygame.draw.rect(WINDOW, COLORS["white"], (WIDTH // 2 - 200 // 2 + 200 // cls.required_keys * i,
                                                       45 - 24 // 2, 200 // cls.required_keys, 24), 2)
        WINDOW.blit(maze.key, (WIDTH // 2 - 200 // 2 - 5 - maze.key.get_width(), 35))
        WINDOW.blit(maze.door, (WIDTH // 2 + 200 // 2 + 5, 35))
        percentage = cls.keys / cls.required_keys
        pygame.draw.rect(WINDOW, COLORS["white"] if percentage < 0.5 else COLORS["dark_yellow"] if percentage < 1 else
        COLORS["green"], (WIDTH // 2 - 100, 45 - 24 // 2, 200 * min(percentage, 1), 24))
        pygame.draw.rect(WINDOW, COLORS["white"], (0, 60, WIDTH, 5))
        return True

    @classmethod
    def win_lose_screen(cls, maze, state: str = "win"):
        if Main.settings["sounds"] == "on" and state == "win":
            LEVEL_WIN.play()
        elif Main.settings["sounds"] == "on":
            LEVEL_LOSE.play()

        if state == "win":
            victory = Button(WIDTH // 2 - 300 // 2, HEIGHT // 2 - 50 // 2 - 50, 300, 50, COLORS["green"],
                             COLORS["green"], 5, COLORS["green"], "Victory", 32, font_color=COLORS["black"])
        else:
            victory = Button(WIDTH // 2 - 300 // 2, HEIGHT // 2 - 50 // 2 - 50, 300, 50, COLORS["red"],
                             COLORS["red"], 5, COLORS["red"], "Defeat", 32, font_color=COLORS["black"])

        continue_button = Button(WIDTH // 2 - 200 // 2, HEIGHT // 2 - 50 // 2 + 50, 200, 50, COLORS["black"],
                                 COLORS["light_grey"], 5, COLORS["white"], "Continue", 24)
        while True:
            cls.clock.tick(cls.settings["max fps"])
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            WINDOW.fill(COLORS["black"])
            cls.level_info(maze, False)
            victory.draw(WINDOW)
            continue_button.draw(WINDOW)
            if continue_button.is_over(WINDOW, pygame.mouse.get_pos()):
                if pygame.mouse.get_pressed()[0]:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    return
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            pygame.display.flip()

    @classmethod
    def question(cls, maze):
        question = cls.choose_q()
        header = Button(WIDTH // 2 - 1000 // 2, 200, 1000, 100, COLORS["black"], COLORS["light_grey"], 5,
                        COLORS["black"], question[0], 30)
        buttons = [Button(WIDTH // 2 - 500 // 2, 250 + 75 * (i + 1), 500, 50, COLORS["black"], COLORS["light_grey"], 5,
                          COLORS["white"], question[i + 1], 24) for i in range(3)]
        done = False
        start = pygame.time.get_ticks() / 1000
        while not done:
            cls.clock.tick(cls.settings["max fps"])
            WINDOW.fill(COLORS["black"])

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                for button in buttons:
                    answer = button.handle_event(event)
                    if answer:
                        done = True
                        break

            font = pygame.font.SysFont("arial", 40)
            time_left = (15 - pygame.time.get_ticks() / 1000 + start)
            time_left_text = font.render(f"Time left: {str(round(time_left, 1))}", True, COLORS["white"])
            if time_left < 0 and not done:
                answer = next((button.text for button in buttons if button.active), buttons[0].text)
                if not any((button.text for button in buttons if button.active)):
                    buttons[0].active = True
                done = True

            WINDOW.blit(time_left_text, (WIDTH // 2 - time_left_text.get_width() // 2, 100))
            header.draw(WINDOW)
            for button in buttons:
                button.draw(WINDOW)
            cls.level_info(maze)
            pygame.display.flip()

        if answer == question[-1]:
            cls.keys += 1
            if Main.settings["sounds"] == "on":
                CORRECT_QUESTION.play()
        elif Main.settings["sounds"] == "on":
            WRONG_QUESTION.play()

        for button in buttons:
            if button.text == str(question[-1]):
                button.bg_color = COLORS["green"]
            elif button.active:
                button.bg_color = COLORS["red"]
            button.active = False
            button.draw(WINDOW)
            pygame.display.flip()

        cont = Button(WIDTH // 2 - 150 // 2, 600, 150, 50, COLORS["black"], COLORS["light_grey"], 5, COLORS["white"],
                      text="CONTINUE", font_color=COLORS["white"], font_hover_color=COLORS["black"], fontsize=30)
        while True:
            cls.clock.tick(cls.settings["max fps"])

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            cls.level_info(maze)
            cont.draw(WINDOW)
            if cont.is_over(WINDOW, pygame.mouse.get_pos()):
                if pygame.mouse.get_pressed()[0]:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    break
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            pygame.display.flip()

    # chooses a random questions and shuffles answers
    @classmethod
    def choose_q(cls, question: str = ""):
        if not question:
            if not cls.questions:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files", "texts", "otazky.txt"),
                          "r", encoding="utf-8") as file_q:
                    cls.questions = [x[:-1].split("=") for x in file_q]

            question = random.choice(cls.questions)
            cls.questions.remove(question)

        q = question.pop(0)
        ca = question[0]
        random.shuffle(question)
        question.insert(0, q)
        question.append(ca)
        return question

    @classmethod
    def level(cls, maze):  # sourcery no-metrics
        pause_button = Button(10, 10, 40, 40, COLORS["white"], COLORS["light_grey"], 1, COLORS["white"])
        cls.level_start = pygame.time.get_ticks() / 1000
        cls.switch = True
        cls.required_keys = len(maze.q_location) // 2
        cls.keys = 0
        Main.can_move["all"] = True  # hopefully fixed the bug when sometimes you can die and next run you cant move

        player = Player(maze)
        pygame.time.set_timer(NPC_UPDATE_POS, 9000)
        pygame.time.set_timer(NPC_MOVE, 2000)
        Npc.update_player_coordinates(player)

        WINDOW.fill(COLORS["black"])
        player.maze.render_full(player)
        player.render(0, 0)
        done = False
        while not done:
            ms = cls.clock.tick(cls.settings["max fps"])

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == NPC_UPDATE_POS:
                    Npc.update_player_coordinates(player)
                if event.type == NPC_MOVE:
                    Npc.move_all_npc(player)
                if event.type == NPC_RENDER:
                    if Npc.elapsed_movement < Main.animation_length:
                        Npc.elapsed_movement = min(Npc.elapsed_movement + ms, Main.animation_length)
                        pygame.event.post(pygame.event.Event(NPC_RENDER))
                    else:
                        Npc.can_kill = True
                    Npc.render_all_npc(player)
                    if not Main.elapsed_movement:
                        player.render(0, 0)

                if event.type == MOVE:
                    if Main.elapsed_movement < Main.animation_length:
                        Main.can_move["all"] = False
                        Main.elapsed_movement = min(Main.elapsed_movement + ms, Main.animation_length)
                        offset_x = int(Main.elapsed_movement / Main.animation_length * player.maze.tile_size) * Main.x
                        offset_y = int(Main.elapsed_movement / Main.animation_length * player.maze.tile_size) * Main.y
                        player.maze.render_movement(player)
                        player.render(offset_x, offset_y)
                        pygame.event.post(pygame.event.Event(MOVE))
                    else:
                        Main.can_move["all"] = True
                        player.x += Main.x
                        player.y += Main.y
                        Main.x = Main.y = 0
                        player.maze.render_movement(player)
                        player.render(0, 0)
                        cls.elapsed_movement = 0

            # win
            if player.maze.is_tile(player.x, player.y, "F") and cls.keys / cls.required_keys >= 1:
                cls.win_lose_screen(maze)
                exitcode = "win"
                break

            # lose
            if name := Npc.collide(player) and Npc.can_kill:
                cls.win_lose_screen(maze, name)
                exitcode = "lose"
                break

            # also lose
            if cls.keys + len(maze.q_location) < cls.required_keys:
                cls.win_lose_screen(maze, "Q")
                exitcode = "lose"
                break

            if (player.x, player.y) in maze.q_location:
                cls.question(maze)
                maze.change_tile(player.x, player.y, "p")
                maze.q_location.remove((player.x, player.y))
                if cls.keys >= cls.required_keys:
                    player.maze.door = player.maze.open_door
                WINDOW.fill(COLORS["black"])
                player.maze.render_full(player)
                player.render(0, 0)

            keys_pressed = pygame.key.get_pressed()
            if Main.can_move["all"]:
                player.movement(keys_pressed)


            #cheat option
            if keys_pressed[pygame.K_x]:
                cls.win_lose_screen(maze)
                exitcode = "win"
                break

            cls.level_info(maze)
            pause_button.draw(WINDOW)
            if pause_button.is_over(WINDOW, pygame.mouse.get_pos()) or keys_pressed[pygame.K_ESCAPE]:
                if pygame.mouse.get_pressed()[0] or keys_pressed[pygame.K_ESCAPE]:
                    while True:
                        selection = Menu("Paused", ("Continue", "Settings", "Give up"),
                                         Main.level_info, maze).mainloop(WINDOW)
                        if selection == "Settings":
                            cls.settings_gui(False)
                        elif selection == "Give up":
                            cls.win_lose_screen(maze, "lose")
                            exitcode = "lose"
                            done = True
                            break
                        else:
                            WINDOW.fill(COLORS["black"])
                            player.maze.render_full(player)
                            player.render(0, 0)
                            break
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            WINDOW.blit(cls.pause_image, (10, 10))
            pygame.display.flip()

        return exitcode

    @classmethod
    def speedrun_mode(cls):
        """"
        maze sizes for corresponding difficulties
        11 - 7, 15 - 9, 19 - 11, 23 - 13, 27 - 15 ___ 4 - 8
        31 - 17, 35 - 19, 39 - 21, 43 - 23, 47 - 25 ___ 3 - 6
        51 - 27, 55 - 29, 59 - 31, 63 - 33, 67 - 35 ___ 2 - 4
        """
        cls.mode = "Speedrun"
        menu = Menu("Speedrun Mode", ("Play", "", "", "", "Settings", "Back"), Main.seed_input, None)
        while True:
            cls.clock.tick(cls.settings["max fps"])
            selection = menu.mainloop(WINDOW)
            if selection == "Play":
                win_lose = "win"
                if cls.seed_value in ["", "-"]:
                    cls.seed_value = random.randint(-sys.maxsize, sys.maxsize)
                    cls.seed = "random"
                else:
                    cls.seed_value = int(cls.seed_value)
                    cls.seed = "custom"

                rng = random.Random(cls.seed_value)
                cls.current_level = 1
                cls.total_levels = 5
                cls.each_level_times = []
                width = 91 - Main.diff_to_number[Main.settings["difficulty"]] * 20
                height = 47 - Main.diff_to_number[Main.settings["difficulty"]] * 10
                if cls.settings["difficulty"] == "Full view":
                    width, height = 15, 9
                maze = Maze(width, height, rng)
                cls.mode_start = datetime.now()
                cls.total_start = pygame.time.get_ticks() / 1000

                for _ in range(5):
                    state = cls.level(maze)
                    if state == "lose":
                        win_lose = state
                        break
                    cls.each_level_times.append(str(round(cls.level_time, 3)))
                    width += 4 if cls.settings["difficulty"] != "Full view" else 12
                    height += 2 if cls.settings["difficulty"] != "Full view" else 6
                    cls.current_level += 1
                    maze = Maze(width, height, rng)

                cls.mode_end = datetime.now()
                enter_name = False
                if win_lose == "win":
                    cls.total_time = round(cls.total_time, 3)
                    text = f"Congratulations you finished speedrun in {cls.total_time} {cls.each_level_times}"
                    highscores = Main.highscores[f"speedrun_{cls.settings['difficulty'].lower()}"
                                                 + f"{'' if cls.seed == 'random' else '_custom'}"]
                    if cls.total_time < highscores[-1]["time"]:
                        enter_name = True
                        name = InputBox(WIDTH // 2 - 400 // 2, 400, 400, 50, COLORS["black"], COLORS["light_grey"], 5,
                                        COLORS["white"], "", 24)
                        name.active = True
                        info_more = Button(WIDTH // 2, 250, 0, 50, COLORS["black"], COLORS["black"], 0,
                                           COLORS["black"], "Please enter your name below and press continue", 24)

                else:
                    text = "Unfortunately you didn't manage to finish this speedrun"

                info_button = Button(WIDTH // 2, 200, 0, 50, COLORS["black"], COLORS["black"], 0, COLORS["black"], text,
                                     32)
                exit_button = Button(WIDTH // 2 - 200 // 2, 500, 200, 50, COLORS["black"], COLORS["light_grey"], 5,
                                     COLORS["white"], "Continue", 24)

                while True:
                    cls.clock.tick(cls.settings["max fps"])
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if enter_name:
                            name.handle_event(event)

                    WINDOW.fill(COLORS["black"])
                    if enter_name:
                        info_more.draw(WINDOW)
                        name.draw(WINDOW)
                    info_button.draw(WINDOW)
                    exit_button.draw(WINDOW)
                    if exit_button.is_over(WINDOW, pygame.mouse.get_pos()):
                        if pygame.mouse.get_pressed()[0]:
                            pygame.time.delay(200)
                            break
                    else:
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    pygame.display.flip()

                if enter_name:
                    highscores[-1] = {"_id": 9, "place": 9, "name": name.text, "time": cls.total_time,
                                      "level times": str(cls.each_level_times), "seed": cls.seed_value,
                                      "seed_type": cls.seed,
                                      "start": cls.mode_start.strftime("%Y/%m/%d %H:%M:%S"),
                                      "end": cls.mode_end.strftime("%Y/%m/%d %H:%M:%S"), "token": cls.make_token()}
                    highscores.sort(key=lambda item: item["time"])
                    highscores = highscores[:9]
                    for x in range(len(highscores)):
                        highscores[x]["_id"] = x + 1
                        highscores[x]["place"] = x + 1
                    Main.highscores[f"speedrun_{cls.settings['difficulty'].lower()}"
                                    + f"{'' if cls.seed == 'random' else '_custom'}"] = copy.deepcopy(highscores)
                    cls.save_highscores()
                    Database.active.sync_online("speedrun")

            elif selection == "Settings":
                cls.settings_gui()
            else:
                break

    @classmethod
    def endless_mode(cls):
        cls.mode = "Endless"
        menu = Menu("Endless mode", ("Play", "", "", "", "Settings", "Back"), Main.seed_input, None)
        while True:
            selection = menu.mainloop(WINDOW)
            if selection == "Play":
                win_lose = "win"
                if not cls.seed_value or cls.seed == "-":
                    cls.seed_value = random.randint(-sys.maxsize, sys.maxsize)
                    cls.seed = "random"
                else:
                    cls.seed_value = int(cls.seed_value)
                    cls.seed = "custom"

                rng = random.Random(cls.seed_value)
                cls.current_level = 1
                cls.total_levels = "?"
                width = 11
                height = 7
                maze = Maze(width, height, rng)
                cls.mode_start = datetime.now()
                cls.total_start = pygame.time.get_ticks() / 1000
                cls.score = 0
                while True:
                    state = cls.level(maze)
                    if state == "lose":
                        win_lose = state
                        break
                    cls.score += (width * height - cls.level_time) * (1
                        +(5 - (cls.diff_to_number[cls.settings["difficulty"]]
                              or 5)))
                    width = min(width + 4, MAX_MAZE_WIDTH)
                    height = min(height + 2, MAX_MAZE_HEIGHT)
                    cls.current_level += 1
                    maze = Maze(width, height, rng)

                cls.mode_end = datetime.now()
                cls.score = round(cls.score)
                enter_name = False

                cls.total_time = round(cls.total_time, 3)
                text = f"Congratulations you finished endless mode with score of {cls.score}"
                highscores = Main.highscores[f"endless_all{'' if cls.seed == 'random' else '_custom'}"]

                if cls.score > highscores[-1]["score"]:
                    enter_name = True
                    name = InputBox(WIDTH // 2 - 400 // 2, 400, 400, 50, COLORS["black"], COLORS["light_grey"], 5,
                                    COLORS["white"], "", 24)
                    name.active = True
                    info_more = Button(WIDTH // 2, 250, 0, 50, COLORS["black"], COLORS["black"], 0,
                                       COLORS["black"], "Please enter your name below and press continue", 24)

                info_button = Button(WIDTH // 2, 200, 0, 50, COLORS["black"], COLORS["black"], 0, COLORS["black"], text,
                                     32)
                exit_button = Button(WIDTH // 2 - 200 // 2, 500, 200, 50, COLORS["black"], COLORS["light_grey"], 5,
                                     COLORS["white"], "Continue", 24)

                while True:
                    cls.clock.tick(cls.settings["max fps"])
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if enter_name:
                            name.handle_event(event)

                    WINDOW.fill(COLORS["black"])
                    if enter_name:
                        info_more.draw(WINDOW)
                        name.draw(WINDOW)
                    info_button.draw(WINDOW)
                    exit_button.draw(WINDOW)
                    if exit_button.is_over(WINDOW, pygame.mouse.get_pos()):
                        if pygame.mouse.get_pressed()[0]:
                            pygame.time.delay(200)
                            break
                    else:
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    pygame.display.flip()

                if enter_name:
                    highscores[-1] = {"_id": 9, "place": 9, "name": name.text, "score": cls.score,
                                      "seed": cls.seed_value, "seed_type": cls.seed,
                                      "start": cls.mode_start.strftime("%Y/%m/%d %H:%M:%S"),
                                      "end": cls.mode_end.strftime("%Y/%m/%d %H:%M:%S"), "token": cls.make_token()}
                    highscores.sort(key=lambda item: item["score"], reverse=True)
                    highscores = highscores[:9]
                    for x in range(len(highscores)):
                        highscores[x]["_id"] = x + 1
                        highscores[x]["place"] = x + 1
                    Main.highscores[f"endless_all{'' if cls.seed == 'random' else '_custom'}"] = copy.deepcopy(highscores)
                    cls.save_highscores()
                    Database.active.sync_online("endless")
            elif selection == "Settings":
                cls.settings_gui()
            else:
                break

    @classmethod
    def story_mode(cls):
        cls.mode = "story"

    @classmethod
    def settings_gui(cls, change_diff: bool = True):
        copyx = Main.settings["max fps"]
        if Main.settings["max fps"] == 1000:
            Main.settings["max fps"] = "unlimited"
        diffs = ("Easy", "Normal", "Hard", "Full view")
        speed = ("Slow", "Normal", "Fast")
        sounds = ("on", "off")
        fps = (30, 60, 90, 120, 140, "unlimited")
        whole = [diffs, speed, sounds, fps]
        indexes = [diffs.index(Main.settings["difficulty"]), speed.index(Main.settings["player speed"]),
                   sounds.index(Main.settings["sounds"]), fps.index(Main.settings["max fps"])]
        diff_index = indexes[0]

        header = Button(WIDTH // 2 - 300 // 2, 100, 300, 50, COLORS["black"], COLORS["black"], 5, COLORS["white"],
                        "Settings", 30)
        key_buttons = [Button(WIDTH // 3, 200 + i * 100, 200, 50, COLORS["black"], COLORS["black"], 0, COLORS["white"],
                              key.upper(), 24) for i, key in enumerate(Main.settings.keys())]
        value_buttons = [Button(WIDTH // 3 * 2 - 200, 200 + i * 100, 200, 50, COLORS["black"], COLORS["black"], 0,
                                COLORS["white"], str(value).upper(), 24) for i, value in
                         enumerate(Main.settings.values())]

        exit_button = Button(WIDTH // 2 - 200 // 2, 600, 200, 50, COLORS["black"], COLORS["light_grey"], 5,
                             COLORS["white"], "Save", 24)
        points = []
        for i in range(4):
            points.extend(([(WIDTH // 3 * 2 - 160, 200 + i * 100), (WIDTH // 3 * 2 - 160, 200 + i * 100 + 50),
                            (WIDTH // 3 * 2 - 160 - 20, 200 + i * 100 + 50 // 2)],
                           [(WIDTH // 3 * 2 - 40, 200 + i * 100), (WIDTH // 3 * 2 - 40, 200 + i * 100 + 50),
                            (WIDTH // 3 * 2 - 40 + 20, 200 + i * 100 + 50 // 2)]))
        rect_buttons = []
        for each in points:
            bounding_rect = pygame.draw.polygon(WINDOW, COLORS["white"], each)
            rect_buttons.append(Button(bounding_rect.x, bounding_rect.y, bounding_rect.width, bounding_rect.height,
                                       COLORS["black"], COLORS["black"], 0, COLORS["white"]))

        while True:
            cls.clock.tick(copyx)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                for button in rect_buttons:
                    button.handle_event(event)

            for i, button in enumerate(rect_buttons):
                if button.active:
                    button.active = False
                    indexes[i // 2] += 1 if i % 2 else -1
                    for x in range(len(indexes)):
                        length = len(whole[x])
                        if indexes[x] >= length:
                            indexes[x] = 0
                        elif indexes[x] < 0:
                            indexes[x] = length - 1
                    if not change_diff:
                        indexes[0] = change_diff
                    for main_button, setting, index in zip(value_buttons, whole, indexes):
                        main_button.text = str(setting[index]).upper()

            WINDOW.fill(COLORS["black"])
            header.draw(WINDOW)
            for button in key_buttons:
                button.draw(WINDOW)
            for button in value_buttons:
                button.draw(WINDOW)
            exit_button.draw(WINDOW)
            if exit_button.is_over(WINDOW, pygame.mouse.get_pos()):
                if pygame.mouse.get_pressed()[0]:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                    Main.settings = {
                        "difficulty": whole[0][indexes[0]],
                        "player speed": whole[1][indexes[1]],
                        "sounds": whole[2][indexes[2]],
                        "max fps": whole[3][indexes[3]],
                    }
                    if Main.settings["max fps"] == "unlimited":
                        Main.settings["max fps"] = 1000
                    cls.animation_length = cls.speed_to_length[cls.settings["player speed"]]
                    cls.save_settings()
                    pygame.time.delay(200)
                    break
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            for each in points:
                pygame.draw.polygon(WINDOW, COLORS["white"], each)
            pygame.display.flip()

    @classmethod
    def save_settings(cls):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files", "jsons", "settings.json"),
                  "wt", encoding="utf-8") as file:
            json.dump(Main.settings, file, indent=2)

    @classmethod
    def save_highscores(cls):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files", "jsons", "highscores.json"),
                  "wt", encoding="utf-8") as file:
            json.dump(Main.highscores, file, indent=2)


class Maze:
    def __init__(self, width: int, height: int, rng: random.Random, top_indent: int = 65):
        if width < 5 or height < 5:
            raise ValueError("Width and height must be 5 or bigger")
        self.width = width
        self.height = height
        self.rng = rng
        self.top_indent = top_indent
        self.maze = self.maze_generator()
        self.start, self.end = self.add_start_finish()
        self.q_location = self.add_questions()
        self.wall = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "game_files", "images", "wall.png"))
        self.path = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "game_files", "images", "path.png"))
        self.open_door = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                        "game_files", "images", "open_door_with_path.png"))
        self.closed_door = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                          "game_files", "images", "closed_door_with_path.png"))
        self.door = self.closed_door
        self.key = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "game_files", "images", "key_with_path.png"))
        self.tile_size = 20
        Npc.clear()
        for _ in range(min((self.width * self.height + 100) // 600, 3)):
            Npc(self, self.rng)

    def maze_generator(self):
        generated_maze = [list("w" * self.width) for _ in range(self.height)]  # creating a wall grid

        # selecting a starting wall
        x = self.rng.randrange(1, self.width - 1, 2)
        y = self.rng.randrange(1, self.height - 1, 2)  # border compensation

        walls = []
        self.add_walls(generated_maze, x, y, walls)
        while walls:
            # deleting improper walls
            temp = [each for each in walls if generated_maze[each[1]][each[0]] != "p"
                    and 1 <= each[0] <= self.width - 2 and 1 <= each[1] <= self.height - 2]
            walls = temp

            # returning the maze if walls are empty
            if not walls:
                break

            # processing random wall
            x, y = self.rng.choice(walls)
            self.make_passages(generated_maze, x, y, walls)
            walls.remove((x, y))

        return generated_maze

    # sub function for maze_generator_sub to make passages and walls while generating maze
    def make_passages(self, generated_maze: list, x: int, y: int, walls: list):
        # counting passages around wall
        n_up = n_down = n_left = n_right = 0
        if generated_maze[y][x + 1] == "c":
            n_right += 1
        if generated_maze[y + 1][x] == "c":
            n_down += 1
        if generated_maze[y][x - 1] == "c":
            n_left += 1
        if generated_maze[y - 1][x] == "c":
            n_up += 1

        # if there's only one passage around wall
        if n_down + n_up + n_left + n_right == 1:
            generated_maze[y][x] = "p"
            if n_right == 1:
                self.add_walls(generated_maze, x - 1, y, walls)
            elif n_left == 1:
                self.add_walls(generated_maze, x + 1, y, walls)
            elif n_down == 1:
                self.add_walls(generated_maze, x, y - 1, walls)
            else:
                self.add_walls(generated_maze, x, y + 1, walls)

    # sub function that adds walls around processed wall while generating maze
    def add_walls(self, generated_maze: list, x: int, y: int, walls: list):
        if 0 < x < self.width - 1 and 0 < y < self.height - 1:
            generated_maze[y][x] = "c"
            walls.extend(((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)))
        return None

    def is_tile(self, x, y, tile):
        return self.maze[y][x] == tile

    def change_tile(self, x, y, tile):
        self.maze[y][x] = tile

    def get_tile(self, x, y):
        if self.maze[y][x] == "w":
            return self.path
        elif self.maze[y][x] == "F":
            return self.door
        elif self.maze[y][x] == "Q":
            return self.key
        else:
            return self.path

    def add_start_finish(self):
        x = 1
        y = self.rng.randint(1, self.height - 2)
        while self.is_tile(x, y, "w"):
            y = self.rng.randint(1, self.height - 2)
        self.change_tile(x, y, "S")
        start = (x, y)

        x = self.width - 2
        y = self.rng.randint(1, self.height - 2)
        while self.is_tile(x, y, "w"):
            y = self.rng.randint(1, self.height - 2)
        self.change_tile(x, y, "F")
        end = (x, y)
        return start, end

    def add_questions(self):
        location = set()
        amount = max(self.height * self.width // 100 + 1, 2)
        for _ in range(amount):
            x = self.rng.randint(1, self.width - 2)
            y = self.rng.randint(1, self.height - 2)
            while self.maze[y][x] not in ("c", "p") or (x + 1, y) in location \
                    or (x - 1, y) in location or (x, y + 1) in location or (x, y - 1) in location:
                x = self.rng.randint(1, self.width - 2)
                y = self.rng.randint(1, self.height - 2)
            self.maze[y][x] = "Q"
            location.add((x, y))
        return location

    def render_full(self, player):
        x, y = (WIDTH // 2 - self.width * self.tile_size // 2,
                (HEIGHT + self.top_indent) // 2 - self.height * self.tile_size // 2)
        pygame.draw.rect(WINDOW, COLORS["white"],
                         (x - 2, y - 2, self.width * self.tile_size + 4, self.height * self.tile_size + 4), 2)
        xx = x
        for i, row in enumerate(self.maze):
            x = xx
            for j, tile in enumerate(row):
                # background tiles
                if abs(i - player.y) > player.view_distance or abs(j - player.x) > player.view_distance:
                    pygame.draw.rect(WINDOW, COLORS["black"], (x, y, 20, 20))
                elif tile == "w":
                    WINDOW.blit(self.wall, (x, y))
                elif tile == "Q":
                    WINDOW.blit(self.key, (x, y))
                elif tile == "F":
                    WINDOW.blit(self.door, (x, y))
                elif tile == "x":
                    pygame.draw.rect(WINDOW, COLORS["black"], (x, y, 10, 10))
                else:
                    WINDOW.blit(self.path, (x, y))
                x += self.tile_size
            y += self.tile_size
        Npc.render_all_npc(player)

    def render_movement(self, player):
        if player.view_distance < 100:
            x, y = (WIDTH // 2 - self.width * self.tile_size // 2,
                    (HEIGHT + self.top_indent) // 2 - self.height * self.tile_size // 2)
            for xx in range(max(player.x - player.view_distance - 1, 0),
                            min(player.x + player.view_distance + 2, self.width)):
                for yy in range(max(player.y - player.view_distance - 1, 0),
                                min(player.y + player.view_distance + 2, self.height)):
                    if self.maze[yy][xx] == "w":
                        WINDOW.blit(self.wall, (x + xx * self.tile_size, y + yy * self.tile_size))
                    elif self.maze[yy][xx] == "Q":
                        WINDOW.blit(self.key, (x + xx * self.tile_size, y + yy * self.tile_size))
                    elif self.maze[yy][xx] == "F":
                        WINDOW.blit(self.door, (x + xx * self.tile_size, y + yy * self.tile_size))
                    else:
                        WINDOW.blit(self.path, (x + xx * self.tile_size, y + yy * self.tile_size))
        Npc.render_all_npc(player)
        # moved circle for vision to player render

    # TODO magnetic moving
    def get_surrounding_walls(self, x, y):
        count = 0
        if self.is_tile(x + 1, y, "w"):
            count += 1
        if self.is_tile(x - 1, y, "w"):
            count += 1
        if self.is_tile(x, y + 1, "w"):
            count += 1
        if self.is_tile(x, y - 1, "w"):
            count += 1

        return count


class Player:
    def __init__(self, maze: Maze):
        self.x, self.y = maze.start
        self.view_distance = 101
        if x := Main.diff_to_number[Main.settings["difficulty"]]:
            self.view_distance = x
        self.score = 0
        self.maze = maze
        self.image = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "game_files", "images", "saolin.png"))
        self.render(0, 0)

    def movement(self, keys_pressed):
        if (keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]) and not self.maze.is_tile(self.x - 1, self.y, "w"):
            pygame.event.post(pygame.event.Event(MOVE))
            Main.x -= 1
        elif (keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]) and not self.maze.is_tile(self.x + 1, self.y,
                                                                                                  "w"):
            pygame.event.post(pygame.event.Event(MOVE))
            Main.x += 1
        elif (keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]) and not self.maze.is_tile(self.x, self.y - 1, "w"):
            pygame.event.post(pygame.event.Event(MOVE))
            Main.y -= 1
        elif (keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]) and not self.maze.is_tile(self.x, self.y + 1,
                                                                                                 "w"):
            pygame.event.post(pygame.event.Event(MOVE))
            Main.y += 1

        Main.elapsed_movement = 0

    def render(self, offset_x, offset_y):
        x, y = (WIDTH // 2 - self.maze.width * self.maze.tile_size // 2,
                (HEIGHT + self.maze.top_indent) // 2 - self.maze.height * self.maze.tile_size // 2)
        x += self.x * self.maze.tile_size + offset_x
        y += self.y * self.maze.tile_size + offset_y
        WINDOW.blit(self.maze.get_tile(self.x, self.y), (x - offset_x, y - offset_y))
        WINDOW.blit(self.maze.get_tile(self.x + Main.x, self.y + Main.y),
                    (x - offset_x + Main.x * 20, y - offset_y + Main.y * 20))
        WINDOW.blit(self.image, (x, y))

        # circle for vision
        if self.view_distance > 100:
            return None
        x, y = (WIDTH // 2 - self.maze.width * self.maze.tile_size // 2,
                (HEIGHT + self.maze.top_indent) // 2 - self.maze.height * self.maze.tile_size // 2)
        if Main.circle_square:
            circle_thickness = self.maze.tile_size * 4
            pygame.draw.circle(WINDOW, COLORS["black"], (x + self.x * self.maze.tile_size + 10 + offset_x,
                                                         y + self.y * self.maze.tile_size + 10 + offset_y),
                               self.view_distance * self.maze.tile_size + 30 + circle_thickness, circle_thickness + 20)
        else:
            # SQUARE RENDERING, order is: up, down, left, right
            pygame.draw.rect(WINDOW, COLORS["black"],
                             (x + (self.x - self.view_distance - 2) * self.maze.tile_size + offset_x,
                              y + (self.y - self.view_distance - 2) * self.maze.tile_size + offset_y,
                              (self.view_distance * 2 + 5) * self.maze.tile_size,
                              self.maze.tile_size * (self.view_distance * 2 + 5)), self.maze.tile_size * 2)
        # border
        pygame.draw.rect(WINDOW, COLORS["white"], (x - 2, y - 2, self.maze.width * self.maze.tile_size + 4,
                                                   self.maze.height * self.maze.tile_size + 4), 2)


# class defining non player characters
class Npc:
    image = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           "game_files", "images", "npc.png"))
    player_coordinates = (0, 0)
    elapsed_movement = 0
    can_kill = True
    moved = False
    npcs = []
    names = ["Base", "Petr", "Alfons"]

    def __init__(self, maze: Maze, rng: random.Random, view_distance: int = 20):
        self.maze = maze
        self.name = rng.choice(self.names)
        self.npcs.append(self)
        self.view_distance = view_distance
        self.y = rng.randint(1, self.maze.height - 2)
        self.x = rng.randint(self.maze.width // 2, self.maze.width - 2)
        self.old_x, self.old_y = self.x, self.y
        while self.maze.maze[self.y][self.x] == "w":
            self.y = rng.randint(1, self.maze.height - 2)
            self.x = rng.randint(self.maze.width // 2, self.maze.width - 2)

    # moves npc closer to the player, player_x and player_y is for determining the path (NPCs vision is delayed)
    # whereas player contains actual position and is used for rendering purposes
    def npc_move(self, player: Player):
        player_x, player_y = self.player_coordinates
        self.old_y, self.old_x = self.y, self.x
        if abs(self.x - player_x) > self.view_distance or abs(self.y - player_y) > self.view_distance:
            return None

        path = path_finder(self.maze, (self.y, self.x), (player_y, player_x), "w")
        try:
            self.y, self.x = path[1]
        except IndexError:
            self.y, self.x = path[0]
            self.old_y, self.old_x = self.y, self.x

        if Main.settings["sounds"] == 'on' and len(path) <= 30:
            ALARM_SOUND.play()
        return None

    def render(self, player: Player):
        if abs(self.y - player.y) > player.view_distance + 1 or abs(self.x - player.x) > player.view_distance + 1:
            return None
        x, y = (WIDTH // 2 - self.maze.width * self.maze.tile_size // 2,
                (HEIGHT + self.maze.top_indent) // 2 - self.maze.height * self.maze.tile_size // 2)
        x += self.old_x * self.maze.tile_size
        y += self.old_y * self.maze.tile_size
        WINDOW.blit(self.maze.get_tile(self.old_x, self.old_y), (x, y))
        WINDOW.blit(self.maze.get_tile(self.x, self.y),
                    (x + (self.x - self.old_x) * 20, y + (self.y - self.old_y) * 20))
        offset_x = (self.elapsed_movement / Main.animation_length) * (self.x - self.old_x) * 20
        offset_y = (self.elapsed_movement / Main.animation_length) * (self.y - self.old_y) * 20
        WINDOW.blit(self.image, (x + offset_x, y + offset_y))

    # checks for collision with player, return npc name or empty string
    @classmethod
    def collide(cls, player):
        return next((each.name for each in cls.npcs if each.x == player.x and each.y == player.y), "")

    @classmethod
    def is_any_npc(cls, x, y):
        return any(True for each in cls.npcs if each.x == x and each.y == y)

    @classmethod
    def clear(cls):
        cls.npcs.clear()

    @classmethod
    def render_all_npc(cls, player):
        for each in cls.npcs:
            each.render(player)

    @classmethod
    def move_all_npc(cls, player):
        for npc in cls.npcs:
            npc.npc_move(player)
        cls.elapsed_movement = 0
        cls.can_kill = False
        pygame.event.post(pygame.event.Event(NPC_RENDER))

    @classmethod
    def update_player_coordinates(cls, player: Player):
        cls.player_coordinates = (player.x, player.y)


class Button:
    def __init__(self, x: int, y: int, width: int, height: int, bg_color: RGB, hover_color: RGB, outline_thickness: int,
                 outline_color: RGB, text: str = "", fontsize: int = 0, font_color: RGB = (255, 255, 255),
                 font_hover_color: RGB = (0, 0, 0), font: str = "arial", active_color: RGB = (244, 132, 14)):
        self.bg_color = bg_color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.hover_color = hover_color
        self.outline_color = outline_color
        self.outline_thickness = outline_thickness
        self.text = text
        self.font = font
        self.fontsize = fontsize
        self.font_color = font_color
        self.font_hover_color = font_hover_color
        self.active = False
        self.active_color = active_color

    def draw(self, window: pygame.Surface, hover: bool = False):
        pygame.draw.rect(window, self.outline_color, (self.x - self.outline_thickness, self.y - self.outline_thickness,
                                                      self.width + self.outline_thickness * 2,
                                                      self.height + self.outline_thickness * 2), 6, 6)
        pygame.draw.rect(window, self.active_color if self.active else self.hover_color if hover else self.bg_color,
                         (self.x, self.y, self.width, self.height))

        if self.text:
            self.draw_text(window, hover)

    def draw_text(self, window: pygame.Surface, hover: bool):
        font = pygame.font.SysFont(self.font, self.fontsize)
        text = font.render(self.text, True, self.font_hover_color if hover else self.font_color)
        window.blit(text, (self.x + (self.width / 2 - text.get_width() / 2),
                           self.y + (self.height / 2 - text.get_height() / 2)))

    # checks if mouse is on button and if is it also draws the hover state, returns TRUE/FALSE
    def is_over(self, window: pygame.Surface, pos: tuple[int, int]):
        if self.x - self.outline_thickness < pos[0] < self.x + self.width + self.outline_thickness \
                and self.y - self.outline_thickness < pos[1] < self.y + self.height + self.outline_thickness:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            enlargement = self.outline_thickness - 3
            self.height += enlargement * 2
            self.width += enlargement * 2
            self.x -= enlargement
            self.y -= enlargement
            self.draw(window, True)
            self.height -= enlargement * 2
            self.width -= enlargement * 2
            self.x += enlargement
            self.y += enlargement

            return True
        return False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.active and self.rect.collidepoint(event.pos):
                return self.text
            else:
                self.active = not self.active if self.rect.collidepoint(event.pos) else False
        return ""


class InputBox(Button):
    def __init__(self, x: int, y: int, width: int, height: int, bg_color: RGB, hover_color: RGB, outline_thickness: int,
                 outline_color: RGB, text: str, fontsize: int, only_number: bool = False):
        super().__init__(x, y, width, height, bg_color, hover_color, outline_thickness, outline_color, text, fontsize,
                         active_color=COLORS["black"])
        self.only_number = only_number

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                if self.text:
                    self.text = self.text[:-1]
            elif len(self.text) < MAX_NAME_LENGTH:
                if self.only_number:
                    if event.unicode.isnumeric() or (not self.text and event.unicode == "-"):
                        self.text += event.unicode
                else:
                    self.text += event.unicode


class Database:
    active = None

    def __init__(self, db, col):
        self.cluster = MongoClient(CONNECTION_TO_DATABASE, connectTimeoutMS=9000)
        self.db = self.cluster[db]
        self.col = self.db[col]
        self.active = self

    def change_db_col(self, db, col):
        self.db = self.cluster[db]
        self.col = self.db[col]

    def sync_all(self):
        all_modes = ("endless_all", "endless_all_custom", "speedrun_easy", "speedrun_easy_custom",
                     "speedrun_normal", "speedrun_normal_custom", "speedrun_hard", "speedrun_hard_custom",
                     "speedrun_full view", "speedrun_full view_custom")
        for each in all_modes:
            items = each.split("_")
            game_mode = items[0]
            Main.settings["difficulty"] = items[1]
            Main.seed = "custom" if len(items) == 3 else "random"
            self.sync_online(game_mode)

    def sync_online(self, game_mode):
        if game_mode == "speedrun":
            string = f"{game_mode}_{Main.settings['difficulty'].lower()}" + f"{'' if Main.seed == 'random' else '_custom'}"
        else:
            string = f"{game_mode}_all" + f"{'' if Main.seed == 'random' else '_custom'}"
        self.change_db_col("highscores", string)

        my_list = copy.deepcopy(Main.highscores[string])
        for i in range(1, 10):
            if x := self.col.find_one({"_id": i}):
                my_list.append(x)

        for x in range(len(my_list)):
            my_list[x]["_id"] = 0
            my_list[x]["place"] = 0
        my_list = [dict(t) for t in {tuple(d.items()) for d in my_list}]

        if game_mode == "speedrun":
            my_list.sort(key=lambda item: item["time"])
        else:

            my_list.sort(key=lambda item: item["score"], reverse=True)

        my_list = my_list[:9]
        for x in range(len(my_list)):
            my_list[x]["_id"] = x + 1
            my_list[x]["place"] = x + 1
        for i in range(1, 10):
            self.col.delete_one({"_id": i})
            self.col.insert_one(my_list[i - 1])

    @classmethod
    def initial_connection(cls):
        loading = Button(0, HEIGHT // 2 - 100, WIDTH, 200, COLORS["black"], COLORS["black"], 0, COLORS["black"],
                         "Loading...", 40)
        loading.draw(WINDOW)
        pygame.display.flip()

        try:
            state = Database("game_version", "game_version")
        except pymongo.errors.ConfigurationError as e:
            print(e)
            loading.text = "Couldn't connect, try again later"
            WINDOW.fill(COLORS["black"])
            loading.draw(WINDOW)
            pygame.display.flip()
            pygame.time.delay(3000)
            pygame.quit()
            sys.exit()

        global CONNECTED
        CONNECTED = True
        cls.active = state
        current = state.col.find_one({"_id": 0})
        if current["game_version"] != VERSION:
            loading.text = "New version is available, click to enter the website or press any key to continue"
        else:
            loading.text = "Press any key to continue"
        done = False
        while not done:
            WINDOW.fill(COLORS["black"])
            loading.draw(WINDOW)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and current["game_version"] != VERSION:
                    webbrowser.open_new_tab("https://czmatejt9.github.io")
                elif event.type == pygame.KEYDOWN:
                    done = True

    def send_error_data(self):
        self.change_db_col("errors", "errors")
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files", "errors.txt") ,
                  "rt", encoding="utf-8") as file:
            error_data = file.read()
        self.col.update_one({"_id": "main"}, {"$inc": {"index": 1}})
        index = self.col.find_one({"_id": "main"})
        index_number = index["index"]
        self.col.insert_one({"_id": index_number, "ip_address": IP_ADDRESS, "description": error_data})


# creates clickable menu from buttons, change settings for buttons in here
class Menu:
    def __init__(self, header: str, content: tuple, func=None, arg=None, outline: int = 5, button_width: int = 300,
                 button_height: int = 50, button_font = "arial"):
        self.header = header
        self.content = content
        self.button_width = button_width
        self.button_height = button_height
        self.header_width = int(self.button_width * 1.25)
        self.header_height = int(self.button_height * 1.2)
        self.spacing = 30
        self.func = func
        self.arg = arg
        self.outline = outline
        self.button_font = button_font

    def mainloop(self, window):
        n = len(self.content)
        header_button = Button(WIDTH // 2 - self.header_width // 2, HEIGHT // 2 - self.header_height // 2
                               - int(n / 2 * (self.header_height + self.spacing)), self.header_width,
                               self.header_height, COLORS["black"], COLORS["white"], self.outline, COLORS["white"],
                               self.header, 30, COLORS["white"], COLORS["black"], "arial")
        buttons = [Button(WIDTH // 2 - self.button_width // 2, HEIGHT // 2 - self.button_height // 2
                          - int((n / 2 - i - 1) * (self.button_height + self.spacing)), self.button_width,
                          self.button_height, COLORS["black"], COLORS["light_grey"], self.outline, COLORS["white"],
                          each, 24, COLORS["white"], COLORS["black"], self.button_font)
                   for i, each in enumerate(self.content) if each]

        # menu loop
        while True:
            event_q = True
            window.fill(COLORS["black"])
            if self.func:
                event_q = self.func(self.arg)

            Main.clock.tick(Main.settings["max fps"])
            if event_q:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

            # drawing buttons
            header_button.draw(window)
            for each in buttons:
                each.draw(window)

            hand = False
            for each in buttons:
                if each.is_over(window, pygame.mouse.get_pos()):
                    hand = True
                    if pygame.mouse.get_pressed()[0]:  # 0 for left mouse button
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                        pygame.time.delay(200)
                        return each.text
            if not hand:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            # updating screen
            pygame.display.flip()


# function that finds the shortest path between two given points in the maze
def path_finder(maze_object: Maze, start_pos: tuple, end: tuple, wall_block: str = "w"):
    maze = maze_object.maze
    q = queue.Queue()
    q.put((start_pos, [start_pos]))
    visited = set()

    while not q.empty():
        current_pos, path = q.get()
        col, row = current_pos

        if (col, row) == end:
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


# logging to file
def logging_setup():
    global logger
    logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files", "errors.txt"))
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    logger.addHandler(handler)


# catches exceptions idk, stackoverflow
def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error(f"Uncaught exception {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}",
                 exc_info=(exc_type, exc_value, exc_traceback,))

    error_button = Button(WIDTH // 2 - 300 // 2, HEIGHT // 2 - 50 // 2 - 50, 300, 50, COLORS["black"],
                     COLORS["black"], 5, COLORS["black"], ERROR_MESSAGE, 32)
    send_data_button = Button(WIDTH // 2 - 200 // 2, HEIGHT // 2 - 50 // 2, 200, 50, COLORS["black"],
                             COLORS["light_grey"], 5, COLORS["white"], "Send data", 24)
    exit_button = Button(WIDTH // 2 - 200 // 2, HEIGHT // 2 - 50 // 2 + 100, 200, 50, COLORS["black"],
                             COLORS["light_grey"], 5, COLORS["white"], "Quit", 24)
    sent = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        WINDOW.fill(COLORS["black"])
        error_button.draw(WINDOW)
        send_data_button.draw(WINDOW)
        exit_button.draw(WINDOW)
        if exit_button.is_over(WINDOW, pygame.mouse.get_pos()):
            if pygame.mouse.get_pressed()[0]:
                pygame.quit()
                sys.exit()
        elif not sent and send_data_button.is_over(WINDOW, pygame.mouse.get_pos()):
            if pygame.mouse.get_pressed()[0]:
                Database.active.send_error_data()
                sent = True
                send_data_button.outline_thickness = 0
                send_data_button.text = "Data sent! Thanks!"
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.flip()


def main():
    logging_setup()
    Database.initial_connection()

    main_menu = Menu("MAIN MENU", ("Speedrun mode", "Endless mode", "Online Highscores", "Local Highscores",
                                   "Controls", "Settings", "Quit"))
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        selection = main_menu.mainloop(WINDOW)
        if selection == "Speedrun mode":
            Main.speedrun_mode()
        elif selection == "Endless mode":
            Main.endless_mode()
        elif selection == "Controls":
            header = Button(WIDTH // 2 - 300 // 2, 100, 300, 50, COLORS["black"], COLORS["black"], 5, COLORS["white"],
                            "Controls", 30)
            text0 = Button(WIDTH // 2, 200, 0, 50, COLORS["black"], COLORS["black"], 0, COLORS["white"],
                           "WASD or/and Arrow Keys for movement", 24)
            text1 = Button(WIDTH // 2, 250, 0, 50, COLORS["black"], COLORS["black"], 0, COLORS["white"],
                           "Any printable keyboard character for name input", 24)
            text2 = Button(WIDTH // 2, 300, 0, 50, COLORS["black"], COLORS["black"], 0, COLORS["white"],
                           "Mouse for everyhing else", 24)
            exit_button = Button(WIDTH // 2 - 200 // 2, 450, 200, 50, COLORS["black"], COLORS["light_grey"], 5,
                                 COLORS["white"], "Back", 24)
            while True:
                Main.clock.tick(Main.settings["max fps"])
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                WINDOW.fill(COLORS["black"])
                header.draw(WINDOW)
                text0.draw(WINDOW)
                text1.draw(WINDOW)
                text2.draw(WINDOW)
                exit_button.draw(WINDOW)
                if exit_button.is_over(WINDOW, pygame.mouse.get_pos()):
                    if pygame.mouse.get_pressed()[0]:
                        pygame.time.delay(200)
                        break
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                pygame.display.flip()

        elif selection in ["Online Highscores", "Local Highscores"]:
            menu = Menu(f"Select {selection.split()[0].upper()} Highscores to display",
                        ("endless_all", "endless_all_custom", "speedrun_easy", "speedrun_easy_custom",
                         "speedrun_normal", "speedrun_normal_custom", "speedrun_hard", "speedrun_hard_custom",
                         "speedrun_full view", "speedrun_full view_custom", "Back"), outline=0, button_height=30)
            while True:
                Main.clock.tick(Main.settings["max fps"])
                sub_selection = menu.mainloop(WINDOW)
                if sub_selection == "Back":
                    break
                if selection == "Online Highscores":
                    Database.active.change_db_col("highscores", sub_selection)
                    my_list = [Database.active.col.find_one({"_id": i}) for i in range(1, 10)]
                else:
                    my_list = Main.highscores[sub_selection]

                converted_list = [f"{each['place']}. {each['name']}     ->     "
                                  + ((datetime.fromtimestamp(each['time']).strftime('%M:%S.%f')[:-3])
                                     if 'speedrun' in sub_selection else (str(each['score'])))
                                  + f"     ->     {str(each['seed'])+' '*(20 - len(str(each['seed'])))}"
                                  for each in my_list]
                converted_list.extend(["", "Back"])
                sub_menu = Menu(f"{sub_selection} {selection.split()[0].upper()}", tuple(converted_list),
                                outline=0, button_width=1000, button_height=30)
                while True:
                    Main.clock.tick(Main.settings["max fps"])
                    sub_sub_select = sub_menu.mainloop(WINDOW)
                    if sub_sub_select == "Back":
                        break

        elif selection == "Settings":
            Main.settings_gui()
        else:
            pygame.quit()
            sys.exit()


if __name__ == "__main__":
    sys.excepthook = handle_exception
    main()
