"""ESPHome ST7305 RLCD Display Component Configuration."""

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import pins
from esphome.components import display, spi
from esphome.const import (
    CONF_DC_PIN,
    CONF_ID,
    CONF_LAMBDA,
    CONF_MODEL,
    CONF_RESET_PIN,
    CONF_UPDATE_INTERVAL,
    CONF_WIDTH,
    CONF_HEIGHT,
)

DEPENDENCIES = ["spi"]
AUTO_LOAD = ["display"]

CONF_ORIENTATION = "orientation"

st7305_rlcd_ns = cg.esphome_ns.namespace("st7305_rlcd")
ST7305RLCD = st7305_rlcd_ns.class_(
    "ST7305RLCD",
    display.DisplayBuffer,
    spi.SPIDevice,
)

# Model enumeration
ST7305Model = st7305_rlcd_ns.enum("ST7305Model")
MODELS = {
    "WAVESHARE_400X300": ST7305Model.ST7305_MODEL_WAVESHARE_400X300,
    "OSPTEK_200X200": ST7305Model.ST7305_MODEL_OSPTEK_200X200,
    "CUSTOM": ST7305Model.ST7305_MODEL_CUSTOM,
}

# Orientation enumeration (for custom panels)
ST7305Orientation = st7305_rlcd_ns.enum("ST7305Orientation")
ORIENTATIONS = {
    "LANDSCAPE": ST7305Orientation.ST7305_ORIENTATION_LANDSCAPE,
    "PORTRAIT": ST7305Orientation.ST7305_ORIENTATION_PORTRAIT,
}


def validate_custom_panel(config):
    """Validate that custom panels have required dimensions."""
    if config.get(CONF_MODEL) == "CUSTOM":
        if CONF_WIDTH not in config or CONF_HEIGHT not in config:
            raise cv.Invalid(
                "Custom model requires 'width' and 'height' to be specified"
            )
        if CONF_ORIENTATION not in config:
            raise cv.Invalid(
                "Custom model requires 'orientation' (LANDSCAPE or PORTRAIT)"
            )
    return config


CONFIG_SCHEMA = cv.All(
    display.FULL_DISPLAY_SCHEMA.extend(
        {
            cv.GenerateID(): cv.declare_id(ST7305RLCD),
            cv.Required(CONF_DC_PIN): pins.gpio_output_pin_schema,
            cv.Optional(CONF_RESET_PIN): pins.gpio_output_pin_schema,
            cv.Optional(CONF_MODEL, default="WAVESHARE_400X300"): cv.enum(
                MODELS, upper=True, space="_"
            ),
            # Default to manual updates for low-power operation
            cv.Optional(CONF_UPDATE_INTERVAL, default="never"): cv.update_interval,
            # For custom panels
            cv.Optional(CONF_WIDTH): cv.int_range(min=1, max=800),
            cv.Optional(CONF_HEIGHT): cv.int_range(min=1, max=800),
            cv.Optional(CONF_ORIENTATION): cv.enum(ORIENTATIONS, upper=True),
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
    .extend(spi.spi_device_schema(cs_pin_required=True)),
    validate_custom_panel,
)


async def to_code(config):
    """Generate C++ code from configuration."""
    var = cg.new_Pvariable(config[CONF_ID])

    # Register with parent classes
    # Note: register_display() calls register_component() internally
    await display.register_display(var, config)
    await spi.register_spi_device(var, config)

    # Configure pins
    dc_pin = await cg.gpio_pin_expression(config[CONF_DC_PIN])
    cg.add(var.set_dc_pin(dc_pin))

    if CONF_RESET_PIN in config:
        reset_pin = await cg.gpio_pin_expression(config[CONF_RESET_PIN])
        cg.add(var.set_reset_pin(reset_pin))

    # Set model
    cg.add(var.set_model(config[CONF_MODEL]))

    # Custom panel settings
    if config[CONF_MODEL] == "CUSTOM":
        cg.add(var.set_width(config[CONF_WIDTH]))
        cg.add(var.set_height(config[CONF_HEIGHT]))
        cg.add(var.set_orientation(config[CONF_ORIENTATION]))

    # Register lambda for display updates
    if CONF_LAMBDA in config:
        lambda_ = await cg.process_lambda(
            config[CONF_LAMBDA], [(display.DisplayRef, "it")], return_type=cg.void
        )
        cg.add(var.set_writer(lambda_))
