import json
import os

files_to_check = [
    r'c:\altskydev\altsky\backend\statscalc\data\stats\armor.json',
    r'c:\altskydev\altsky\backend\statscalc\data\stats\armor_expanded.json',
    r'c:\altskydev\altsky\furfsky_tree.json'
]

items_to_find = [
    'REVENANT_HELMET', 'REVENANT_CHESTPLATE', 'REVENANT_LEGGINGS', 'REVENANT_BOOTS',
    'REAPER_HELMET', 'REAPER_CHESTPLATE', 'REAPER_LEGGINGS', 'REAPER_BOOTS', 'REAPER_MASK',
    'FINAL_DESTINATION_HELMET', 'FINAL_DESTINATION_CHESTPLATE', 'FINAL_DESTINATION_LEGGINGS', 'FINAL_DESTINATION_BOOTS',
    'BAT_PERSON_HELMET', 'BAT_PERSON_CHESTPLATE', 'BAT_PERSON_LEGGINGS', 'BAT_PERSON_BOOTS',
    'WEREWOLF_HELMET', 'WEREWOLF_CHESTPLATE', 'WEREWOLF_LEGGINGS', 'WEREWOLF_BOOTS',
    'HYPERION',
    'TERMINATOR',
    'JUJU_SHORTBOW',
    'GIANTS_SWORD',
    'DARK_CLAYMORE',
    'LIVID_DAGGER',
    'SHADOW_FURY',
    'ASPECT_OF_THE_END',
    'ASPECT_OF_THE_VOID'
]

found_data = {}

for file_path in files_to_check:
    if not os.path.exists(file_path):
        print(f'File not found: {file_path}')
        continue
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f'Scanning {file_path}...')
            
            if 'armor_stats' in data:
                for item_id, stats in data['armor_stats'].items():
                    if item_id in items_to_find:
                        found_data[item_id] = stats
            
            if 'armor_sets' in data:
                 for set_id, bonus in data['armor_sets'].items():
                     found_data[f'SET_{set_id}'] = bonus

            def traverse_furfsky(node):
                if isinstance(node, dict):
                    if 'matcher' in node and 'value' in node['matcher']:
                        item_id = node['matcher']['value']
                        if item_id in items_to_find:
                            found_data[f'FURFSKY_{item_id}'] = node
                    
                    for key, value in node.items():
                        traverse_furfsky(value)
                elif isinstance(node, list):
                    for item in node:
                        traverse_furfsky(item)

            if 'furfsky' in file_path:
                traverse_furfsky(data)

    except Exception as e:
        print(f'Error reading {file_path}: {e}')

print(json.dumps(found_data, indent=2))
