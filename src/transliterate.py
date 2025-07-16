# Proof of concept of transliteration using Nominatim as a library
# from nominatim_api.v1.format import dispatch as dispatch
import nominatim_api as napi
from unidecode import unidecode
import opencc
import yaml
from cantoroman import Cantonese # only works from cantonese (written zh-Hant script) to latin
from typing import Optional, Tuple, Sequence, TypeVar, Type, List, cast, Callable, Mapping
from langdetect import detect, LangDetectException # for now, until can figure out why names default no langauge
from nominatim_api.config import Configuration
from nominatim_db.db.connection import Connection
import os


country_data = None
latin_data = None
lang_data = None

class Transliterator():
    """
        Class handling the process of transliteration from search results.
    """
    def __init__(self, config: Configuration, conn: Connection) -> None:
        self.config = config
        self.db_connection = conn
        self.country_data = None
        self.lang_data = None


def load_country_info(yaml_path=None):
    """ Loads country_settings
        Yaml files from Nominatim blob/master/settings/country_settings.yaml 
    """
    if yaml_path is None:
        current_dir = os.path.dirname(__file__)
        yaml_path = os.path.join(current_dir, "..", "country_settings.yaml")

    with open(yaml_path, 'r') as file:
        return yaml.safe_load(file)


def load_latin(yaml_path=None):
    """ Loads latin_languages.yaml

        Will only work on two-letter ISO 639 language codes
        with the exception of yue, which is also included
    """
    if yaml_path is None:
        current_dir = os.path.dirname(__file__)
        yaml_path = os.path.join(current_dir, "..", "latin_languages.yaml")

    with open(yaml_path, 'r') as file:
        return yaml.safe_load(file)
    

def load_lang_info(yaml_path=None):
    """ Loads language information on writing system

    Will only work on two-letter ISO 639 language codes
    with the exception of yue, which is also included
    """
    if yaml_path is None:
        current_dir = os.path.dirname(__file__)
        yaml_path = os.path.join(current_dir, "..", "languages.yaml")

    with open(yaml_path, 'r') as file:
        return yaml.safe_load(file)

def get_languages(result):
    """ Given a result, returns the languages associated with the region

        Special handling is needed for Macau and Hong Kong (not in yaml)
    """
    global country_data

    if not country_data:
        country_data = load_country_info()

    country = country_data.get(result.country_code.lower())
    if country and 'languages' in country:
        return [lang.strip() for lang in country['languages'].split(',')]
    return []


def latin(language_code) -> bool:
    """ Using latin_languages.yaml, returns if the 
        given language is latin based or not.

        If the code does not exist in the yaml file, it 
        will return false. This works as, due to normalization,
        we assume that the "prime" version of the code is also in 
        the user languages, so it will eventually execute

        Will only work on two-letter ISO 639 language codes
        with the exception of yue, which is also included
    """
    global lang_data

    if not lang_data:
        lang_data = load_lang_info()

    language = lang_data.get(language_code)
    if language:
        return language['written'] == 'lat'
    return False


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


def decode_canto(line: str) -> str:
    """ Takes in a string in Cantonese and returns the Latin
        transliterated version. 
        Uses the cantoroman library, named as so to be homogenous
        with unidecode

        For cases with multiple pronounciation, the first is always taken
    """
    cantonese = Cantonese() # perhaps make into global variable later
    cantonese_line = ""
    for char in line:
        cantonese_line += cantonese.getRoman(char)[0][0].capitalize()
        cantonese_line += ' '
    return cantonese_line.strip()


def _transliterate(line: napi.AddressLine, locales: List[str], in_cantonese: bool = False):
    """ Most granular transliteration component
        Performs raw transliteration based on locales

        Defaults to Latin
    """
    # in_cantonese is a placeholder for now until we determine HK and Macau mapping

    for locale in locales:
        # Need to replace to be a valid function
        _function = f"{locale.replace("-", "_")}_transliterate"
        if _function in globals():
            print(f"{locale} transliteration successful")
            return globals()[_function](line)
        elif latin(locale):
            print("latin based language detected, latin transliteration occuring")
            if not in_cantonese:
                return unidecode(line.local_name)
            else:
                return decode_canto(line.local_name)
    
    print("defaulting to latin based transliteration")
    if not in_cantonese:
        return unidecode(line.local_name)
    else:
        return decode_canto(line.local_name)


def zh_Hans_transliterate(line: napi.AddressLine):
    """ If in Traditional Chinese, convert to Simplified
        NOT TESTED, PROOF OF CONCEPT

        Else switch to standard Latin default transliteration
    """
    if line.local_name_lang == 'zh-hant':
        converter = opencc.OpenCC('t2s.json') # t2s.json Traditional Chinese to Simplified Chinese 繁體到簡體
        return converter.convert(line.local_name)
    return unidecode(line.local_name)


def zh_Hant_transliterate(line: napi.AddressLine):
    """ If in Simplified Chinese, convert to Traditional

        Else switch to standard Latin default transliteration
    """
    if line.local_name_lang == 'zh-hans' or line.local_name_lang == 'zh-CN': # also need a way to know it its in chinese or not
        converter = opencc.OpenCC('s2t.json') # t2s.json Traditional Chinese to Simplified Chinese 繁體到簡體
        return converter.convert(line.local_name)
    return unidecode(line.local_name)


def yue_transliterate(line: napi.AddressLine):
    """ If in Simplified Chinese, convert to Traditional

        Else switch to standard Latin default transliteration
    """
    if line.local_name_lang == 'zh-hans' or line.local_name_lang == 'zh':
        converter = opencc.OpenCC('s2t.json') # t2s.json Traditional Chinese to Simplified Chinese 繁體到簡體
        return converter.convert(line.local_name)
    return unidecode(line.local_name)


def transliterate(result, user_languages: List) -> str:
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

    if len(local_languages) == 1 and local_languages[0] in user_languages:
        iso = True
        line.local_name_lang = local_languages[0] # can potentially do more with this

    for line in result.address_rows:
        if line.isaddress and line.names:

            if not iso:
                line.local_name, line.local_name_lang = display_name_with_locale(user_languages, line.names) # new identifier, local_name_lang

                # print(line.names) # For test cases, to see what names are avaliable
                # dont use this function for Locales
                # want to replace this

            if not label_parts or label_parts[-1] != line.local_name:
                if iso or line.local_name_lang in user_languages:
                    print(f"no transliteration needed for {line.local_name}")
                    label_parts.append(line.local_name)
                else:
                    label_parts.append(_transliterate(line, user_languages))

    return ", ".join(part.strip() for part in label_parts)


def display_name_with_locale(name_tags: List[str], names: Optional[Mapping[str, str]]) -> Tuple[str, str]:
    """ Return the best matching name from a dictionary of names
        containing different name variants, as well as an identifier 
        with regards to what language used

        If 'names' is null or empty, an empty tuple is returned. If no
        appropriate localization is found, the first name is returned with
        the 'default' marker, where afterwards iso is used.
    """
    if not names:
        return ['', '']
    if len(names) > 1:
        for tag in name_tags:
            alt_name = f"alt_name:{tag}"
            name = f"name:{tag}"

            if name in names:
                return [names[name], tag]
            elif alt_name in names:
                return [names[alt_name], tag]

    # Nothing? Return any of the other names as a default.
    if 'name' in names:
        return [names['name'], "default"] # without this will return ref before name
    return [next(iter(names.values())), "default"] # want to see what this will return


async def search(query):
    """ Nominatim Search Query
    """
    async with napi.NominatimAPIAsync() as api:
        return await api.search(query, address_details=True)
        # return await api.search(query)