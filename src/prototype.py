# Proof of concept of transliteration using Nominatim as a library
# from nominatim_api.v1.format import dispatch as dispatch
import unicodedata
import nominatim_api as napi
from unidecode import unidecode
import asyncio
import opencc
import yaml
from cantoroman import Cantonese # only works from cantonese (written zh-Hant script) to latin
from typing import Optional, Tuple, Dict, Sequence, TypeVar, Type, List, cast, Callable
from langdetect import detect, LangDetectException # for now, until can figure out why names default no langauge
from nominatim_api.typing import Protocol
from nominatim_api.config import Configuration
from nominatim_db.db.connection import Connection

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

