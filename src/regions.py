# Proof of concept of regional detection
import nominatim_api as napi
import asyncio

async def search(query):
    """ Nominatim Search Query
    """
    async with napi.NominatimAPIAsync() as api:
        return await api.search(query, address_details=True)
        # return await api.search(query)

async def get_hk_geojson():
    """ Nominatim Search Query modified for Hong Kong
    """
    async with napi.NominatimAPIAsync() as api:
        # result = await api.lookup(places="R913110", polygon_geojson=True)
        result = await api.lookup("R913110")
        print(result)
        # return result[0].geometry["geojson"]

hk = asyncio.run(get_hk_geojson())
print(hk)