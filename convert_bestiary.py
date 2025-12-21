import json
import re

def parse_js_object(js_content):
    # This is a very rough parser, assuming the file structure is consistent
    # It extracts the BESTIARY object and BESTIARY_BRACKETS object
    
    # Extract BESTIARY object content
    bestiary_match = re.search(r'export const BESTIARY = ({[\s\S]*?});\s*export const BESTIARY_BRACKETS', js_content)
    if not bestiary_match:
        print("Could not find BESTIARY object")
        return None, None
        
    bestiary_str = bestiary_match.group(1)
    
    # Extract BESTIARY_BRACKETS object content
    brackets_match = re.search(r'export const BESTIARY_BRACKETS = ({[\s\S]*?});', js_content)
    if not brackets_match:
        print("Could not find BESTIARY_BRACKETS object")
        return None, None
        
    brackets_str = brackets_match.group(1)
    
    return bestiary_str, brackets_str

def convert_to_python(js_str):
    # Replace JS syntax with Python syntax
    # Remove comments
    py_str = re.sub(r'//.*', '', js_str)
    
    # Quote keys
    py_str = re.sub(r'(\w+):', r'"\1":', py_str)
    
    # Fix specific issues
    # "https"://... -> "https://..." (if any) - actually keys are simple words usually
    
    # Remove trailing commas before closing braces/brackets (Python handles them but JSON doesn't, 
    # but we are generating Python code so it's fine)
    
    return py_str

def main():
    with open('tmp/skycrypt/src/constants/bestiary.js', 'r', encoding='utf-8') as f:
        content = f.read()
        
    bestiary_str, brackets_str = parse_js_object(content)
    
    if not bestiary_str or not brackets_str:
        return

    # Manual cleanup for Python syntax
    # JS: keys don't need quotes, Python: keys need quotes
    # We can use a regex to quote keys, but we need to be careful about values that contain colons (urls)
    
    # Let's try a different approach:
    # We will generate the python file by reading the JS file line by line and transforming it.
    
    py_lines = []
    py_lines.append("BESTIARY = {")
    
    # Process BESTIARY
    # It's a nested object.
    # Let's just use the regex replacement for keys, it should be mostly fine for this specific file structure
    
    bestiary_py = bestiary_str
    # Quote keys at the start of the line or after { or ,
    # Pattern: (start or space or { or ,) key :
    bestiary_py = re.sub(r'(\s+|{|,)(\w+):', r'\1"\2":', bestiary_py)
    
    brackets_py = brackets_str
    brackets_py = re.sub(r'(\s+|{|,)(\w+):', r'\1"\2":', brackets_py)
    
    with open('backend/api/domain/bestiary_constants.py', 'w', encoding='utf-8') as f:
        f.write("BESTIARY = " + bestiary_py + "\n\n")
        f.write("BESTIARY_BRACKETS = " + brackets_py + "\n")
        
    print("Conversion complete.")

if __name__ == "__main__":
    main()
