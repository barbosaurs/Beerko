import pygame
import math
import pymunk
import pymunk.pygame_util
pymunk.pygame_util.positive_y_is_up = False

game_global = None


class GameRenderer:
    def __init__(self, game_objects):
        self.game_objects = game_objects

    def render(self, group, screen):
        [screen.blit(obj.image, (obj.pos[0] - game_global.cam_pos[0], obj.pos[1] - game_global.cam_pos[1])) for obj in group]

    def scene_start(self):
        pass


class GameManager:
    def __init__(self, keys_path):
        self.players = []
        self.buttons_pressed = set()
        self.move_input_axis = (0, 0)

        self.input_keys = {}
        self.load_keys(keys_path)

        self.space = pymunk.Space()
        self.space.gravity = 0, 8000

    def load_keys(self, keys_path):
        f = open(keys_path).readlines()
        for i in f:
            k, v = i.split(';')
            self.input_keys[int(k)] = v

    def add_players(self, players):
        self.players += players

    def add_move_input_axis(self, vector=(0, 0)):
        self.move_input_axis = (self.move_input_axis[0] + vector[0], self.move_input_axis[1] + vector[1])

    def update(self):
        self.move_input_axis = (0, 0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_global.program_running = False
            if event.type == pygame.MOUSEWHEEL:
                game_global.cam_pos = (game_global.cam_pos[0] + event.x, game_global.cam_pos[1] - event.y)
            # if event.type == pygame.KEYDOWN:
            #     print(event.key)
        keys = pygame.key.get_pressed()
        for k, v in self.input_keys.items():
            if keys[k]:
                eval(v)
        [player.set_move_input_axis(self.move_input_axis) for player in self.players]

    def scene_start(self):
        pass


class GameGlobal:
    def __init__(self, game_objects=(), init_path='', sprites_path=(), prefabs_path='', keys_path='', fps=60):
        self.program_running = True
        self.cam_pos = (0, 0)
        self.fps = fps

        self.all_objects_group = pygame.sprite.Group()
        self.physical_objects_group = pygame.sprite.Group()
        self.collider_objects_group = pygame.sprite.Group()

        self.game_objects = game_objects
        self.game_renderer = GameRenderer(self.game_objects)
        self.game_manager = GameManager(keys_path)
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
                for i in range(len(f)):
                    game_object = eval(f'{f2[0]}{f[i]}')
                    segment_shape = pymunk.Segment(self.game_manager.space.static_body, game_object.pos, game_object.size, 26)
                    self.game_manager.space.add(segment_shape)
                    segment_shape.elasticity = 0.4
                    segment_shape.friction = 1.0
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
    def __init__(self, prefab='', pos=(0, 0), scale=(1, 1), size=(40, 40), name='new_game_object', im='', color=(255, 255, 255), gravity=(0, 0), **tags):
        super().__init__(game_global.all_objects_group)
        self.physical_object = None

        self.pos, self.size, self.scale, self.name, self.im, self.color, self.gravity = [None] * 7
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
        if self.gravity is None:
            self.gravity = gravity

        for k, v in tags.items():
            if k not in self.tags.keys():
                self.tags[k] = v

        self.image = images[self.im]
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self.image = pygame.transform.scale(self.image, (self.get_transform()[2], self.get_transform()[3]))

        if 'has_collider' in self.tags and self.tags['has_collider']:
            self.add(game_global.collider_objects_group)


        if 'physical' in self.tags and self.tags['physical']:
            self.add(game_global.physical_objects_group)

            self.physical_speed = (0, 0)
            self.velocity = (0, 0)
            self.forces = {}
            self.forces['gravity'] = self.gravity
            self.collisions = set()

    def assign_physical(self, physical):
        self.physical_object = physical

    def start(self):
        pass

    def update(self):
        self.rect.x, self.rect.y = self.pos
        if 'physical' in self.tags and self.tags['physical']:
            self.physics_calculate()
            collided = pygame.sprite.spritecollideany(self, game_global.collider_objects_group)
            if collided and collided != self:
                print(collided)
    def physics_calculate(self):
        self.velocity = (sum([v[0] for v in self.forces.values()]) // 1, sum([v[1] for v in self.forces.values()]) // 1)
        # self.physical_speed = ((self.physical_speed[0] + self.velocity[0]) / 10, (self.physical_speed[1] + self.velocity[1]) / 10)
        self.translate((
            self.physical_speed[0] + self.velocity[0] / 2,
            self.physical_speed[1] + self.velocity[1] / 2
        ))
        self.pos = (self.pos[0] // 1, self.pos[1] // 1)

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
    def __init__(self, prefab='', pos=(0, 0), scale=(1, 1), size=(40, 40), name='new_game_object', im='', color=(255, 255, 255),  gravity=(0, 0), move_speed=1, **tags):
        super().__init__(prefab=prefab, pos=pos, scale=scale, size=size, name=name, im=im, color=color, gravity=gravity, **tags)
        self.move_input_axis = (0, 0)
        if self.move_speed is None:
            self.move_speed = move_speed

    def set_move_input_axis(self, vector=(0, 0)):
        self.move_input_axis = vector

    def update(self):
        super().update()
        self.forces['input_force'] = (self.move_input_axis[0] * self.move_speed, self.move_input_axis[1] * self.move_speed)


if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption('Alpha something...')
    size = width, height = 1200, 680  # 30x17 cells
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    window_size = pygame.display.get_surface().get_size()

    images = {}
    game_global = GameGlobal(
        init_path='data/images/',
        sprites_path=(('bricks.png', 'bricks', 5), ('dirt.png', 'dirt', 5), ('dark_stone.png', 'dark_stone', 5), ('hp_from_bar.png', 'hp', 5), ('sign.png', 'sign', 5)),
        prefabs_path='data/prefabs.txt', keys_path='data/input_keys.txt',
        fps=60,
    )
    game_global.load_scene('data/scenes/test.txt', load_type='new', cell_size=40, path_symbols='data/prefabs_symbols.txt', path2='data/scenes/test_.txt')

    while game_global.program_running:
        screen.fill((0, 0, 0))
        game_global.update()
        game_global.render(screen)
        pygame.display.flip()
        clock.tick(game_global.fps)
    pygame.quit()
