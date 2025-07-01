# Normalization for User Languages & Header Files
import nominatim_api as napi
from typing import Optional, Tuple, Dict, Sequence, TypeVar, Type, List, cast, Callable
import re

def normalize_lang(lang):
    """ Mock idea for language mapping dictionary

        Hoping to standardize certain names, i.e.
        zh and zh-cn will always map to zh-Hans
        zh-tw will always map to zh-Hant

        In the case of ambiguity, the largest number of 
        languages will be added

        For all other languages, follow Nominatim precedent
        and just concatenate after the '-'

        Code assumes all language codes are in two letter format 
        https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes 
        with the exception of yue 
    """
    # Potentially make this a global variable (or object field) to reduce compute
    # For zh-Latn-pinyin and zh-Latn, I did not include this as it is not really a spoken language
    # For now, no dialect support
    lang_dict = {
        "zh": ["zh-Hans", "zh-Hant", "yue"], # zh covers zh-Hans, zh-Hant, yue
        "zh-cn": ["zh-Hans"], # only Simplfied 
        "zh-tw": ["zh-Hant"], # only Traditional Mandarin
        "zh-hans": ["zh-Hans"],
        "zh-hant": ["zh-Hant", "yue"], # Traditional implies both canto & mando
        "zh-Hans-CN": ["zh-Hans"], # only Simplfied 
        "zh-cmn": ["zh-Hans"], # only Simplified, cmn means Mandarin
        "zh-cmn-Hans": ["zh-Hans"],  # only Simplified, cmn means Mandarin
        "zh-cmn-Hant": ["zh-Hant"]  # only Traditional, cmn means Mandarin
    }

    if lang in lang_dict:
    #  Ordering nessecary due to zh edge case (no '-')
        return lang_dict[lang]
    elif '-' not in lang:
        return [lang]
    return [lang.split('-')[0]]


def parse_languages(langstr: str) -> List[str]:
    """ Create a localization object from a language list in the
        format of HTTP accept-languages header.

        The functions tries to be forgiving of format errors by first splitting
        the string into comma-separated parts and then parsing each
        description separately. Badly formatted parts are then ignored.

        Using the additional normalization transliteration constraints,
        then returns the larguage in its normalized form, as well as the regional 
        dialect, if applicable.

        The regional dialect always takes precedence

        Languages are returned in lowercase form
    """
    # split string into languages
    candidates = []
    for desc in langstr.split(','):
        m = re.fullmatch(r'\s*([a-z_-]+)(?:;\s*q\s*=\s*([01](?:\.\d+)?))?\s*',
                            desc, flags=re.I)
        if m:
            candidates.append((m[1], float(m[2] or 1.0)))

    # sort the results by the weight of each language (preserving order).
    candidates.sort(reverse=True, key=lambda e: e[1])

    # if a language has a region variant, ignore it
    # we want base transliteration language only
    languages = []
    for lid, _ in candidates:
        lid = lid

        if lid not in languages:
            languages.append(lid)

        normalized = normalize_lang(lid)
        for norm_lang in normalized:
            if norm_lang not in languages:
                languages.append(norm_lang)
    return languages