# Proof of concept of transliteration using Nominatim as a library
import nominatim_api as napi
from unidecode import unidecode
import asyncio
from nominatim_api import StatusResult

async def search(query):
    async with napi.NominatimAPIAsync() as api:
        return await api.search(query)
        # return await api.search(query)

def transliterate(text): #  only latin transliteration
    return unidecode(text)

variable = 'hospital in dandong'
results = asyncio.run(search(f"{variable}"))

if not results:
    print(f'Cannot find {variable}')
else:
    print(f'Found a place at {results[0].centroid.x},{results[0].centroid.y}')
    
    for i, result in enumerate(results):
        print(result)
        print(result.names)
        print(result.locale_name)
        print(result.display_name)

        print('\nOriginal Result Display: ')
        print(result.display_name)

        print('\nTransliterated Result Display: ')
        print(transliterate(result.display_name))
