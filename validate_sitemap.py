import xml.etree.ElementTree as ET

try:
    tree = ET.parse('frontend/static/sitemap.xml')
    root = tree.getroot()
    print("XML is valid")
    print(f"Root tag: {root.tag}")
    for child in root:
        print(f"Child: {child.tag}")
except Exception as e:
    print(f"XML error: {e}")
