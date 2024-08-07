# Home Assistant Photo Metadata Extractor

Home Assistant custom component to extract photo metadata.

## Installation

Copy the `custom_components/photo_metadata_extractor` folder to your Home Assistant configuration directory.

## Configuration

Add the following to your `configuration.yaml`:

```yaml
sensor:
  - platform: photo_metadata_extractor
    image_path: "/path/to/your/image.jpg"
    entity_name: "sensor.wall_panel_photo_metadata"
    device_class: "timestamp"
    icon: "mdi:camera"
