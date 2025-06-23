# Proof of concept of transliteration using Nominatim as a library
# from nominatim_api.v1.format import dispatch as dispatch
import unicodedata
import nominatim_api as napi
from unidecode import unidecode
import asyncio
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
dictionary = None

async def search(query):
    """ Nominatim Search Query
    """
    async with napi.NominatimAPIAsync() as api:
        return await api.search(query, address_details=True)
        # return await api.search(query)

def lang_dictionary():
    """ Mock idea for language mapping dictionary
    """
    dictionary = {
        "zh": ["zh-cn", "zh-hans"],
        "zh-cn": ["zh-cn", "zh-hans"],
        "zh-hans": ["zh-hans", "zh-cn"],
        "zh-hant": ["zh-hant", "zh-tw"],
        "zh-tw": ["zh-tw", "zh-hant"],
    }

    return dictionary

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
            if any(target in key for key in address_part.names.keys()):
                return True
    return False


def result_transliterate(results, user_languages: List[str] = []) -> List[str]:
    """ High level transliteration result wrapper

        Prints out the transliterated results
        Returns output as list
    """
    output = []
    for i, result in enumerate(results):
        address_parts = transliterate(result, user_languages)
        print(f"{i + 1}. {', '.join(part.strip() for part in address_parts)}")
        output.append(", ".join(part.strip() for part in address_parts))
    return output


def _transliterate(text, locales: napi.Locales):
    """ Most granular transliteration component
        Performs raw transliteration based on locales

        Defaults to Latin
    """
    return unidecode(text)


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
    locales = napi.Locales(user_languages)
    label_parts: List[str] = []
    iso = False

    if not result.address_rows:
        return label_parts

    if bool(set(get_languages(result)) & set(user_languages)):
        iso = True

    for line in result.address_rows:
        if line.isaddress and line.names:

            if not iso:
                line.local_name = locales.display_name(line.names)
                # print(line.names) # For test cases, to see what names are avaliable

            if not label_parts or label_parts[-1] != line.local_name:
                if iso or result_locales(line, user_languages):
                    label_parts.append(line.local_name)
                else:
                    label_parts.append(_transliterate(line.local_name, locales))

    return label_parts


variable = 'hospital in dandong'
# variable = 'school in dandong'
results = asyncio.run(search(f"{variable}"))
result_transliterate(results, ['en'])
o = result_transliterate(results, ['ps'])
o = result_transliterate(results, ['km'])
print(o)
