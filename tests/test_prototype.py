import pytest
import nominatim_api as napi
import asyncio
from src.transliterate import get_languages, latin, detect_language, result_transliterate, transliterate, _transliterate, decode_canto
from src.normalization import parse_languages

async def search(query):
    """ Nominatim Search Query
    """
    async with napi.NominatimAPIAsync() as api:
        return await api.search(query, address_details=True)


def test_transliterate():
    """ Base Transliteration Test

        Results should show that the result is perfectly transliterated to latin
    """
    variable = 'school in dandong'
    results = asyncio.run(search(f"{variable}"))
    output = result_transliterate(results)[0]
    assert output == "Dan Dong Shi Di Liu Zhong Xue, Qi Wei Lu, Zhan Qian Jie Dao, Dan Dong Shi, Zhen Xing Qu, 118000, Zhong Guo"


def test_transliterate_english():
    """ Base Transliteration Test to English

        Results should show that the result is transliterated to latin
        Except for components that have English locales already set
    """
    variable = 'school in dandong'
    results = asyncio.run(search(f"{variable}"))
    output = result_transliterate(results, ['en'])[0]
    assert output == "Dan Dong Shi Di Liu Zhong Xue, Qi Wei Lu, Zhanqian Subdistrict, Dandong, Zhenxing, 118000, China"


def test_transliterate_local():
    """ Base Transliteration Test where the user knows the local language

        Results should show that the result is in the orginal locale
    """
    variable = 'hospital in dandong'
    results = asyncio.run(search(f"{variable}"))
    output = result_transliterate(results, ['zh-Hans'])[0] # if we have zh enterring here it fails
    assert output == "丹东市中医院, 锦山大街, 站前街道, 元宝区, 振兴区, 118000, 中国"


def test_transliterate_ps():
    """ Base transliteration test where the user does not know the local language
        and only knows a non-latin language

        Results should show that the result is transliterated to latin (for now)
        but all aspects in the users non latin locale sould be not in latin

        ISSUE RIGHT NOW: langdetect detects ps (Afghanistan) as ur (Pakistan)
        FIXED: With locale key search
    """
    variable = 'hospital in dandong'
    results = asyncio.run(search(f"{variable}"))
    output = result_transliterate(results, ['ps'])[0]
    assert output == "Dan Dong Shi Zhong Yi Yuan, Jin Shan Da Jie, Zhan Qian Jie Dao, Yuan Bao Qu, Zhen Xing Qu, 118000, چين"


def test_transliterate_he():
    """ Base transliteration test where the user does not know the local language
        and only knows a non-latin language

        Results should show that the result is transliterated to latin (for now)
        but all aspects in the users non latin locale should be not in latin

        ISSUE RIGHT NOW: Hebrew is somehow flipped in the script
        FIXED: With locale key search
    """
    variable = 'hospital in dandong'
    results = asyncio.run(search(f"{variable}"))
    output = result_transliterate(results, ['he'])[0]
    assert output == "Dan Dong Shi Zhong Yi Yuan, Jin Shan Da Jie, Zhan Qian Jie Dao, Yuan Bao Qu, Zhen Xing Qu, 118000, סין"


def test_transliterate_km():
    """ Base transliteration test where the user does not know the local language
        and only knows a non-latin language

        Results should show that the result is transliterated to latin (for now)
        but all aspects in the users non latin locale should be not in latin

        ISSUE RIGHT NOW: langdetect does not detect Cambodian
        FIXED: With locale key search
    """
    variable = 'hospital in dandong'
    results = asyncio.run(search(f"{variable}"))
    output = result_transliterate(results, ['km'])[0]
    assert output == "Dan Dong Shi Zhong Yi Yuan, Jin Shan Da Jie, Zhan Qian Jie Dao, Yuan Bao Qu, Zhen Xing Qu, 118000, ចិន"


def test_transliterate_two():
    """ Base transliteration test where the user does not know the local language
        and only knows two latin languages (French and English)

        Results should show that the result is shown in French and English, with a preference for French
        All non-latin components should then be translated to Latin
    """
    variable = 'hospital in dandong'
    results = asyncio.run(search(f"{variable}"))
    output = result_transliterate(results, ['fr', 'en'])[0]
    assert output == "Dan Dong Shi Zhong Yi Yuan, Jinshan Main Street, Zhanqian Subdistrict, Yuanbao, Zhenxing, 118000, Chine"


def test_transliterate_region():
    """ Base transliteration test where the user does not know the local language
        and only knows two latin languages (French and English), but the browser gives 
        region specific language (en-US)

        Results should show that the result is shown in French and English, with a preference for French
        All non-latin components should then be translated to Latin
    """
    variable = 'hospital in dandong'
    test_header = "fr,en-GB;q=0.9,en-US;q=0.8,en;q=0.7"

    results = asyncio.run(search(f"{variable}"))
    output = result_transliterate(results, parse_languages(test_header))[0]
    assert output == "Dan Dong Shi Zhong Yi Yuan, Jinshan Main Street, Zhanqian Subdistrict, Yuanbao, Zhenxing, 118000, Chine"


def test_parsing_transliterate():
    """ Base HTML Header Parsing test + Transliteration
        to see if it can properly concatanate and 
        extract the proper naming conventions

        Checks if the prototype can differentiate between English Variants
    """
    test_header = "en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7"
    variable = 'school in dandong'
    results = asyncio.run(search(f"{variable}"))
    output = result_transliterate(results, parse_languages(test_header))[0]
    assert output == "Dan Dong Shi Di Liu Zhong Xue, Qi Wei Lu, Zhanqian Subdistrict, Dandong, Zhenxing, 118000, China"


def test_canto_transliterate():
    """ Cantonese transliteration to Latin test

        Tests to see if transliteration can accurately convert to 
        Cantonese
    """
    test_str = "梁國雄"
    output = decode_canto(test_str)
    assert output == "Leung Gwok Hung"