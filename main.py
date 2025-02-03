import pygame
import math
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
    square_shape.color = [randrange(256) for i in range(4)]
    space.add(square_body, square_shape)
    return square_body, square_shape


def create_static_collider(space, pos, size):
    body_pos = pos[0] + size[0] / 2, pos[1] + size[1] / 2
    static_body = space.static_body
    rect_shape = pymunk.Poly.create_box(static_body, size=size)
    rect_shape.body.position = body_pos
    # rect_shape.elasticity = 0.0
    rect_shape.friction = 0
    space.add(rect_shape)
    return static_body, rect_shape


class GameRenderer:
    def __init__(self, game_objects):
        self.game_objects = game_objects

    def render(self, group, screen):
        [screen.blit(obj.image, (obj.pos[0] - game_global.cam_pos[0], obj.pos[1] - game_global.cam_pos[1])) for obj in group]

    def scene_start(self):
        pass


class GameManager:
    def __init__(self, keys_path, gravity):
        self.players = []
        self.buttons_pressed = set()
        self.move_input_axis = (0, 0)

        self.input_keys = {}
        self.load_keys(keys_path)

        self.space = pymunk.Space()
        self.space.gravity = gravity
        surface = pygame.display.set_mode((1200, 680))
        self.draw_options = pymunk.pygame_util.DrawOptions(surface)

    def load_keys(self, keys_path):
        f = open(keys_path).readlines()
        for i in f:
            k, v, v1 = i.split(';')
            self.input_keys[int(k)] = (v, v1.strip())

    def add_players(self, players):
        self.players += players

    def add_move_input_axis(self, vector=(0, 0)):
        self.move_input_axis = (self.move_input_axis[0] + vector[0], self.move_input_axis[1] + vector[1])

    def jump(self):
        [player.jump() for player in self.players]


    def update(self):
        self.move_input_axis = (0, 0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_global.program_running = False
            if event.type == pygame.MOUSEWHEEL:
                game_global.cam_pos = (game_global.cam_pos[0] + event.x, game_global.cam_pos[1] - event.y)
            if event.type == pygame.KEYDOWN:
                for k, v in self.input_keys.items():
                    if event.key == k:
                        if v[1] == '1':
                            # print(k)
                            eval(v[0])
                # if event.key == pygame.K_w:
                #     [player.jump() for player in self.players]
                #     print(event.key)
        keys = pygame.key.get_pressed()
        for k, v in self.input_keys.items():
            if keys[k]:
                if v[1] == '0':
                    eval(v[0])
        [player.set_move_input_axis(self.move_input_axis) for player in self.players]


    def scene_start(self):
        pass


class GameGlobal:
    def __init__(self, game_objects=(), init_path='', sprites_path=(), prefabs_path='', keys_path='', fps=60, gravity=(0, 0)):
        self.program_running = True
        self.cam_pos = (0, 0)
        self.fps = fps

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
                        v3 = prf[f0[x][y].strip()][1].rstrip(')') + f', pos=({y * kwargs["cell_size"]}, {x * kwargs["cell_size"]}))'
                        game_objects += [eval(f'{prf[f0[x][y].strip()][0]}{v3}')]
            self.add_game_objects(tuple(game_objects))
            self.load_scene(path=kwargs['path2'], load_type='old')
        self.scene_start()
        return path

    def add_game_objects(self, game_objects=()):
        self.game_objects += game_objects
        self.game_renderer.game_objects += game_objects

    def find_objects_with_class(self, text):
        return list(filter(lambda x: x.__class__.__name__ == text, self.game_objects))

    def find_objects_with_tag(self, k, v):
        return list(filter(lambda x: k in x.tags.keys() and x.tags[k] == v, self.game_objects))

    def update(self):
        # self.game_renderer.update()
        self.game_manager.update()
        [obj.update() for obj in self.game_objects]


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
            self.body, self.shape = create_static_collider(game_global.game_manager.space, self.pos, self.size)

        if 'physical' in self.tags and self.tags['physical']:
            self.add(game_global.physical_objects_group)
            self.body, self.shape = create_rigidbody(game_global.game_manager.space, self.pos, self.size)


    def start(self):
        pass

    def update(self):
        self.rect.x, self.rect.y = self.pos
        if 'physical' in self.tags and self.tags['physical']:
            self.body.angle = 0
            # self.body.angular_velocity = 0
            self.pos = self.body.position[0] - self.size[0] / 2, self.body.position[1] - self.size[1] / 2
            self.body.velocity *= 0.99
            # self.body.


    def on_collision(self, other):
        pass

    def on_collision_exit(self, other):
        pass

    def get_transform(self):
        return self.pos[0], self.pos[1], self.size[0] * self.scale[0], self.size[1] * self.scale[1]

    def translate(self, vector=(0, 0), strength=1):
        self.pos = (self.pos[0] + vector[0] * strength, self.pos[1] + vector[1] * strength)

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
        self.move_input_axis = vector

    def update(self):
        super().update()
        self.body.velocity += (self.move_input_axis[0] * self.move_speed, 0)

    def jump(self):
        for target_shape in game_global.find_objects_with_tag("is_floor", True):
            if target_shape.rect.colliderect(self.rect):
                self.body.velocity += (0, -self.jump_strength)
                print('jump')
                break


if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption('Platformer alpha')
    size = width, height = 1200, 680  # 30x17 cells
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    window_size = pygame.display.get_surface().get_size()

    images = {}
    game_global = GameGlobal(
        init_path='data/images/',
        sprites_path=(('bricks.png', 'bricks', 5), ('dirt.png', 'dirt', 5), ('dark_stone.png', 'dark_stone', 5), ('hp_from_bar.png', 'hp', 5), ('sign.png', 'sign', 5), ('player.png', 'player', 5)),
        prefabs_path='data/prefabs.txt', keys_path='data/input_keys.txt',
        fps=60, gravity=(0, 800)
    )
    game_global.load_scene('data/scenes/test.txt', load_type='new', cell_size=40, path_symbols='data/prefabs_symbols.txt', path2='data/scenes/test_.txt')
    print(*[el for el in game_global.collider_objects_group])
    while game_global.program_running:
        screen.fill((0, 0, 0))
        game_global.update()
        game_global.render(screen)
        game_global.game_manager.space.step(1 / 60)
        # game_global.game_manager.space.debug_draw(game_global.game_manager.draw_options)
        pygame.display.flip()
        clock.tick(game_global.fps)
    pygame.quit()