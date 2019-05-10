#include "ina226.h"
#include "ltc2983.h"

#include <Arduino.h>
#include <ArduinoSTL.h>
#include <SPI.h>

constexpr auto V_BIAS_LNA_CHX = A6;
constexpr auto V_BIAS_LNA_CHY = A3;
constexpr auto V_BIAS_LNA_CHZ = A0;

constexpr auto M_CHX = A7;
constexpr auto M_CHY = A4;
constexpr auto M_CHZ = A1;

constexpr auto VDD_CHX = A8;
constexpr auto VDD_CHY = A5;
constexpr auto VDD_CHZ = A2;

constexpr uint8_t INA_CHX = 0x40;
constexpr uint8_t INA_CHY = 0x41;
constexpr uint8_t INA_CHZ = 0x44;

constexpr auto TempA           = LTC2983::Channel::CH4;
constexpr auto TempC           = LTC2983::Channel::CH6;
constexpr auto TempB           = LTC2983::Channel::CH8;
const LTC2983::Channel Temp[3] = {TempA, TempB, TempC};

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
    SPI.setClockDivider(SPI_CLOCK_DIV4);
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

static Ina226<500000, 50> currentMonitor{};
using SPI_dev = SPI_dev_t<0xff, 2>;
static Ltc2983<SPI_dev> ltc2983(SPI_dev{});

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(2000000);
  delay(1000);
  for(auto ina : {INA_CHX, INA_CHY, INA_CHZ})
  {
    currentMonitor.setup(ina, INA226::OperatingMode::BothContinuous,
                         INA226::ConvTime::cnv_140us,
                         INA226::ConvTime::cnv_140us, INA226::AvgNum::avg_16);
  }
  ltc2983.setup();
  for(const auto ch :
      {LTC2983::Channel::CH4, LTC2983::Channel::CH6, LTC2983::Channel::CH8})
  {
    ltc2983.configure_RTD(ch, LTC2983::SensorType::PT_1000,
                          LTC2983::Channel::CH2,
                          LTC2983::ExcitationCurrent::Cur500uA, 3333000,
                          LTC2983::MeasurementMode::TwoWires,
                          LTC2983::ExcitationMode::GroundInternal);
  }
  ltc2983.configure_MultipleConv(
      {LTC2983::Channel::CH4, LTC2983::Channel::CH6, LTC2983::Channel::CH8});
  ltc2983.start_Conv(LTC2983::Channel::Multiple);
  std::cout << "# Found " << 3 << " ina226" << std::endl;
  std::cout << "V_BIAS_LNA_CHX\t"
            << "V_BIAS_LNA_CHY\t"
            << "V_BIAS_LNA_CHZ\t"
            << "M_CHX\t"
            << "M_CHY\t"
            << "M_CHZ\t"
            << "VDD_CHX\t"
            << "VDD_CHY\t"
            << "VDD_CHZ\t"
            << "I_CHX\t"
            << "I_CHY\t"
            << "I_CHZ\t"
            << "V_CHX\t"
            << "V_CHY\t"
            << "V_CHZ\t"
            << "TempA\t"
            << "TempB\t"
            << "TempC\t"
            << "FrameNumber" << std::endl;
}

void loop()
{
  static uint32_t frame         = 0;
  static double temperatures[3] = {0., 0., 0.};
  bool measure_temp             = false;
  digitalWrite(LED_BUILTIN, HIGH);
  if(frame % 100 == 0) { measure_temp = true; }
  for(auto i : {V_BIAS_LNA_CHX, V_BIAS_LNA_CHY, V_BIAS_LNA_CHZ, M_CHX, M_CHY,
                M_CHZ, VDD_CHX, VDD_CHY, VDD_CHZ})
  {
    int sensorValue = analogRead(i);
    std::cout << sensorValue << "\t";
  }
  for(auto ina : {INA_CHX, INA_CHY, INA_CHZ})
  {
    std::cout << currentMonitor.microAmps(ina) << "\t";
  }
  for(auto ina : {INA_CHX, INA_CHY, INA_CHZ})
  {
    std::cout << currentMonitor.milliVolts(ina) << "\t";
  }
  if(measure_temp)
  {
    while(0x40 != ltc2983.status())
      ;
    for(auto i : {0, 1, 2})
    {
      temperatures[i] = ltc2983.temperature(Temp[i]);
    }
    ltc2983.start_Conv(LTC2983::Channel::Multiple);
  }

  for(auto i : {0, 1, 2})
  {
    std::cout << temperatures[i] << "\t";
  }

  std::cout << frame++ << std::endl;
  digitalWrite(LED_BUILTIN, LOW);
  delay(1);
}
