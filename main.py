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
    static_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    rect_shape = pymunk.Poly.create_box(static_body, size=size)
    rect_shape.body.position = body_pos

    # rect_shape.position = body_pos

    # rect_shape.elasticity = 0.0
    rect_shape.friction = 0
    space.add(static_body, rect_shape)
    return static_body, rect_shape


class GameRenderer:
    def __init__(self, game_objects):
        self.game_objects = game_objects

    def render(self, group, screen):
        [screen.blit(obj.image, (obj.pos[0] - game_global.cam_pos[0] * obj.parallax_x, obj.pos[1] - game_global.cam_pos[1] * obj.parallax_y)) for obj in sorted(group, key=lambda x: x.renderLayer)]

    def scene_start(self):
        pass


class GameManager:
    def __init__(self, keys_path, gravity):
        self.players = []
        self.buttons_pressed = set()
        self.move_input_axis = (0, 0)

        self.input_keys = {}
        self.load_keys(keys_path)

        surface = pygame.display.set_mode((1200, 680))
        self.draw_options = pymunk.pygame_util.DrawOptions(surface)

        self.cur_room = 0
        self.cam_speed = 50

        self.game_started = False
        self.game_time_max = 200
        self.game_time_left = self.game_time_max

    def load_keys(self, keys_path):
        f = open(keys_path).readlines()
        for i in f:
            k, v, v1 = i.split(';')
            self.input_keys[int(k)] = (v, v1.strip())

    def add_players(self, players):
        self.players += players

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
                #print(event.key)
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
            game_global.load_rnd_room()
        if game_global.cam_pos[0] < game_global.rooms_x[self.cur_room] * game_global.cell_size:
            game_global.cam_pos = (game_global.cam_pos[0] + self.cam_speed * game_global.cell_size * dt, game_global.cam_pos[1])
        game_global.cam_pos = (min(game_global.cam_pos[0], game_global.rooms_x[self.cur_room] * game_global.cell_size), game_global.cam_pos[1])

        if self.players[0].pos[0] > game_global.rooms_x[1] * game_global.cell_size and not self.game_started:
            self.game_started = True
            self.game_time_left = self.game_time_max
        if self.game_started:
            if self.game_time_left > 0:
                self.game_time_left -= 1/game_global.fps
                self.game_time_left -= dt
                # print(self.game_time_left)
            else:
                print('Game ended.')

        if self.players[0].pos[0] == min(self.players[0].pos[0], game_global.cam_pos[0] + 20):
            self.players[0].set_pos((game_global.cam_pos[0] + 21, self.players[0].pos[1]))

    def scene_start(self):
        pass


class GameGlobal:
    def __init__(self, game_objects=(), init_path='', sprites_path=(), prefabs_path='', keys_path='', fps=60, gravity=(0, 0), rooms=()):
        self.program_running = True
        self.cam_pos = (0, 0)
        self.fps = fps
        self.rooms = rooms
        self.rooms_x = [0]
        self.last_room_x = 0
        self.cell_size = 40
        self.placed_rooms = {}

        self.all_objects_group = pygame.sprite.Group()
        self.physical_objects_group = pygame.sprite.Group()
        self.collider_objects_group = pygame.sprite.Group()

        self.game_objects = game_objects
        self.game_renderer = GameRenderer(self.game_objects)
        self.game_manager = GameManager(keys_path, gravity)
        [obj.start() for obj in self.game_objects]
        self.collisions = {}

        for path in sprites_path:
            image = pygame.image.load(init_path + path[0])
            image = pygame.transform.scale(image, (image.get_width()*path[2], image.get_height()*path[2]))
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
        game_global.load_room(game_global.rooms[random.randrange(0, len(game_global.rooms))], cell_size=40, path_symbols='data/prefabs_symbols.txt')

    def load_room(self, path, **kwargs):
        if path in self.placed_rooms.keys() and self.placed_rooms[path][1] != self.last_room_x:
            print(self.placed_rooms[path][0][0].pos, self.placed_rooms[path][0][0].rect, self.placed_rooms[path][0][0].body.position, self.placed_rooms[path][0][0].body.mass)

            delta_x = (self.last_room_x - self.placed_rooms[path][1] + self.placed_rooms[path][2]) * self.cell_size
            [obj.translate((1, 0), delta_x) for obj in self.placed_rooms[path][0]]
            print(self.placed_rooms[path][0][0].pos, self.placed_rooms[path][0][0].rect, self.placed_rooms[path][0][0].body.position, delta_x, len(self.placed_rooms[path][0]))

            self.last_room_x += self.placed_rooms[path][2]
            self.placed_rooms[path][1] = self.last_room_x
            self.rooms_x += [self.last_room_x]
            print(self.placed_rooms[path][0][0].pos, self.placed_rooms[path][0][0].rect, self.placed_rooms[path][0][0].body.position, self.placed_rooms[path][0][0].body.mass)
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
                    self.anim_speeds[i] = self.tags[f'anim_{i}_speed'] if type(self.tags[f'anim_{i}_speed']) != tuple else random.randrange(self.tags[f'anim_{i}_speed'][0], self.tags[f'anim_{i}_speed'][1])
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


    def start(self):
        pass

    def update(self):
        self.rect.x, self.rect.y = self.pos
        if 'physical' in self.tags and self.tags['physical']:
            self.body.angle = 0
            self.pos = self.body.position[0] - self.size[0] / 2, self.body.position[1] - self.size[1] / 2
            self.body.velocity *= 0.99
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


class Player(GameObject):
    def __init__(self, prefab='', pos=(0, 0), scale=(1, 1), size=(40, 40), name='new_game_object', im='', color=(255, 255, 255), move_speed=1, jump_strength=1, **tags):
        super().__init__(prefab=prefab, pos=pos, scale=scale, size=size, name=name, im=im, color=color, **tags)
        self.move_input_axis = (0, 0)
        if self.move_speed is None:
            self.move_speed = move_speed
        if self.jump_strength is None:
            self.jump_strength = jump_strength

    def set_move_input_axis(self, vector=(0, 0)):
        self.scale = (self.scale[0], self.scale[1]) if vector[0] == self.move_input_axis[0] else (-self.scale[0], self.scale[1])
        self.move_input_axis = vector

    def update(self):
        super().update()
        self.body.velocity += (self.move_input_axis[0] * self.move_speed, 0)
        if abs(self.move_input_axis[0]) <= 0:
            self.cur_animation = 'stay'
            self.body.velocity = (self.body.velocity[0] * 0.8, self.body.velocity[1])
        else:
            self.cur_animation = 'move'
            self.body.velocity = (min(700, max(-700, self.body.velocity[0])), self.body.velocity[1])

    def jump(self):
        if abs(self.body.velocity[1]) < 0.5:
            self.impulse((0, self.jump_strength))

    def impulse(self, vector, reset=True):
        if reset:
            self.body.velocity = (0, 0)
        self.body.velocity += (0, -vector[1])


class Interactable(GameObject):
    def __init__(self, prefab='', pos=(0, 0), scale=(1, 1), size=(40, 40), name='button', im='', color=(255, 255, 255), **tags):
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
        else:
            self.is_pressed = False


class Movable(GameObject):
    def update(self):
        super().update()
        # self.translate((1, 0), game_global.fps / 100)
        # print(self.body.position, self.rect)
        self.body.position += (game_global.fps / 100, 0)
        self.rect.x, self.rect.y = self.body.position.x - self.rect[2] / 2, self.body.position.y - self.rect[3] / 2
        self.pos = self.rect.x, self.rect.y


def escape():
    game_global.program_running = False


if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption('Platformer alpha')
    size = width, height = 1200, 680  # 30x17 cells
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    window_size = pygame.display.get_surface().get_size()
    space = pymunk.Space()
    space.gravity = gravity=(0, 3200)

    images = {}
    game_global = GameGlobal(
        init_path='data/images/',
        sprites_path=(('bricks.png', 'bricks', 5), ('bricks1.png', 'bricks1', 5), ('bricks_bg.png', 'bricks_bg', 5), ('glass.png', 'glass', 5), ('sign.png', 'sign', 5), ('moon.png', 'moon', 5), ('player.png', 'player', 5),
                      ('player/player_stay1.png', 'player_stay1', 5), ('player/player_stay2.png', 'player_stay2', 5), ('player/player_stay3.png', 'player_stay3', 5), ('player/player_stay4.png', 'player_stay4', 5), ('player/player_move1.png', 'player_move1', 5), ('player/player_move2.png', 'player_move2', 5), ('player/player_move3.png', 'player_move3', 5), ('player/player_move4.png', 'player_move4', 5),
                      ('star0.png', 'star0', 5), ('button.png', 'button', 5), ('spring.png', 'spring', 5)),
        prefabs_path='data/prefabs.txt', keys_path='data/input_keys.txt',
        fps=60,
        rooms=('data/scenes/testroom.txt', 'data/scenes/testroom1.txt')
    )
    game_global.load_scene('data/scenes/test.txt', load_type='new', cell_size=40, path_symbols='data/prefabs_symbols.txt', path2='data/scenes/test_.txt', stars_path='data/scenes/star_map.txt')
    # print(*[el for el in game_global.collider_objects_group])
    while game_global.program_running:
        screen.fill((0, 10, 10))
        dt = clock.tick(game_global.fps) / 1000
        game_global.update(dt)
        game_global.render(screen)
        space.step(dt * 40 / 60)
        space.debug_draw(game_global.game_manager.draw_options)
        pygame.display.flip()
    pygame.quit()