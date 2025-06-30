from nominatim_api import FormatDispatcher, SearchResults
from nominatim_api.server.content_types import CONTENT_TEXT
from typing import List, Dict, Mapping, Any, Union
from nominatim_api.results import AddressLines, ReverseResults, SearchResults


# Stole from format_json.py :) --> can probably do a cleaner import but whatever
def format_base_json(results: Union[ReverseResults, SearchResults],
                     options: Mapping[str, Any], simple: bool,
                     class_label: str) -> str:
    """ Return the result list as a simple json string in custom Nominatim format.
    """
    out = JsonWriter()

    if simple:
        if not results:
            return '{"error":"Unable to geocode"}'
    else:
        out.start_array()

    for result in results:
        out.start_object()\
             .keyval_not_none('place_id', result.place_id)\
             .keyval('licence', cl.OSM_ATTRIBUTION)\

        _write_osm_id(out, result.osm_object)

        # lat and lon must be string values
        out.keyval('lat', f"{result.centroid.lat:0.7f}")\
           .keyval('lon', f"{result.centroid.lon:0.7f}")\
           .keyval(class_label, result.category[0])\
           .keyval('type', result.category[1])\
           .keyval('place_rank', result.rank_search)\
           .keyval('importance', result.calculated_importance())\
           .keyval('addresstype', cl.get_label_tag(result.category, result.extratags,
                                                   result.rank_address,
                                                   result.country_code))\
           .keyval('name', result.locale_name or '')\
           .keyval('display_name', result.display_name or '')

        if options.get('icon_base_url', None):
            icon = cl.ICONS.get(result.category)
            if icon:
                out.keyval('icon', f"{options['icon_base_url']}/{icon}.p.20.png")

        if options.get('addressdetails', False):
            out.key('address').start_object()
            _write_typed_address(out, result.address_rows, result.country_code)
            out.end_object().next()

        if options.get('extratags', False):
            out.keyval('extratags', result.extratags)

        if options.get('namedetails', False):
            out.keyval('namedetails', result.names)

        # must be string values
        bbox = cl.bbox_from_result(result)
        out.key('boundingbox').start_array()\
           .value(f"{bbox.minlat:0.7f}").next()\
           .value(f"{bbox.maxlat:0.7f}").next()\
           .value(f"{bbox.minlon:0.7f}").next()\
           .value(f"{bbox.maxlon:0.7f}").next()\
           .end_array().next()

        if result.geometry:
            for key in ('text', 'kml'):
                out.keyval_not_none('geo' + key, result.geometry.get(key))
            if 'geojson' in result.geometry:
                out.key('geojson').raw(result.geometry['geojson']).next()
            out.keyval_not_none('svg', result.geometry.get('svg'))

        out.end_object()

        if simple:
            return out()

        out.next()

    out.end_array()

    return out()

dispatch = FormatDispatcher()

@dispatch.format_func(SearchResults, 'anqi')
def _format_search_anqi(results: SearchResults,
                        options: Mapping[str, Any]) -> str:
    print("Anqi's Version:")

    return format_base_json(results, options, False,
                                        class_label='class')

