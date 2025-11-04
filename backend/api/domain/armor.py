from typing import Optional

def get_armor_texture_path(armor_type: str, piece: str, texture_pack: str = "vanilla") -> Optional[str]:
    """
    Get the path to an armor texture
    
    Args:
        armor_type (str): Type of armor (e.g. "fermento", "rancher")
        piece (str): Armor piece ("helmet", "chestplate", "leggings", "boots")
        texture_pack (str): Texture pack name ("vanilla", "furfsky", "flufsky")
        
    Returns:
        str: Path to the texture file
    """
    valid_pieces = ["helmet", "chestplate", "leggings", "boots"]
    if piece.lower() not in valid_pieces:
        return None
        
    return f"/static/icons/armor/{texture_pack}/{armor_type}_{piece.lower()}.png"