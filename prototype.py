# Proof of concept of transliteration using Nominatim as a library
# from nominatim_api.v1.format import dispatch as dispatch
import unicodedata
import nominatim_api as napi
from unidecode import unidecode
import asyncio
import yaml
from typing import Optional, Tuple, Dict, Sequence, TypeVar, Type, List, cast, Callable
from langdetect import detect, LangDetectException # for now, until can figure out why names default no langauge

async def search(query):
    async with napi.NominatimAPIAsync() as api:
        return await api.search(query, address_details=True)
        # return await api.search(query)

def load_languages(yaml_path='country_settings.yaml') -> dict:
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)

    return {code.lower(): settings.get('languages', '').split(',') 
            for code, settings in data.items()}

def get_languages(result, lang_map):
    code = result.country_code.lower()
    return lang_map.get(code, [])  # defaults to empty list

def prototype(results):
    if not results:
        print(f'No results found')
    else:
        print(f'Found a place at {results[0].centroid.x},{results[0].centroid.y}')

        print('\nOriginal Result: ')
        locale = napi.Locales([]) 
        for i, result in enumerate(results):
            address_parts = result.address_rows.localize(locale)
            print(f"{i + 1}. {', '.join(address_parts)}")

        print('\nDirect Localization to Chinese')
        locale = napi.Locales(['zh']) 
        for i, result in enumerate(results):
            address_parts = result.address_rows.localize(locale)
            print(f"{i + 1}. {', '.join(address_parts)}")

        locale = napi.Locales(['en']) 
        print('\nDirect Localization to English:')
        for i, result in enumerate(results):
            address_parts = result.address_rows.localize(locale)
            print(f"{i + 1}. {', '.join(address_parts)}")

        locale = napi.Locales(['fr']) 
        print('\nDirect Localization to French:')
        for i, result in enumerate(results):
            address_parts = result.address_rows.localize(locale)
            print(f"{i + 1}. {', '.join(address_parts)}")

        print('\nTranliterated Result: ')
        locale = napi.Locales(['chinese']) 
        for i, result in enumerate(results):
            address_parts = result.address_rows.localize(locale)
            print(f"{i + 1}. {', '.join(unidecode(part) for part in address_parts)}")

        print('\n Combination Result English: ')
        locale = napi.Locales(['en']) 
        for i, result in enumerate(results):
            address_parts = result.address_rows.localize(locale)
            print(f"{i + 1}. {', '.join(unidecode(part) for part in address_parts)}")

        print('\n Combination Result French: ')
        locale = napi.Locales(['fr']) 
        for i, result in enumerate(results):
            address_parts = result.address_rows.localize(locale)
            print(f"{i + 1}. {', '.join(unidecode(part) for part in address_parts)}")

def latin(text): # returns if it is latin based or not
    for char in text:
        if char.isalpha():
            name = unicodedata.name(char, "")
            if 'LATIN' not in name:
                return False
    return True

def get_locales(results):
    locale_set = set()
    for result in results:
        if result.names:
            locale_set.update(result.names.keys())
        if result.address_rows:
            for row in result.address_rows:
                if row.names:
                    locale_set.update(row.names.keys())
    return sorted(locale_set)

def result_transliterate(results, user_languages):
    for i, result in enumerate(results):
        address_parts = transliterate_iso(result, user_languages)
        print(f"{i + 1}. {', '.join(part for part in address_parts)}")

def _transliterate(text, locales: napi.Locales): #  only latin transliteration for now
    return unidecode(text)

def transliterate_langdetect(result, user_languages: List) -> List[str]:
    """ Based on Nominatim Localize and Detect Languages
        Assumes the user does not know the local language
    
        Set the local name of address parts according to the chosen
        local, transliterating if not avaliable. 
        Return the list of local names without duplicates.

        Only address parts that are marked as isaddress are localized
        and returned.
    """
    locales = napi.Locales(user_languages) 
    label_parts: List[str] = []

    if not result.address_rows:
        return label_parts
    
    for line in result.address_rows:
        if line.isaddress and line.names:
            line.local_name = locales.display_name(line.names)

            language = detect_language_langdetect(line)
            print(language)
            if not label_parts or label_parts[-1] != line.local_name:
                if language in user_languages:
                    label_parts.append(line.local_name)
                else:
                    label_parts.append(_transliterate(line.local_name, locales))

    return label_parts

def detect_language_langdetect(line):
    try:
        return detect(line.local_name) if len(line.local_name.strip()) >= 3 else None
    except LangDetectException:
        return None

def transliterate_iso(result, user_languages: List) -> List[str]:
    """ Based on Nominatim Localize and ISO regions
        Assumes the user does not know the local language
    
        Set the local name of address parts according to the chosen
        local, transliterating if not avaliable. 
        Return the list of local names without duplicates.

        Only address parts that are marked as isaddress are localized
        and returned.
    """
    locales = napi.Locales(user_languages) 
    lang_map = load_languages()
    label_parts: List[str] = []
    iso = False

    if not result.address_rows:
        return label_parts

    if bool(set(get_languages(result, lang_map)) & set(user_languages)):
        iso = True

    for line in result.address_rows:
        if line.isaddress and line.names:

            if not iso:
                line.local_name = locales.display_name(line.names)

            language = detect_language_langdetect(line)
            print(language)
            
            if not label_parts or label_parts[-1] != line.local_name:
                if iso or language in user_languages:
                    label_parts.append(line.local_name)
                else:
                    label_parts.append(_transliterate(line.local_name, locales))

    return label_parts

variable = 'hospital in dandong'
results = asyncio.run(search(f"{variable}"))

# print(get_locales(results))
# also need to have zh, chinese, cn, zh_hs, zh-cn be together?
result_transliterate(results,  ['zh', 'fr'] )
# prototype(results)