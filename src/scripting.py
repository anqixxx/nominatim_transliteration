from transliterate import get_languages, latin, detect_language, result_transliterate, transliterate, _transliterate, decode_canto
from normalization import normalize_lang, parse_lang
import nominatim_api as napi
import asyncio

data = None  

async def search(query):
    """ Nominatim Search Query
    """
    async with napi.NominatimAPIAsync() as api:
        return await api.search(query, address_details=True)
        # return await api.search(query)

variable = 'hospital in dandong'
# variable = 'school in dandong'
results = asyncio.run(search(f"{variable}"))
result_transliterate(results, ['en'])
o = result_transliterate(results, ['fr', 'en'])
print(o)

test_header = "zh-hans, zh;q=0.9, en;q=0.8"
user_languages = parse_lang(test_header)
results = asyncio.run(search(variable))
print("User preferred languages:", user_languages)
print("User preferred languages changed:", [normalize_lang(lang) for lang in user_languages])
print(result_transliterate(results, user_languages))

marc_header = "en-US,en;q=0.5"
user_languages = parse_lang(marc_header)
results = asyncio.run(search(variable))
print("User preferred languages:", user_languages)
print("User preferred languages changed:", [normalize_lang(lang) for lang in user_languages])
print(type(user_languages))
print(result_transliterate(results, user_languages))

anqi_header = "en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7"
user_languages = parse_lang(anqi_header)
results = asyncio.run(search(variable))
print("User preferred languages:", user_languages)
print("User preferred languages changed:", [normalize_lang(lang) for lang in user_languages])
print(type(user_languages))
print(result_transliterate(results, user_languages))

print(decode_canto('梁國雄'))