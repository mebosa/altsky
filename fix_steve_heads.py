"""
SkyCrypt API를 사용하여 펫 텍스처를 다시 다운로드
"""
import requests
import os
from pathlib import Path
import time

# 스티브 머리로 표시되는 펫들
STEVE_HEAD_PETS = {
    'baby_yeti': 'ab126814fc3fa846dad934c349628a7a1de5b415021a03ef4211d62514d5',
    'elephant': '7071a76f669db5ed6d32b48bb2dba55d5317d7f45225cb3267ec435cfa514',
    'endermite': '5a1a0831aa03afb4212adcbb24e5dfaa7f476a1173fce259ef75a85855',
    'flying_fish': '40cd71fbbbbb66c7baf7881f415c64fa84f6504958a57ccdb8589252647ea',
    'frog': '5454ad786b1cd4a1c2c3469023c1e38d2c5a8e3c3cc06d3f8dae8c8f5e3dcb87',
    'giraffe': '176b4e390f2ecdb8a78dc611789ca0af1e7e09229319c3a7aa8209b63b9',
    'golem': '89091d79ea0f59ef7ef94d7bba6e5f17f2f7d4572c44f90f76c4819a714',
    'horse': '36fcd3ec3bc84bafb4123ea479471f9d2f42d8fb9c5f11cf5f4e0d93226',
    'jerry': '822d8e751c8f2fd4c8942c44bdb2f5ca4d8ae8e575ed3eb34c18a86e93b',
    'magma_cube': '38957d5023c937c4c41aa2412d43410bda23cf79a9f6ab36b76fef2d7c429',
    'monkey': '13cf8db84807c471d7c6922302261ac1b5a179f96d1191156ecf3e1b1d3ca',
    'ocelot': '5657cd5c2989ff97570fec4ddcdc6926a68a3393250c1be1f0b114a1db1',
    'pig': '621668ef7cb79dd9c22ce3d1f3f4cb6e2559893b6df4a469514e667c16aa4',
    'rabbit': '117bffc1972acd7f3b4a8f43b5b6c7534695b8fd62677e0306b2831574b',
    'sheep': '64e22a46047d272e89a1cfa13e9734b7e12827e235c2012c1a95962874da0',
    'skeleton_horse': '47effce35132c86ff72bcae77dfbb1d22587e94df3cbc2570ed17cf8973a',
}

def fix_steve_heads():
    """SkyCrypt API를 사용하여 스티브 머리 이미지를 수정"""
    pets_dir = Path('frontend/static/pets')
    
    print(f"펫 이미지 디렉토리: {pets_dir.absolute()}")
    print(f"수정할 펫: {len(STEVE_HEAD_PETS)}개\n")
    
    success = 0
    failed = []
    
    for pet_name, texture_hash in STEVE_HEAD_PETS.items():
        output_file = pets_dir / f"{pet_name}.png"
        
        # 현재 파일 크기 확인 (스티브 머리 = 10751 bytes)
        if output_file.exists():
            current_size = output_file.stat().st_size
            if current_size != 10751:
                print(f"✓ {pet_name}: 이미 올바른 이미지 ({current_size} bytes)")
                success += 1
                continue
        
        url = f"https://sky.shiiyu.moe/api/head/{texture_hash}"
        print(f"→ {pet_name}: 다운로드 중...")
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # PNG 파일인지 확인
            if response.content[:4] == b'\x89PNG':
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"  ✓ 성공 ({len(response.content)} bytes)")
                success += 1
            else:
                print(f"  ✗ PNG 아님")
                failed.append(pet_name)
        except Exception as e:
            print(f"  ✗ 실패: {str(e)}")
            failed.append(pet_name)
        
        time.sleep(0.3)  # Rate limiting
    
    print(f"\n{'='*60}")
    print(f"수정 완료!")
    print(f"성공: {success}/{len(STEVE_HEAD_PETS)}")
    if failed:
        print(f"실패: {len(failed)}개 - {', '.join(failed)}")
    print(f"{'='*60}")

if __name__ == '__main__':
    fix_steve_heads()
