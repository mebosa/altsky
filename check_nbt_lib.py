
import base64
import io
import sys

try:
    import nbtlib
    print("nbtlib is available")
except ImportError:
    print("nbtlib is NOT available")

try:
    from nbt import nbt
    print("nbt is available")
except ImportError:
    print("nbt is NOT available")
