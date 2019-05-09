#include "ltc2983.h"

#include <Arduino.h>
#include <ArduinoSTL.h>
#include <LTC298X.h>
#include <SPI.h>

template<uint8_t RST_pin, uint8_t CS_pin> struct SPI_dev_t
{
  template<int PIN> void _set_pin(bool state)
  {
    if constexpr(PIN != 0xff)
    {
      if(state) { digitalWrite(PIN, HIGH); }
      else
      {
        digitalWrite(PIN, LOW);
      }
    }
  }
  void setup()
  {
    SPI.begin();
    SPI.setClockDivider(SPI_CLOCK_DIV8);
    SPI.setBitOrder(MSBFIRST);
    SPI.setDataMode(SPI_MODE0);
    if constexpr(CS_pin != 0xff) pinMode(CS_pin, OUTPUT);
    if constexpr(RST_pin != 0xff) pinMode(RST_pin, OUTPUT);
  }
  void reset(bool rst) { _set_pin<RST_pin>(rst); }
  void select(bool select) { _set_pin<CS_pin>(!select); }
  uint8_t write(const uint8_t val) const { return SPI.transfer(val); }
  uint16_t write(const uint16_t val) const { return SPI.transfer16(val); }
};

using SPI_dev = SPI_dev_t<0xff, 2>;

static Ltc2983<SPI_dev> ltc2983(SPI_dev{});

static LTC298X ltc2983bis(2);

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(3, OUTPUT);
  Serial.begin(2000000);
  delay(200);
  ltc2983.setup();
  for(const auto ch :
      {LTC2983::Channel::CH4, LTC2983::Channel::CH6, LTC2983::Channel::CH8})
  {
    ltc2983.configure_RTD(ch, LTC2983::SensorType::PT_1000,
                          LTC2983::Channel::CH2,
                          LTC2983::ExcitationCurrent::Cur250uA,
                          (static_cast<uint32_t>(10000) * 1000) / 3,
                          LTC2983::MeasurementMode::TwoWires,
                          LTC2983::ExcitationMode::GroundInternal);
  }
  //  ltc2983.configure_MultipleConv(
  //      {LTC2983::Channel::CH4, LTC2983::Channel::CH6,
  //      LTC2983::Channel::CH8});
  std::cout << "Status = " << static_cast<uint16_t>(ltc2983.satus())
            << std::endl;
}

void loop()
{
  static uint16_t address = 0;
  digitalWrite(LED_BUILTIN, HIGH);
  ltc2983.start_Conv(LTC2983::Channel::CH4);
  std::cout << "Status = " << static_cast<uint16_t>(ltc2983.satus()) << "...";
  // ltc2983bis.beginConversion(9);
  delay(500);
  std::cout << static_cast<uint16_t>(ltc2983.satus()) << std::endl;
  std::cout << std::hex << ltc2983.adc_result(LTC2983::Channel::CH4)
            << std::endl;
  //            << ltc2983.adc_result(LTC2983::Channel::CH6)
  //            << ltc2983.adc_result(LTC2983::Channel::CH8) << std::endl;
  digitalWrite(LED_BUILTIN, LOW);
}
