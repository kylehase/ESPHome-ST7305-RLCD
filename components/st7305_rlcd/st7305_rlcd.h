/**
 * @file st7305_rlcd.h
 * @brief ESPHome driver for ST7305 reflective LCD displays
 *
 * Supports multiple panel configurations:
 * - Waveshare ESP32-S3-RLCD-4.2 (400×300) - also: GooDisplay GDTL042T71
 * - Osptek YDP154H008 (200×200)
 * - Custom user-defined panels
 *
 * References:
 * - ST7305 Datasheet: https://files.waveshare.com/wiki/common/ST_7305_V0_2.pdf
 * - Waveshare product: https://www.waveshare.com/wiki/ESP32-S3-RLCD-4.2
 *
 * @version 2.0.0
 */

#pragma once

#include "esphome/core/component.h"
#include "esphome/core/hal.h"
#include "esphome/components/spi/spi.h"
#include "esphome/components/display/display_buffer.h"

namespace esphome {
namespace st7305_rlcd {

/// Panel model enumeration
enum ST7305Model : uint8_t {
  ST7305_MODEL_WAVESHARE_400X300 = 0,  ///< Landscape 2×4 blocks
  ST7305_MODEL_OSPTEK_200X200,         ///< Square 4×2 blocks
  ST7305_MODEL_CUSTOM,                 ///< User-defined
};

/// Pixel block orientation (determines LUT calculation)
enum ST7305Orientation : uint8_t {
  ST7305_ORIENTATION_LANDSCAPE = 0,  ///< 2 cols × 4 rows per byte
  ST7305_ORIENTATION_PORTRAIT,       ///< 4 cols × 2 rows per byte
};

class ST7305RLCD : public display::DisplayBuffer,
                   public spi::SPIDevice<spi::BIT_ORDER_MSB_FIRST, spi::CLOCK_POLARITY_LOW,
                                         spi::CLOCK_PHASE_LEADING, spi::DATA_RATE_10MHZ> {
 public:
  void setup() override;
  void update() override;
  void dump_config() override;
  void fill(Color color) override;

  // Configuration setters (called from Python codegen)
  void set_dc_pin(GPIOPin *pin) { this->dc_pin_ = pin; }
  void set_reset_pin(GPIOPin *pin) { this->reset_pin_ = pin; }
  void set_model(ST7305Model model) { this->model_ = model; }
  void set_width(uint16_t width) { this->width_ = width; }
  void set_height(uint16_t height) { this->height_ = height; }
  void set_orientation(ST7305Orientation orientation) { this->orientation_ = orientation; }

  /// Enter sleep mode (lowest power, display blanks, RAM retained)
  void sleep();
  /// Exit sleep mode (120ms delay required by controller)
  void wake();
  /// Switch to low power refresh (~1Hz) for static content
  void low_power_mode();
  /// Switch to high power refresh (~51Hz) for animations
  void high_power_mode();
  /// Turn display on (recover from display_off)
  void display_on();
  /// Turn display off (RAM retained, instant recovery)
  void display_off();

  display::DisplayType get_display_type() override { return display::DisplayType::DISPLAY_TYPE_BINARY; }

 protected:
  void draw_absolute_pixel_internal(int x, int y, Color color) override;
  int get_width_internal() override { return this->width_; }
  int get_height_internal() override { return this->height_; }
  size_t get_buffer_length_() { return this->buffer_size_; }

  void apply_model_settings_();
  void hardware_reset_();
  void init_display_();
  void init_pixel_lut_();
  void init_lut_landscape_();
  void init_lut_portrait_();
  void write_display_();
  void send_command_(uint8_t cmd);
  void send_data_(uint8_t data);

  GPIOPin *dc_pin_{nullptr};
  GPIOPin *reset_pin_{nullptr};

  ST7305Model model_{ST7305_MODEL_WAVESHARE_400X300};
  ST7305Orientation orientation_{ST7305_ORIENTATION_LANDSCAPE};
  uint16_t width_{400};
  uint16_t height_{300};
  size_t buffer_size_{15000};

  // Address window parameters (panel-specific)
  uint8_t col_start_{0x12};
  uint8_t col_end_{0x2A};
  uint8_t row_start_{0x00};
  uint8_t row_end_{0xC7};

  // Pixel coordinate lookup tables for O(1) buffer access
  uint16_t *pixel_index_lut_{nullptr};
  uint8_t *pixel_bit_lut_{nullptr};
};

}  // namespace st7305_rlcd
}  // namespace esphome
