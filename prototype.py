# Proof of concept of transliteration using Nominatim as a library

import nominatim_api as napi
from unidecode import unidecode
import asyncio

async def search(query):
    async with napi.NominatimAPIAsync() as api:
        return await api.search(query, address_details=True)
        # return await api.search(query)

def transliterate(text): #  only latin transliteration
    return unidecode(text)

variable = 'hospital in dandong'
results = asyncio.run(search(f"{variable}"))

if not results:
    print(f'Cannot find {variable}')
else:
    print(f'Found a place at {results[0].centroid.x},{results[0].centroid.y}')
    
    print('\nOriginal Result: ')
    locale = napi.Locales(['chinese']) 
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

    print('\n Combination Result: ')
    locale = napi.Locales(['en']) 
    for i, result in enumerate(results):
        address_parts = result.address_rows.localize(locale)
        print(f"{i + 1}. {', '.join(unidecode(part) for part in address_parts)}")

    print('\n Reverse Result: ')
    locale = napi.Locales(['en']) 
    for i, result in enumerate(results):
        address_parts = result.address_rows.localize(locale)
        print(f"{i + 1}. {', '.join(unidecode(part) for part in address_parts)}")