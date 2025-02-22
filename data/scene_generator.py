 # import sys

# scene_path = 'scenes/test.txt'
# f = open(scene_path, encoding='utf-8').read()
final = open('scenes/scene_generated.txt', mode='w', encoding='utf-8')
cell_size = 40
final_game_objects = []
class_types = []

work = True
while work:
    class_type = "GameObject"
    res0 = {}
    res0['pos'] = []
    while True:
        text = input().split()
        if text[0].lower().strip() == 'fill':  # fill 0 0 5 2 40
            size = cell_size if len(text) == 5 else int(text[5])
            for y in range((int(text[4]))):
                for x in range((int(text[3]))):
                    res0['pos'] += [((int(text[1]) + x) * size, (int(text[2]) + y) * size)]
        if text[0].lower().strip() == 'prefab':  # prefab bricks
            res0['prefab'] = ['"' + text[1] + '"' for i in range(len(res0['pos']))]
        if text[0].lower().strip() == 'class':  # class GameObject
            class_type = text[1]
        if text[0].lower().strip() == 'sprite':  # sprite bricks
            res0['sprite'] = ['"' + text[1] + '"' for i in range(len(res0['pos']))]
        if text[0].lower().strip() == 'name':  # name game_object
            res0['name'] = ['"' + text[1] + '"' for i in range(len(res0['pos']))]
        if text[0].lower().strip() == 'next':  # break this time
            break
        if text[0].lower().strip() == 'end':  # exit program
            work = False
            break
    game_objects = []
    for i in range(len(res0['pos'])):
        text = f'('
        text += ', '.join(list(map(lambda x: f'{x}={res0[x][i]}', res0.keys())))
        text += ')'
        game_objects += [text]
    final_game_objects += game_objects
    class_types += [class_type] * len(game_objects)
final_game_objects_by_classes = {}
game_objects_by_classes = []
last_class = None
for i in range(len(class_types)):
    if last_class is None:
        last_class = class_types[i]
    if last_class != class_types[i]:
        final_game_objects_by_classes[last_class] += game_objects_by_classes
        last_class = class_types[i]
        game_objects_by_classes = []
    if last_class == class_types[i]:
        game_objects_by_classes += [final_game_objects[i]]
    if last_class not in final_game_objects_by_classes.keys():
        final_game_objects_by_classes[last_class] = []
final_game_objects_by_classes[last_class] += game_objects_by_classes
for k, v in final_game_objects_by_classes.items():
    print(f"{k}:{';'.join(final_game_objects_by_classes[k])}", file=final)

# print(';'.join(final_game_objects), file=final)

EXAMPLE = """
fill 0 0 30 17
prefab dark_stone
next
fill 0 0 30 2
prefab bricks
fill 0 15 30 2
prefab bricks
next
fill 15 8 1 1
sprite hp
class Player
name player
end
""",
"""
fill 0 0 30 17
prefab dark_stone
next
fill 0 0 30 2
prefab bricks
fill 0 15 30 2
prefab bricks
next
fill 15 8 1 1
sprite hp
class Player
name player
end
"""