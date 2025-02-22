import pygame
import math
import random
import pymunk
import pymunk.pygame_util
from random import randrange

pymunk.pygame_util.positive_y_is_up = False
game_global = None


def create_rigidbody(space, pos, size):
    body_pos = pos[0] + size[0] / 2, pos[1] + size[1] / 2
    square_mass, square_size = 1, size
    square_moment = pymunk.moment_for_box(square_mass, square_size)
    square_body = pymunk.Body(square_mass, square_moment)
    square_body.position = body_pos
    square_shape = pymunk.Poly.create_box(square_body, square_size)
    square_shape.elasticity = 0.0
    square_shape.friction = 1.0

    # square_shape.position = body_pos

    square_shape.color = [randrange(256) for i in range(4)]
    space.add(square_body, square_shape)
    return square_body, square_shape


def create_static_collider(space, pos, size):
    body_pos = pos[0] + size[0] / 2, pos[1] + size[1] / 2

    static_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    static_body.position = body_pos

    rect_shape = pymunk.Poly.create_box(static_body, size=size)
    rect_shape.friction = 0  # Устанавливаем трение

    # Добавляем тело и форму в пространство
    space.add(static_body, rect_shape)

    return static_body, rect_shape


def play(val):  # Play sound by name
    if val in game_global.game_manager.sounds.keys():
        sound = game_global.game_manager.sounds[val]
        sound.play()


class GameRenderer:
    def __init__(self, game_objects):
        self.game_objects = game_objects

    def restart(self):
        self.game_objects = []

    def render(self, group, screen):
        [screen.blit(obj.image, (
        obj.pos[0] - game_global.cam_pos[0] * obj.parallax_x, obj.pos[1] - game_global.cam_pos[1] * obj.parallax_y)) for
        obj in sorted(group, key=lambda x: x.renderLayer)]

    def render_objects(self, objects):
        [screen.blit(obj[0],(obj[1][0] - game_global.cam_pos[0] * obj[2], obj[1][1] - game_global.cam_pos[1] * obj[2])) for obj in objects]


    def scene_start(self):
        pass


class GameManager:
    def __init__(self, keys_path, audio_path, sounds, player_data_path):
        self.players = []
        self.buttons_pressed = set()
        self.move_input_axis = (0, 0)

        self.player_data = {}
        self.player_data_path = player_data_path
        self.load_player_data()

        self.input_keys = {}
        self.load_keys(keys_path)

        surface = pygame.display.set_mode((1200, 680))
        self.draw_options = pymunk.pygame_util.DrawOptions(surface)

        self.cur_room = 0
        self.rooms_count_max = 15 + 3
        self.rooms_count = 0
        self.cam_speed = 50

        self.game_started = False
        self.game_time_max = int(self.player_data['upgrade_level']) * 20
        self.game_time_left = self.game_time_max
        self.view_end_screen = False
        self.time_before_view_end_screen = -1

        self.exp_all = int(self.player_data['exp'])
        self.exp_got = -3

        self.sounds = {}
        for s in sounds:
            self.sounds[s[1]] = pygame.mixer.Sound(audio_path + s[0])
            self.sounds[s[1]].set_volume(s[2])

        self.texts_info = {}
        self.view_end_screen_objects = {}

    def load_player_data(self):
        f = open(self.player_data_path).readlines()
        self.player_data = {}
        for i in f:
            k, v = i.split('=')
            self.player_data[k.strip()] = v.strip()

    def save_player_data(self):
        f = open(self.player_data_path, mode='w')
        for k, v in self.player_data.items():
            print(f'{k}={v}', file=f)

    def load_keys(self, keys_path):
        f = open(keys_path).readlines()
        for i in f:
            k, v, v1 = i.split(';')
            self.input_keys[int(k)] = (v, v1.strip())

    def add_players(self, players):
        self.players += players

        if 'player' not in self.texts_info.keys():
            self.texts_info['player'] = [font.render('', True, (40, 40, 40)), (10, 50), 0]
            self.texts_info['exp'] = [font.render('', True, (40, 40, 40)), (10, 10), 0]

    def add_move_input_axis(self, vector=(0, 0)):
        if self.game_time_left > 0:
            self.move_input_axis = (self.move_input_axis[0] + vector[0], self.move_input_axis[1] + vector[1])

    def jump(self):
        if self.game_time_left > 0:
            [player.jump() for player in self.players]

    def update(self, dt):
        self.move_input_axis = (0, 0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_global.program_running = False
            if event.type == pygame.KEYDOWN:
                for k, v in self.input_keys.items():
                    if event.key == k:
                        if v[1] == '1':
                            # print(k)
                            eval(v[0])
                # print(event.key)
        keys = pygame.key.get_pressed()
        for k, v in self.input_keys.items():
            if keys[k]:
                if v[1] == '0':
                    eval(v[0])
        [player.set_move_input_axis(self.move_input_axis) for player in self.players]

        for i in range(len(game_global.rooms_x)):
            if self.players[0].pos[0] > game_global.rooms_x[i] * game_global.cell_size:
                self.cur_room = i
        if self.players[0].pos[0] > game_global.rooms_x[-1] * game_global.cell_size:
            if self.rooms_count < self.rooms_count_max:
                game_global.load_rnd_room()
            elif not self.view_end_screen and self.time_before_view_end_screen == -1:
                # self.view_end_screen = True
                # self.open_end_screen()
                space.gravity = (200, -50)
                self.players[0].set_move_input_axis((0, 0))
                self.players[0].controlling = False
                self.time_before_view_end_screen = 5

        if self.view_end_screen:
            if self.time_before_restart >= 0:
                self.view_end_screen_objects['restart_at'][0] = font.render('Restart in: ' + str((self.time_before_restart * 10) // 1 / 10), True, (240, 240, 240))
                self.time_before_restart -= dt
            else:
                # print('RESTART>>>>>')
                game_global.restart()
                return

            if self.anim_time >= 0:
                self.view_end_screen_objects['bg'][0].fill((self.anim_time / self.anim_delta * 100, self.anim_time / self.anim_delta * 100, self.anim_time / self.anim_delta * 100))
                self.view_end_screen_objects['time'][1] = ((1 - self.anim_time / self.anim_delta) * 150, self.view_end_screen_objects['time'][1][1])
                self.view_end_screen_objects['rooms_completed'][1] = ((1 - max(self.anim_time - 0.2, 0) / self.anim_delta) * 150, self.view_end_screen_objects['rooms_completed'][1][1])
                self.view_end_screen_objects['exp'][1] = ((1 - max(self.anim_time - 0.4, 0) / self.anim_delta) * 150, self.view_end_screen_objects['exp'][1][1])
                self.view_end_screen_objects['exp_now'][1] = ((1 - max(self.anim_time - 0.6, 0) / self.anim_delta) * 150, self.view_end_screen_objects['exp_now'][1][1])
                self.view_end_screen_objects['restart_at'][1] = ((1 - max(self.anim_time - 1, 0) / self.anim_delta) * 150, self.view_end_screen_objects['restart_at'][1][1])

                self.anim_time -= dt

        if game_global.cam_pos[0] < game_global.rooms_x[self.cur_room] * game_global.cell_size:
            game_global.cam_pos = (game_global.cam_pos[0] + self.cam_speed * game_global.cell_size * dt, game_global.cam_pos[1])
        game_global.cam_pos = (min(game_global.cam_pos[0], game_global.rooms_x[self.cur_room] * game_global.cell_size), game_global.cam_pos[1])

        if self.players[0].pos[0] > game_global.rooms_x[1] * game_global.cell_size and not self.game_started:
            self.game_started = True
            self.game_time_left = self.game_time_max
        if self.game_started and not self.view_end_screen:
            if self.time_before_view_end_screen == -1:
                if self.game_time_left > 0:
                    self.game_time_left -= dt
                    # print(self.game_time_left)
                else:
                    self.view_end_screen = True
                    self.open_end_screen()
            else:
                if self.time_before_view_end_screen > 0:
                    self.time_before_view_end_screen -= dt
                else:
                    self.time_before_view_end_screen = -1
                    self.view_end_screen = True
                    self.open_end_screen()


        if self.players[0].pos[0] == min(self.players[0].pos[0], game_global.cam_pos[0] + 20):
            self.players[0].set_pos((game_global.cam_pos[0] + 21, self.players[0].pos[1]))

        if self.game_started:
            if self.game_time_left >= 0:
                self.texts_info['player'][0] = font.render('Time left: ' + str(int(self.game_time_left)), True, (40, 40, 40))
                self.texts_info['exp'][0] = font.render('Exp got: ' + str(int(self.exp_got)), True, (40, 40, 40))
        else:
            self.texts_info['player'][0] = font.render('', True, (40, 40, 40))
            self.texts_info['exp'][0] = font.render('Exp now: ' + str(self.exp_all), True, (40, 40, 40))

    def open_end_screen(self):
        self.anim_time = 2
        self.anim_delta = self.anim_time
        self.time_before_restart = 10

        self.exp_all += self.exp_got
        self.player_data['exp'] = str(self.exp_all)

        new_record = False
        if self.game_time_left > int(self.player_data['best_time']):
            self.player_data['best_time'] = str(int(self.game_time_max - self.game_time_left))
            new_record = True

        self.view_end_screen_objects['bg'] = [pygame.Surface((width, height)), (0, 0), 0]
        self.view_end_screen_objects['bg'][0].fill((100, 100, 100))
        self.view_end_screen_objects['time'] =[font.render(f'Time: {self.game_time_max - max((int(self.game_time_left), 0))} {"(New record)" if new_record else ""}', True, (240, 240, 240) if not new_record else (240, 240, 0)), (150, 50), 0]
        self.view_end_screen_objects['rooms_completed'] = [font.render('Rooms completed: ' + str(self.rooms_count - 3), True, (240, 240, 240)), (150, 100), 0]
        self.view_end_screen_objects['exp'] = [font.render('Exp got: ' + str(self.exp_got), True, (240, 240, 240)), (150, 150), 0]
        self.view_end_screen_objects['exp_now'] = [font.render('Exp now: ' + str(self.exp_all), True, (240, 240, 240)), (150, 200), 0]
        self.view_end_screen_objects['restart_at'] = [font.render('Restart in: ' + str(self.time_before_restart), True, (240, 240, 240)), (150, height - 50), 0]

        if self.exp_all > 8 * int(self.player_data['upgrade_level']):
            self.player_data['upgrade_level'] = str(int(self.player_data['upgrade_level']) + 1)
            if int(self.player_data['upgrade_level']) >= 5:
                self.player_data['upgrade_level'] = str(5)
                self.view_end_screen_objects['upgrade_level'] = [font.render('Level 5 (MAX)', True, (0, 240, 0)), (150, height - 100), 0]
            else:
                self.view_end_screen_objects['upgrade_level'] = [font.render('Level upgraded to ' + self.player_data['upgrade_level'], True, (240, 240, 0)), (150, height - 100), 0]

        self.save_player_data()

    def scene_start(self):
        pass


class GameGlobal:
    def __init__(self, game_objects=(), init_path='', sprites_path=(), prefabs_path='', keys_path='', fps=60, rooms=(), audio_path='', music='', sounds=(), player_data_path=''):
        global game_global
        game_global = self

        self.program_running = None
        self.cam_pos = None
        self.last_room_x = None
        self.rooms_x = None
        self.cell_size = None
        self.placed_rooms = None

        self.all_objects_group = None
        self.physical_objects_group = None
        self.collider_objects_group = None

        pygame.mixer.init()
        pygame.mixer.music.load(audio_path + music)
        pygame.mixer.music.play(-1)

        self.game_objects = None
        self.game_renderer = GameRenderer(self.game_objects)
        self.game_manager_init_data = (keys_path, audio_path, sounds, player_data_path)
        self.game_manager = None
        self.collisions = {}

        for path in sprites_path:
            image = pygame.image.load(init_path + path[0])
            image = pygame.transform.scale(image, (image.get_width() * path[2], image.get_height() * path[2]))
            images[path[1]] = image

        self.prefabs = {}
        prefabs_f = open(prefabs_path, encoding='utf-8').readlines()
        for i in prefabs_f:
            prefab_name, prefab_object = i.split(':')
            self.prefabs[prefab_name.strip()] = {}
            prefab_object = prefab_object.strip().strip('(').strip(')')
            texts = prefab_object.split(',')
            for t in range(len(texts) - 1):
                if texts[t] is None:
                    continue
                if texts[t].count('(') > texts[t].count(')'):
                    texts[t] = texts[t] + ',' + texts[t + 1]
                    texts[t + 1] = None
            texts = list(filter(lambda x: x is not None, texts))
            for j in texts:
                k, v = j.split('=')
                if not k.strip().startswith('*'):
                    self.prefabs[prefab_name.strip()][k.strip()] = v.strip()
                else:
                    if 'tags' not in self.prefabs[prefab_name.strip()].keys():
                        self.prefabs[prefab_name.strip()]['tags'] = {}
                    self.prefabs[prefab_name.strip()]['tags'][k.strip().lstrip('*')] = v.strip()

        self.restart_data = (fps, rooms, game_objects)
        self.restart()

    def restart(self):
        global space
        fps, rooms, game_objects = self.restart_data

        space = pymunk.Space()
        space.gravity = (0, 3200)

        self.program_running = True
        self.cam_pos = (0, 0)
        self.last_room_x = 0
        self.rooms_x = [0]
        self.cell_size = 40
        self.placed_rooms = {}

        self.fps = fps
        self.rooms = rooms

        self.all_objects_group = pygame.sprite.Group()
        self.physical_objects_group = pygame.sprite.Group()
        self.collider_objects_group = pygame.sprite.Group()
        if self.game_manager is not None:
            self.game_manager.active = False
            del self.game_manager
        self.game_manager = GameManager(*self.game_manager_init_data)
        if self.game_objects is not None:
            del self.game_objects
        self.game_objects = game_objects
        self.game_renderer.restart()
        [obj.start() for obj in self.game_objects]

        load_scene()

    def scene_start(self):
        self.game_renderer.scene_start()
        self.game_manager.scene_start()

        self.game_manager.add_players(self.find_objects_with_class('Player'))
        # self.collider_objects = self.find_objects_with_tag('has_collider', True)

    def load_scene(self, path, load_type='new', **kwargs):
        f0 = open(path, encoding='utf-8').readlines()
        if load_type == 'old':
            for f1 in f0:
                f2 = f1.split(':')
                f = f2[1].split(';')
                f = [i.strip() for i in f]
                game_objects = [eval(f'{f2[0]}{f[i]}') for i in range(len(f))]
                self.add_game_objects(tuple(game_objects))
        else:
            self.load_room(kwargs['stars_path'], add_x=False, **kwargs)
            self.load_room(path, **kwargs)
            self.load_scene(path=kwargs['path2'], load_type='old')
            self.load_rnd_room()
        self.scene_start()
        return path

    def load_rnd_room(self):
        self.load_room(
            self.rooms[random.randrange(0, len(self.rooms))], cell_size=40, path_symbols='data/prefabs_symbols.txt'
        )

    def load_room(self, path, **kwargs):
        self.cur_room_path = path
        self.game_manager.rooms_count += 1
        self.game_manager.exp_got += 1

        if path in self.placed_rooms.keys() and self.placed_rooms[path][1] != self.last_room_x:
            # print(self.placed_rooms[path][0][0].pos, self.placed_rooms[path][0][0].rect,
            #       self.placed_rooms[path][0][0].body.position, self.placed_rooms[path][0][0].body.mass)

            delta_x = (self.last_room_x - self.placed_rooms[path][1] + self.placed_rooms[path][2]) * self.cell_size
            [obj.translate((1, 0), delta_x) for obj in self.placed_rooms[path][0]]
            [obj.reset() for obj in self.placed_rooms[path][0]]
            # print(self.placed_rooms[path][0][0].pos, self.placed_rooms[path][0][0].rect,
            #       self.placed_rooms[path][0][0].body.position, delta_x, len(self.placed_rooms[path][0]))

            self.last_room_x += self.placed_rooms[path][2]
            self.placed_rooms[path][1] = self.last_room_x
            self.rooms_x += [self.last_room_x]
            # print(self.placed_rooms[path][0][0].pos, self.placed_rooms[path][0][0].rect,
            #       self.placed_rooms[path][0][0].body.position, self.placed_rooms[path][0][0].body.mass)
            return

        room_objects = []
        self.cell_size = kwargs["cell_size"]

        f0 = open(path, encoding='utf-8').readlines()
        fsymbols = open(kwargs['path_symbols'], encoding='utf-8').readlines()
        prf = {}
        for fs in fsymbols:
            k, v = fs.split(' ')
            v1, v2 = v.strip().split(':')
            k, v1, v2 = k.strip(), v1.strip(), v2.strip()
            prf[k] = (v1, v2)
        game_objects = []
        for x in range(len(f0)):
            for y in range(len(f0[x])):
                if f0[x][y].strip() in prf.keys():
                    v3 = prf[f0[x][y].strip()][1].rstrip(
                        ')') + f', pos=({(y + self.last_room_x) * kwargs["cell_size"]}, {x * kwargs["cell_size"]}))'
                    room_objects += [eval(f'{prf[f0[x][y].strip()][0]}{v3}')]
        if 'add_x' in kwargs and kwargs['add_x'] == False:
            pass
        else:
            self.last_room_x += len(f0[0]) - 1
            self.rooms_x += [self.last_room_x]
        game_objects += room_objects
        self.add_game_objects(tuple(game_objects))
        self.placed_rooms[path] = [room_objects, self.last_room_x, len(f0[0]) - 1]
        # print(self.placed_rooms[path])
        # print(len(self.placed_rooms[path]), len(self.placed_rooms[path][0]), len(f0[0]))

    def add_game_objects(self, game_objects=()):
        self.game_objects += game_objects
        self.game_renderer.game_objects += game_objects

    def find_objects_with_class(self, text):
        return list(filter(lambda x: x.__class__.__name__ == text, self.game_objects))

    def find_objects_with_tag(self, k, v):
        return list(filter(lambda x: k in x.tags.keys() and x.tags[k] == v, self.game_objects))

    def update(self, dt):
        # self.game_renderer.update()
        self.game_manager.update(dt)
        [obj.update() for obj in self.game_objects]

        # print(self.placed_rooms[self.rooms[0]][0][0].pos, self.placed_rooms[self.rooms[0]][0][0].rect, self.placed_rooms[self.rooms[0]][0][0].body.position)

    def render(self, screen):
        self.game_renderer.render(self.all_objects_group, screen)
        self.game_renderer.render_objects(self.game_manager.texts_info.values())
        if self.game_manager.view_end_screen and len(self.game_manager.view_end_screen_objects) > 0:
            self.game_renderer.render_objects(self.game_manager.view_end_screen_objects.values())


class GameObject(pygame.sprite.Sprite):
    def __init__(self, prefab='', pos=(0, 0), scale=(1, 1), size=(40, 40), name='new_game_object', im='', color=(255, 255, 255), **tags):
        super().__init__(game_global.all_objects_group)

        self.pos, self.size, self.scale, self.name, self.im, self.color = [None] * 6
        self.tags = {}
        if prefab != '' and prefab in game_global.prefabs.keys():
            for k in game_global.prefabs[prefab].keys():
                if k != 'tags':
                    setattr(self, k, eval(game_global.prefabs[prefab][k]))
                else:
                    for key, value in game_global.prefabs[prefab][k].items():
                        self.tags[key] = eval(game_global.prefabs[prefab]['tags'][str(key)])

        if self.pos is None:
            self.pos = pos
        if self.size is None:
            self.size = size
        if self.scale is None:
            self.scale = scale
        if self.name is None:
            self.name = name
        if self.im is None:
            self.im = im
        if self.color is None:
            self.color = color

        for k, v in tags.items():
            if k not in self.tags.keys():
                self.tags[k] = v

        self.image = images[self.im]
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self.image = pygame.transform.scale(self.image, (self.get_transform()[2], self.get_transform()[3]))

        if 'has_collider' in self.tags and self.tags['has_collider']:
            self.add(game_global.collider_objects_group)
            self.body, self.shape = create_static_collider(space, self.pos, self.size)
            if 'print_target' in self.tags:
                print('SP', self.body.position, self.pos)

        if 'physical' in self.tags and self.tags['physical']:
            self.add(game_global.physical_objects_group)
            self.body, self.shape = create_rigidbody(space, self.pos, self.size)

        self.renderLayer = 0
        if 'layer' in self.tags:
            self.renderLayer = int(self.tags['layer'])

        if 'mult_sprites' in self.tags:
            self.anim_speeds = {}
            for i in self.tags['animations'].split():
                if f'anim_{i}_speed' in self.tags:
                    self.anim_speeds[i] = self.tags[f'anim_{i}_speed'] if type(
                        self.tags[f'anim_{i}_speed']) != tuple else random.randrange(self.tags[f'anim_{i}_speed'][0],
                                                                                     self.tags[f'anim_{i}_speed'][1])
                else:
                    self.anim_speeds[i] = 1
            self.cur_image = 0
            self.cur_animation = self.tags['animations'].split()[0]
            self.mult_sprites = self.tags['mult_sprites'].split()

        if 'parallax' in self.tags:
            self.parallax_x, self.parallax_y = self.tags['parallax']
        else:
            self.parallax_x, self.parallax_y = 1, 1

        if 'size_delta' in self.tags:
            val = random.randrange(-10, 10) * self.tags['size_delta']
            self.size = (self.size[0] + val, self.size[1] + val)
        if 'pos_delta' in self.tags:
            val = random.randrange(-100, 100) * self.tags['pos_delta']
            self.pos = (self.pos[0] + val, self.pos[1] + val)
            self.rect.x, self.rect.y = pos

        self.reset()

    def start(self):
        pass

    def update(self):
        self.rect.x, self.rect.y = self.pos
        if 'physical' in self.tags and self.tags['physical']:
            self.body.angle = 0
            self.pos = self.body.position[0] - self.size[0] / 2, self.body.position[1] - self.size[1] / 2
            self.body.velocity *= 0.99
        if 'has_collider' in self.tags and self.tags['has_collider']:
            self.pos = self.body.position[0] - self.size[0] / 2, self.body.position[1] - self.size[1] / 2
        if 'mult_sprites' in self.tags:
            if int(self.cur_image) < self.tags[f'anim_{self.cur_animation}_borders'][0]:
                self.cur_image = self.tags[f'anim_{self.cur_animation}_borders'][1]
            if int(self.cur_image) > self.tags[f'anim_{self.cur_animation}_borders'][1]:
                self.cur_image = self.tags[f'anim_{self.cur_animation}_borders'][0]
            self.image = images[self.mult_sprites[int(self.cur_image)]]
            self.cur_image += 1 * self.anim_speeds[self.cur_animation] / game_global.fps

        if 'print_target' in self.tags:
            print('X', self.body.position, self.pos[0])

    def on_collision(self, other):
        pass

    def on_collision_exit(self, other):
        pass

    def get_transform(self):
        return self.pos[0], self.pos[1], self.size[0] * self.scale[0], self.size[1] * self.scale[1]

    def translate(self, vector=(0, 0), strength=1):
        self.pos = (self.pos[0] + vector[0] * strength, self.pos[1] + vector[1] * strength)
        self.rect.x, self.rect.y = self.pos
        if 'has_collider' in self.tags:
            self.body.position = (self.pos[0] + self.size[0] / 2, self.pos[1] + self.size[1] / 2)
            if 'print_target' in self.tags:
                print('TR', self.body.position, self.pos[0])

    def set_pos(self, vector):
        self.pos = vector
        self.rect.x, self.rect.y = self.pos
        if 'has_collider' in self.tags:
            self.body.position = (self.pos[0] + self.size[0] / 2, self.pos[1] + self.size[1] / 2)
            if 'print_target' in self.tags:
                print(self.body.position, self.pos[0])

    def __str__(self):
        return f'GameObject {self.name} {self.get_transform()}'

    def reset(self):
        pass


class Player(GameObject):
    def __init__(self, prefab='', pos=(0, 0), scale=(1, 1), size=(40, 40), name='new_game_object', im='',
                 color=(255, 255, 255), move_speed=1, jump_strength=1, **tags):
        super().__init__(prefab=prefab, pos=pos, scale=scale, size=size, name=name, im=im, color=color, **tags)
        self.move_input_axis = (0, 0)
        if self.move_speed is None:
            self.move_speed = move_speed
        if self.jump_strength is None:
            self.jump_strength = jump_strength
        self.controlling = True

    def set_move_input_axis(self, vector=(0, 0)):
        if self.controlling:
            self.move_input_axis = vector

    def update(self):
        super().update()
        self.body.velocity += (self.move_input_axis[0] * self.move_speed, 0)
        if abs(self.move_input_axis[0]) <= 0:
            self.cur_animation = 'stay'
            self.body.velocity = (self.body.velocity[0] * 0.8 if self.controlling else self.body.velocity[0] * 0.95, self.body.velocity[1])
        else:
            self.cur_animation = 'move'
            self.body.velocity = (min(700, max(-700, self.body.velocity[0])), self.body.velocity[1])

    def jump(self):
        if abs(self.body.velocity[1]) < 1:
            self.impulse((0, self.jump_strength))
            play('jump')

    def impulse(self, vector, reset=True):
        if reset:
            self.body.velocity = (0, 0)
        self.body.velocity += (0, -vector[1])


class Interactable(GameObject):
    def __init__(self, prefab='', pos=(0, 0), scale=(1, 1), size=(40, 40), name='button', im='', color=(255, 255, 255),
                 **tags):
        super().__init__(prefab=prefab, pos=pos, scale=scale, size=size, name=name, im=im, color=color, **tags)
        self.is_pressed = False
        if "func" in self.tags:
            self.func = self.tags["func"]

    def update(self):
        super().update()
        if self.rect.colliderect(game_global.game_manager.players[0].rect):
            if not self.is_pressed:
                self.is_pressed = True
                eval(self.func)
                if 'sound' in self.tags:
                    play(self.tags['sound'])
        else:
            self.is_pressed = False

        if self.is_pressed:
            self.cur_animation = 'used'
        else:
            self.cur_animation = 'default'

    def reset(self):
        pass


class Button(Interactable):
    def update(self):
        super().update()

        if self.door_to_open is None:
            if game_global.cur_room_path in game_global.placed_rooms.keys():
                variants = list(filter(lambda x: x.__class__ == Door and not x.inverted and x.pos[0] > self.last_room_x, game_global.placed_rooms[self.cur_room][0]))
                if len(variants) > 0:
                    self.door_to_open = variants[0]
            else:
                self.door_to_open = None

    def reset(self):
        self.cur_room = game_global.cur_room_path
        self.last_room_x = game_global.last_room_x * game_global.cell_size

        if game_global.cur_room_path in game_global.placed_rooms.keys():
            variants = list(filter(lambda x: x.__class__ == Door and not x.inverted and x.pos[0] > self.last_room_x, game_global.placed_rooms[self.cur_room][0]))
            if len(variants) > 0:
                self.door_to_open = variants[0]
            else:
                self.door_to_open = None
        else:
            self.door_to_open = None


class Door(GameObject):
    def __init__(self, prefab='', pos=(0, 0), scale=(1, 1), size=(40, 40), name='button', im='', color=(255, 255, 255),
                 **tags):
        self.start_pos = None
        self.opened = False
        super().__init__(prefab=prefab, pos=pos, scale=scale, size=size, name=name, im=im, color=color, **tags)

    def update(self):
        super().update()

        if self.opened:
            if self.pos[1] > self.start_pos[1] - self.size[1] + 45:
                self.translate((0, -1), 5)
            self.cur_animation = 'opened'
            self.renderLayer = -4
        else:
            if self.pos[1] < self.start_pos[1]:
                self.translate((0, 1), 5)
            self.cur_animation = 'closed' if not self.inverted else 'opened'
            self.renderLayer = 1

        if game_global.game_manager.players[0].pos[0] > self.pos[0] + self.rect[2] / 2:
            self.opened = False

    def open(self):
        if not self.opened:
            self.opened = True
            play('door')

    def reset(self):
        self.inverted = ('inverted' in self.tags.keys() and self.tags['inverted'])
        self.opened = self.inverted
        if self.start_pos is not None:
            self.pos = self.start_pos if not self.inverted else (self.start_pos[0] - self.size[1] + 45, self.start_pos[1])
        self.start_pos = self.pos


def escape():
    game_global.program_running = False


def load_scene():
    game_global.load_scene('data/scenes/main_room.txt', load_type='new', cell_size=40,
                    path_symbols='data/prefabs_symbols.txt', path2='data/scenes/main_room_.txt',
                    stars_path='data/scenes/star_map.txt')


if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption('BEERKO')
    size = width, height = 1200, 680  # 30x17 cells
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    window_size = pygame.display.get_surface().get_size()
    space = None

    font = pygame.font.Font('data/retro_computer_personal_use.ttf', 20)

    images = {}
    game_global = None
    GameGlobal(
        init_path='data/images/',
        sprites_path=(('bricks.png', 'bricks', 5), ('bricks1.png', 'bricks1', 5), ('bricks_bg.png', 'bricks_bg', 5),
                      ('glass.png', 'glass', 5), ('sign.png', 'sign', 5), ('moon.png', 'moon', 5),
                      ('rofler.png', 'test', 5),
                      ('player/player_stay1.png', 'player_stay1', 5), ('player/player_stay2.png', 'player_stay2', 5),
                      ('player/player_stay3.png', 'player_stay3', 5), ('player/player_stay4.png', 'player_stay4', 5),
                      ('player/player_move1.png', 'player_move1', 5), ('player/player_move2.png', 'player_move2', 5),
                      ('player/player_move3.png', 'player_move3', 5), ('player/player_move4.png', 'player_move4', 5),
                      ('star0.png', 'star0', 5), ('button.png', 'button', 5),
                      ('button_clicked.png', 'button_clicked', 5), ('spring.png', 'spring', 5), ('spring_used.png', 'spring1', 5),
                      ('door_closed.png', 'door_closed', 5), ('door_opened.png', 'door_opened', 5)),
        prefabs_path='data/prefabs.txt', keys_path='data/input_keys.txt',
        fps=60,
        rooms=('data/scenes/room.txt', 'data/scenes/room1.txt', 'data/scenes/room2.txt', 'data/scenes/room3.txt',
               'data/scenes/room4.txt', 'data/scenes/room5.txt'),
        audio_path='data/audio/', music='SpacyFood.mp3',
        sounds=(('jump.wav', 'jump', 0.5), ('spring.wav', 'spring', 0.5), ('door_open.wav', 'door', 0.5),
                ('button_clicked.wav', 'button', 0.5)),
        player_data_path='data/player_data.txt'
    )

    while game_global.program_running:
        screen.fill((0, 10, 10))
        dt = clock.tick(game_global.fps) / 1000
        game_global.update(dt)
        game_global.render(screen)
        space.step(dt * 40 / 60)
        # space.debug_draw(game_global.game_manager.draw_options)
        pygame.display.flip()
    pygame.quit()
