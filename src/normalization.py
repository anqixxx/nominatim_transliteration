# Normalization for User Languages & Header Files
import unicodedata
import nominatim_api as napi
from unidecode import unidecode
import opencc
import yaml
from cantoroman import Cantonese # only works from cantonese (written zh-Hant script) to latin
from typing import Optional, Tuple, Dict, Sequence, TypeVar, Type, List, cast, Callable
from langdetect import detect, LangDetectException # for now, until can figure out why names default no langauge

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
    # For zh-Latn-pinyin and zh-Latn, I did not include this as it is not really a spoken language
    # For now, no dialect support
    lang_dict = {
        "zh": "zh-Hans",
        "zh-cn": "zh-Hans", # only Simplfied 
        "zh-tw": "zh-Hant",
        "zh-hans": "zh-Hans",
        "zh-hant": "zh-Hant",
        "zh-Hans-CN": "zh-Hans",
        "zh-cmn": "zh-Hans",
        "zh-cmn-Hans": "zh-Hans",
        "zh-cmn-Hant": "zh-Hant"
        # add yue as cantonese
    }

    if lang in lang_dict:
    #  Ordering nessecary due to zh edge case (no '-')
        return lang_dict[lang]
    elif '-' not in lang:
        return lang
    return lang.split('-')[0] 


def parse_lang(header) -> List[str]:
    """ Parse Accept-Language HTTP header into a list of normalized language codes
        Uses Nominatim Locales class to do so

        Is it better to place normalize lang here instead of in transliterate?
        I am just worried about breaking upstream processes
    """
    languages = napi.Locales.from_accept_languages(header).languages
    return [normalize_lang(lang) for lang in languages] # both here and in transliterate, need to think about best logic flow
    # in final result, parse_lang will probably be part of larger script, just here right now in this form for testing modularity
    # should we allow for duplicates? this is only probably a big issue in English
    # would probably be better code if not
