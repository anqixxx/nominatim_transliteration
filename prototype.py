# Proof of concept of transliteration using Nominatim as a library
# from nominatim_api.v1.format import dispatch as dispatch
import unicodedata
import nominatim_api as napi
from unidecode import unidecode
import asyncio
import opencc
import yaml
from typing import Optional, Tuple, Dict, Sequence, TypeVar, Type, List, cast, Callable
from langdetect import detect, LangDetectException # for now, until can figure out why names default no langauge
from nominatim_api.typing import Protocol
from nominatim_api.config import Configuration
from nominatim_db.db.connection import Connection

class Transliterator():
    """
        Class handling the process of transliteration from search results.
    """
    def __init__(self, config: Configuration, conn: Connection) -> None:
        self.config = config
        self.db_connection = conn
        self.data = None
    
data = None  

async def search(query):
    """ Nominatim Search Query
    """
    async with napi.NominatimAPIAsync() as api:
        return await api.search(query, address_details=True)
        # return await api.search(query)


def normalize_lang(lang):
    """ Mock idea for language mapping dictionary

        Hoping to standardize certain names, i.e.
        zh and zh-cn will always map to zh-hans
        zh-tw will always map to zh-hant

        For all other languages, follow Nominatim precedent
        and just concatenate after the '-'

        Code assumes all language codes are in two letter format
        https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes 
    """
    # Potentially make this a global variable (or object field) to reduce compute
    lang_dict = {
        "zh": "zh-Hans",
        "zh-cn": "zh-Hans",
        "zh-tw": "zh-Hant",
        "zh-hans": "zh-Hans",
        "zh-hant": "zh-Hant",
    }
    if lang in lang_dict:
    #  Ordering nessecary due to zh edge case (no '-')
        return lang_dict[lang]
    elif '-' not in lang:
        return lang
    return lang.split('-')[0] 


def load_languages(yaml_path='country_settings.yaml'):
    """ Loads country_settings
        Yaml files from Nominatim blob/master/settings/country_settings.yaml 
    """
    with open(yaml_path, 'r') as file:
        return yaml.safe_load(file)


def get_languages(result):
    """ Given a result, returns the languages associated with the region

        Special handling is needed for Macau and Hong Kong (not in yaml)
    """
    global data

    if not data:
        data = load_languages()

    country = data.get(result.country_code.lower())
    if country and 'languages' in country:
        return [lang.strip() for lang in country['languages'].split(',')]
    return []


def prototype(results):
    """ Initial transliteration prototype
        Proof of concept
    """
    if not results:
        print('No results found')
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


def latin(text):
    """ Given a text string, eturns if
        the string is Latin based or not
    """
    for char in text:
        if char.isalpha():
            name = unicodedata.name(char, "")
            if 'LATIN' not in name:
                return False
    return True


def get_locales(results):
    """ Given a list of results, prints out all locales
        associated with the results
    """
    locale_set = set()
    for result in results:
        if result.names:
            locale_set.update(result.names.keys())
        if result.address_rows:
            for row in result.address_rows:
                if row.names:
                    locale_set.update(row.names.keys())
    return sorted(locale_set)


def result_locales(address_part, languages: List[str]):
    """ Given a result address part component, return if True the user knows any
        of the locales associated with the results and False if transliteration
        is needed
    """
    if languages:
        for language in languages:
            target = f"name:{language}" 
            if target in address_part.names.keys():
                return True
        
            target = f"alt_name:{language}" 
            if target in address_part.names.keys(): 
                return True
    return False


def result_transliterate(results, user_languages: List[str] = []) -> List[str]:
    """ High level transliteration result wrapper

        Prints out the transliterated results
        Returns output as list
    """
    output = []
    user_languages = [normalize_lang(lang) for lang in user_languages]

    for i, result in enumerate(results):
        address_parts = transliterate(result, user_languages)
        print(f"{i + 1}. {', '.join(part.strip() for part in address_parts)}")
        output.append(", ".join(part.strip() for part in address_parts))
    return output


def _transliterate(line: napi.AddressLine, locales: List[str]):
    """ Most granular transliteration component
        Performs raw transliteration based on locales

        Defaults to Latin
    """
    for locale in locales:
        # Need to replace to be a valid function
        _function = f"{locale.replace("-", "_")}_transliterate"
        if _function in globals():
            print(f"{locale} transliteration successful")
            return globals()[_function](line)
    
    print("defaulting to latin based transliteration")
    return unidecode(line.local_name)


def zh_Hans_transliterate(line: napi.AddressLine):
    """ If in Traditional Chinese, convert to Simplified
        NOT TESTED, PROOF OF CONCEPT

        Else switch to standard Latin default transliteration
    """
    if result_locales(line, ['zh-hant']):
        converter = opencc.OpenCC('t2s.json') # t2s.json Traditional Chinese to Simplified Chinese 繁體到簡體
        return converter.convert(line.local_name)
    return unidecode(line.local_name)


def zh_Hant_transliterate(line: napi.AddressLine):
    """ If in Simplified Chinese, convert to Traditional

        Else switch to standard Latin default transliteration
    """
    if result_locales(line, ['zh-hans']) or result_locales(line, ['zh']): # also need a way to know it its in chinese or not
        converter = opencc.OpenCC('s2t.json') # t2s.json Traditional Chinese to Simplified Chinese 繁體到簡體
        return converter.convert(line.local_name)
    return unidecode(line.local_name)


def detect_language(text):
    """ Given a string of characters, uses the langdetect library
        to determine the language
    """
    try:
        return detect(text) if len(text.strip()) >= 3 else None
    except LangDetectException:
        return None


def transliterate(result, user_languages: List) -> List[str]:
    """ Based on Nominatim Localize and ISO regions
        Assumes the user does not know the local language

        Set the local name of address parts according to the chosen
        local, transliterating if not avaliable.
        Return the list of local names without duplicates.

        Only address parts that are marked as isaddress are localized
        and returned.
    """
    label_parts: List[str] = []
    iso = False

    if not result.address_rows:
        return label_parts

    local_languages = get_languages(result)
    print(local_languages)
    print(user_languages)
    if len(local_languages) == 1 and local_languages[0] in user_languages:
        iso = True

    for line in result.address_rows:
        if line.isaddress and line.names:

            if not iso:
                line.local_name = napi.Locales(user_languages).display_name(line.names)
                # print(line.names) # For test cases, to see what names are avaliable

            if not label_parts or label_parts[-1] != line.local_name:
                if iso or result_locales(line, user_languages):
                    print(f"no transliteration needed for {line.local_name}")
                    label_parts.append(line.local_name)
                else:
                    label_parts.append(_transliterate(line, user_languages))

    return label_parts

def parse_lang(header) -> List[str]:
    """ Parse Accept-Language HTTP header into a list of normalized language codes
        Uses Nominatim Locales class to do so

        Is it better to place normalize lang here instead of in transliterate?
        I am just worried about breaking upstream processes
    """
    return napi.Locales.from_accept_languages(header).languages


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