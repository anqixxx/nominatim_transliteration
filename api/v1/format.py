from nominatim_api import FormatDispatcher, SearchResults
from nominatim_api.server.content_types import CONTENT_TEXT
from typing import List, Dict, Mapping, Any, Union
from nominatim_api.v1.format import dispatch as default_dispatch
from nominatim_api.results import AddressLines, ReverseResults, SearchResults
from nominatim_api.server.content_types import CONTENT_TEXT
from nominatim_api.utils.json_writer import JsonWriter
from nominatim_api.v1.format_json import format_base_json, format_base_geocodejson, _write_osm_id, _write_typed_address
from nominatim_api.v1 import classtypes as cl

from transliterate import result_transliterate, transliterate

# extend default dispatcher
dispatch = default_dispatch

dispatch.set_content_type('transliteration', CONTENT_TEXT) # new type of content type

@dispatch.format_func(SearchResults, 'anqi')
def _format_search_anqi(results: SearchResults,
                        options: Mapping[str, Any]) -> str:
    print("Anqi's Version:")

    return None

@dispatch.format_func(SearchResults, 'transliteration')
def _format_transliteration(results: SearchResults,
                            options: Mapping[str, Any]) -> str:
    """ Return the result list as a simple json string in custom Nominatim format.
        with the addition or transliteration field and without
        class label or simple.
    """
    if not results:
        return '{"error":"Unable to geocode"}'
      
    locales = options.get("locales")

    user_languages = locales.languages if locales else []

    out = JsonWriter() # similar to format_base_json

    # based on format_base_json and format_base_geojson
    for result in results:
        out.start_object()\
            .keyval_not_none('place_id', result.place_id)\
            .keyval('licence', cl.OSM_ATTRIBUTION)\

        _write_osm_id(out, result.osm_object)

        out.keyval('place_rank', result.rank_search)\
           .keyval('category', result.category[0])\
           .keyval('type', result.category[1])\
           .keyval('importance', result.calculated_importance())\
           .keyval('addresstype', cl.get_label_tag(result.category, result.extratags,
                                                   result.rank_address,
                                                   result.country_code))\
           .keyval('name', result.locale_name or '')\
           .keyval('display_name', result.display_name or '')

        if options.get('addressdetails', False):
            out.key('address').start_object()
            _write_typed_address(out, result.address_rows, result.country_code)
            out.end_object().next()

        if options.get('extratags', False):
            out.keyval('extratags', result.extratags)

        if options.get('namedetails', False):
            out.keyval('namedetails', result.names)

        # get the transliteration string for this result
        translit_str = transliterate(result, user_languages)

        # include the transliteration in output
        out.keyval('transliterated_name', translit_str or "")

        out.end_object().next()  # properties

        out.key('bbox').start_array()
        for coord in cl.bbox_from_result(result).coords:
            out.float(coord, 7).next()
        out.end_array().next()

        out.key('geometry').raw(result.geometry.get('geojson')
                                or result.centroid.to_geojson()).next()

        out.end_object().next()

    out.end_array().next().end_object()

    return out()


