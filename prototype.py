# Proof of concept of transliteration using Nominatim as a library

import nominatim_api as napi

import asyncio

async def search(query):
    async with napi.NominatimAPIAsync() as api:
        return await api.search(query)

variable = 'yi yuan'
results = asyncio.run(search(f"{variable}"))
if not results:
    print(f'Cannot find {variable}')
else:
    print(f'Found a place at {results[0].centroid.x},{results[0].centroid.y}')