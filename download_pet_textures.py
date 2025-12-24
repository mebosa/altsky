"""
펫 텍스처를 mc-heads.net에서 다운로드하여 로컬에 저장하는 스크립트
"""
import requests
import os
from pathlib import Path
import time

# PetsTab.svelte의 petTextures와 동일한 데이터
PET_TEXTURES = {
    'ARMADILLO': 'c1eb6df4736ae24dd12a3d00f91e6e3aa7ade6bbefb0978afef2f0f92461018f',
    'BAT': '382fc3f71b41769376a9e92fe3adbaac3772b999b219c9d6b4680ba9983e527',
    'BLAZE': 'b78ef2e4cf2c41a2d14bfde9caff10219f5b1bf5b35a49eb51c6467882cb5f0',
    'CHICKEN': '7f37d524c3eed171ce149887ea1dee4ed399904727d521865688ece3bac75e',
    'HORSE': '36fcd3ec3bc84bafb4123ea479471f9d2f42d8fb9c5f11cf5f4e0d93226',
    'JERRY': '822d8e751c8f2fd4c8942c44bdb2f5ca4d8ae8e575ed3eb34c18a86e93b',
    'OCELOT': '5657cd5c2989ff97570fec4ddcdc6926a68a3393250c1be1f0b114a1db1',
    'PIGMAN': '63d9cb6513f2072e5d4e426d70a5557bc398554c880d4e7b7ec8ef4945eb02f2',
    'RABBIT': '117bffc1972acd7f3b4a8f43b5b6c7534695b8fd62677e0306b2831574b',
    'FROG': '5454ad786b1cd4a1c2c3469023c1e38d2c5a8e3c3cc06d3f8dae8c8f5e3dcb87',
    'SHEEP': '64e22a46047d272e89a1cfa13e9734b7e12827e235c2012c1a95962874da0',
    'SILVERFISH': 'da91dab8391af5fda54acd2c0b18fbd819b865e1a8f1d623813fa761e924540',
    'WITHER_SKELETON': 'f5ec964645a8efac76be2f160d7c9956362f32b6517390c59c3085034f050cff',
    'SKELETON_HORSE': '47effce35132c86ff72bcae77dfbb1d22587e94df3cbc2570ed17cf8973a',
    'WOLF': 'dc3dd984bb659849bd52994046964c22725f717e986b12d548fd169367d494',
    'ENDERMAN': '6eab75eaa5c9f2c43a0d23cfdce35f4df632e9815001850377385f7b2f039ce1',
    'PHOENIX': '23aaf7b1a778949696cb99d4f04ad1aa518ceee256c72e5ed65bfa5c2d88d9e',
    'MAGMA_CUBE': '38957d5023c937c4c41aa2412d43410bda23cf79a9f6ab36b76fef2d7c429',
    'FLYING_FISH': '40cd71fbbbbb66c7baf7881f415c64fa84f6504958a57ccdb8589252647ea',
    'FLYING_FISH_MYTHIC': 'b0e2363c2d41a9d323ba625de8c0637063a36fe85a045de275a7b7739ded6051',
    'BLUE_WHALE': 'dab779bbccc849f88273d844e8ca2f3a67a1699cb216c0a11b44326ce2cc20',
    'TIGER': 'fc42638744922b5fcf62cd9bf27eeab91b2e72d6c70e86cc5aa3883993e9d84',
    'LION': '38ff473bd52b4db2c06f1ac87fe1367bce7574fac330ffac7956229f82efba1',
    'PARROT': '5df4b3401a4d06ad66ac8b5c4d189618ae617f9c143071c8ac39a563cf4e4208',
    'SNOWMAN': '11136616d8c4a87a54ce78a97b551610c2b2c8f6d410bc38b858f974b113b208',
    'TURTLE': '212b58c841b394863dbcc54de1c2ad2648af8f03e648988c1f9cef0bc20ee23c',
    'BEE': '7e941987e825a24ea7baafab9819344b6c247c75c54a691987cd296bc163c263',
    'ENDER_DRAGON': 'aec3ff563290b13ff3bcc36898af7eaa988b6cc18dc254147f58374afe9b21b9',
    'GUARDIAN': '221025434045bda7025b3e514b316a4b770c6faa4ba9adb4be3809526db77f9d',
    'SQUID': '01433be242366af126da434b8735df1eb5b3cb2cede39145974e9c483607bac',
    'GIRAFFE': '176b4e390f2ecdb8a78dc611789ca0af1e7e09229319c3a7aa8209b63b9',
    'ELEPHANT': '7071a76f669db5ed6d32b48bb2dba55d5317d7f45225cb3267ec435cfa514',
    'MONKEY': '13cf8db84807c471d7c6922302261ac1b5a179f96d1191156ecf3e1b1d3ca',
    'SPIDER': 'cd541541daaff50896cd258bdbdd4cf80c3ba816735726078bfe393927e57f1',
    'ENDERMITE': '5a1a0831aa03afb4212adcbb24e5dfaa7f476a1173fce259ef75a85855',
    'GHOUL': '87934565bf522f6f4726cdfe127137be11d37c310db34d8c70253392b5ff5b',
    'JELLYFISH': '913f086ccb56323f238ba3489ff2a1a34c0fdceeafc483acff0e5488cfd6c2f1',
    'PIG': '621668ef7cb79dd9c22ce3d1f3f4cb6e2559893b6df4a469514e667c16aa4',
    'ROCK': 'cb2b5d48e57577563aca31735519cb622219bc058b1f34648b67b8e71bc0fa',
    'SKELETON': 'fca445749251bdd898fb83f667844e38a1dff79a1529f79a42447a0599310ea4',
    'ZOMBIE': '56fc854bb84cf4b7697297973e02b79bc10698460b51a639c60e5e417734e11',
    'DOLPHIN': 'cefe7d803a45aa2af1993df2544a28df849a762663719bfefc58bf389ab7f5',
    'BABY_YETI': 'ab126814fc3fa846dad934c349628a7a1de5b415021a03ef4211d62514d5',
    'MEGALODON': 'a94ae433b301c7fb7c68cba625b0bd36b0b14190f20e34a7c8ee0d9de06d53b9',
    'GOLEM': '89091d79ea0f59ef7ef94d7bba6e5f17f2f7d4572c44f90f76c4819a714',
    'HOUND': 'b7c8bef6beb77e29af8627ecdc38d86aa2fea7ccd163dc73c00f9f258f9a1457',
    'TARANTULA': '8300986ed0a04ea79904f6ae53f49ed3a0ff5b1df62bba622ecbd3777f156df8',
    'BLACK_CAT': 'e4b45cbaa19fe3d68c856cd3846c03b5f59de81a480eec921ab4fa3cd81317',
    'SPIRIT': '8d9ccc670677d0cebaad4058d6aaf9acfab09abea5d86379a059902f2fe22655',
    'GRIFFIN': '4c27e3cb52a64968e60c861ef1ab84e0a0cb5f07be103ac78da67761731f00c8',
    'MITHRIL_GOLEM': 'c1b2dfe8ed5dffc5b1687bc1c249c39de2d8a6c3d90305c95f6d1a1a330a0b1',
    'GRANDMA_WOLF': '4e794274c1bb197ad306540286a7aa952974f5661bccf2b725424f6ed79c7884',
    'RAT': 'a8abb471db0ab78703011979dc8b40798a941f3a4dec3ec61cbeec2af8cffe8',
    'BAL': 'c469ba2047122e0a2de3c7437ad3dd5d31f1ac2d27abde9f8841e1d92a8c5b75',
    'SCATHA': 'df03ad96092f3f789902436709cdf69de6b727c121b3c2daef9ffa1ccaed186c',
    'GOLDEN_DRAGON': '2e9f9b1fc014166cb46a093e5349b2bf6edd201b680d62e48dbf3af9b0459116',
    'AMMONITE': 'a074a7bd976fe6aba1624161793be547d54c835cf422243a851ba09d1e650553',
    'BINGO': 'd4cd9c707c7092d4759fe2b2b6a713215b6e39919ec4e7afb1ae2b6f8576674c',
    'MOOSHROOM_COW': '2b52841f2fd589e0bc84cbabf9e1c27cb70cac98f8d6b3dd065e55a4dcb70d77',
    'SNAIL': '50a9933a3b10489d38f6950c4e628bfcf9f7a27f8d84666f04f14d5374252972',
    'KUUDRA': '1f0239fb498e5907ede12ab32629ee95f0064574a9ffdff9fc3a1c8e2ec17587',
    'DROPLET_WISP': 'b412e70375ec99ee38ae94b30e9b10752d459662b54794dfe66fe6a183c672d3',
    'FROST_WISP': '1d8ad9936d758c5ea30b0b7cc7c67c2bfcea829ecf2425c0b50fc92a26ae23d0',
    'GLACIAL_WISP': '3e2018feebe1a99177b3cb196d4e44521268b4b3eb56e6419cb0253cdbf0456c',
    'SUBZERO_WISP': '7a0eb37e58c942eca4d33ab44e26eb1910c783788510b0a53b6f4d18881e237e',
    'REINDEER': 'a2df65c6fd19a58bee38252192ac7ce2cf1dc8632c3547a9228b6b697240d098',
    'RIFT_FERRET': 'b6b11399448260185da1d17e54c984515faab6d8585f00972451ec2b43d46f94',
    'EERIE': 'c3af70c6ff76ba48f24ee8a2063a5b50bbfabf409f4795248a292f8289f47c98',
    'SLUG': '7a79d0fd677b54530961117ef84adc206e2cc5045c1344d61d776bf8ac2fe1ba',
    'OWL': 'da3216da54e7368fb40b721239ad95e07ef4f97d93f1c42ff319bab9a53882af',
    'TYRANNOSAURUS': '93f28ec96df59c67e9d2fc2e7e3d055fa31646e4111add9fe26a692801964126',
    'SPINOSAURUS': 'd3c9d479471a2f13f22548315159591720992e70c920fef83a901b7186720e3c',
    'GOBLIN': '7309d8dc35a638a04b915a3b15a1452ceeae0d7ea42bcdadb21b03046987515c',
    'ANKYLOSAURUS': 'c1aa836b9096c417903299a6c5ab41738c19648ac439fed4bcbe6c32605338dc',
    'PENGUIN': '37534e97f36e5a8335928e171ec99608bee7fb16e260afb301025b3b17eeefc4',
    'MAMMOTH': '6b10715732cd1fd49fa1b6187947c307dd4687105cf033840607f9d6234743ad',
    'MOLE': '727baaafc09978d4bda73e16afdde85ec13b0f95ad989524c5fcaa717cf06b4a',
    'GLACITE_GOLEM': 'af132a6593876d3c377d503fd66eca3fb938743251f7b16a9870c60b7388c8a3',
}

def download_pet_textures():
    """모든 펫 텍스처를 다운로드"""
    output_dir = Path('backend/staticfiles/pets')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"다운로드 디렉토리: {output_dir.absolute()}")
    print(f"총 {len(PET_TEXTURES)}개 펫 텍스처 다운로드 시작...\n")
    
    success = 0
    failed = []
    
    for pet_name, texture_hash in PET_TEXTURES.items():
        output_file = output_dir / f"{pet_name.lower()}.png"
        
        # 이미 존재하면 스킵
        if output_file.exists():
            print(f"✓ {pet_name}: 이미 존재 (스킵)")
            success += 1
            continue
        
        url = f"https://mc-heads.net/head/{texture_hash}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # PNG 파일인지 확인
            if response.content[:4] == b'\x89PNG':
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"✓ {pet_name}: 다운로드 성공 ({len(response.content)} bytes)")
                success += 1
            else:
                print(f"✗ {pet_name}: PNG 파일이 아님")
                failed.append(pet_name)
        
        except Exception as e:
            print(f"✗ {pet_name}: 다운로드 실패 - {str(e)}")
            failed.append(pet_name)
        
        # Rate limiting 방지
        time.sleep(0.1)
    
    print(f"\n{'='*60}")
    print(f"다운로드 완료!")
    print(f"성공: {success}/{len(PET_TEXTURES)}")
    if failed:
        print(f"실패: {len(failed)}개 - {', '.join(failed)}")
    print(f"{'='*60}")

if __name__ == '__main__':
    download_pet_textures()
