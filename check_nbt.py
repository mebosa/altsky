
try:
    from nbt import nbt
    print("NBT imported successfully")
except ImportError as e:
    print(f"Import failed: {e}")
