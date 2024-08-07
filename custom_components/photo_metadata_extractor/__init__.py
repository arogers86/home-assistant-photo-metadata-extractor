import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "photo_metadata_extractor"

async def async_setup(hass, config):
    async def handle_extract_metadata(call):
        entity_id = call.data.get("entity_id")
        if entity_id:
            await hass.helpers.entity_component.async_update_entity(entity_id)

    hass.services.async_register(DOMAIN, "extract_metadata", handle_extract_metadata)
    _LOGGER.info("Registered service extract_metadata for domain photo_metadata_extractor")
    return True

async def async_setup_entry(hass, config_entry, async_add_entities):
    await async_setup_platform(hass, {}, async_add_entities)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([PhotoMetadataExtractor(hass, config)], True)
