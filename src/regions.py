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
        # result = await api.lookup(places="R913110")
        result = await api.lookup(["R913110"])
        print(result)
        return result

# async def lookup(self, places: Sequence[ntyp.PlaceRef], **params: Any) -> SearchResults:
#     """ Get simple information about a list of places.

#         Returns a list of place information for all IDs that were found.
#     """
#     details = ntyp.LookupDetails.from_kwargs(params)
#     async with self.begin() as conn:
#         conn.set_query_timeout(self.query_timeout)
#         if details.keywords:
#             await nsearch.make_query_analyzer(conn)
#         return await get_places(conn, places, details)

hk = asyncio.run(get_hk_geojson())
print(hk)