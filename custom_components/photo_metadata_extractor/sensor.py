import logging
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import async_update_entity
import exifread
from datetime import datetime
from geopy.geocoders import Nominatim

_LOGGER = logging.getLogger(__name__)

# List of preferred keys
preferred_keys = [
    'emergency', 'historic', 'military', 'natural', 'landuse', 'place', 'railway', 
    'man_made', 'aerialway', 'boundary', 'amenity', 'aeroway', 'club', 'craft', 
    'leisure', 'office', 'mountain_pass', 'shop', 'tourism', 'bridge', 'tunnel', 'waterway'
]

def extract_metadata_sync(image_path):
    try:
        # Open image file for reading (binary mode)
        with open(image_path, 'rb') as f:
            # Return Exif tags
            tags = exifread.process_file(f)

        # Extract date and time
        date_taken = tags.get('EXIF DateTimeOriginal')
        if date_taken:
            date_taken = str(date_taken)
            date_object = datetime.strptime(date_taken, '%Y:%m:%d %H:%M:%S')
            date = date_object.strftime('%Y-%m-%dT%H:%M:%S')
            time = date_object.strftime('%H:%M')
        else:
            date = "Unknown"
            time = "Unknown"

        # Extract GPS information
        gps_latitude = tags.get('GPS GPSLatitude')
        gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
        gps_longitude = tags.get('GPS GPSLongitude')
        gps_longitude_ref = tags.get('GPS GPSLongitudeRef')

        if gps_latitude and gps_longitude and gps_latitude_ref and gps_longitude_ref:
            lat = [float(x.num) / float(x.den) for x in gps_latitude.values]
            lon = [float(x.num) / float(x.den) for x in gps_longitude.values]

            lat_ref = gps_latitude_ref.values[0]
            lon_ref = gps_longitude_ref.values[0]

            latitude = lat[0] + lat[1] / 60 + lat[2] / 3600
            longitude = lon[0] + lon[1] / 60 + lon[2] / 3600

            if lat_ref != 'N':
                latitude = -latitude
            if lon_ref != 'E':
                longitude = -longitude

            gps_coordinates = (latitude, longitude)

            # Reverse geocoding to get location details
            geolocator = Nominatim(user_agent="my_geopy_application")
            location = geolocator.reverse(gps_coordinates, exactly_one=True, addressdetails=True)

            # Debugging information
            _LOGGER.debug("Reverse geocoding response: %s", location.raw if location else "No location found")

            if location and 'address' in location.raw:
                address = location.raw['address']
                
                # Check for preferred keys in address
                location_name = None
                for key in preferred_keys:
                    if key in address:
                        location_name = address[key]
                        break
                
                if not location_name:
                    # Default to formatted address if no preferred keys found
                    street = address.get('road', 'Unknown street')
                    suburb = address.get('town', address.get('suburb', address.get('neighbourhood', 'Unknown suburb')))
                    state = address.get('state', 'Unknown state')
                    country = address.get('country', 'Unknown country')
                    location_name = f"{street}, {suburb}, {state}, {country}"
            else:
                location_name = "Unknown location"
        else:
            gps_coordinates = ("Unknown", "Unknown")
            location_name = "Unknown location"

        return date, time, gps_coordinates, location_name

    except Exception as e:
        _LOGGER.error(f"Error during metadata extraction: {e}")
        return "Unknown", "Unknown", ("Unknown", "Unknown"), "Unknown location"

class PhotoMetadataExtractor(Entity):
    def __init__(self, hass, config):
        self._hass = hass
        self._config = config
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return self._config.get("entity_name", "photo_metadata_extractor")

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return self._config.get("icon", "mdi:camera")

    @property
    def device_class(self):
        return self._config.get("device_class", "timestamp")

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        _LOGGER.debug("Updating photo metadata")
        image_path = self._config["image_path"]
        date, time, gps_coordinates, location_name = await self._hass.async_add_executor_job(extract_metadata_sync, image_path)
        self._state = date
        self._attributes = {
            "time_taken": time,
            "gps_coordinates": {
                "latitude": gps_coordinates[0],
                "longitude": gps_coordinates[1]
            },
            "location_name": location_name
        }

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([PhotoMetadataExtractor(hass, config)], True)

async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([PhotoMetadataExtractor(hass, config_entry.data)], True)
