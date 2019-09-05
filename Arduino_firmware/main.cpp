#include "ina226.h"
#include "ltc2983.h"

#include <Arduino.h>
#include <ArduinoSTL.h>
#include <SPI.h>


constexpr auto CS_ADC = 10;

constexpr auto V_BIAS_LNA_CHX = A0;
constexpr auto V_BIAS_LNA_CHY = A5;
constexpr auto V_BIAS_LNA_CHZ = A10;

constexpr auto M_CHX = A1;
constexpr auto M_CHY = A6;
constexpr auto M_CHZ = A11;

constexpr auto VDD_CHX = A2;
constexpr auto VDD_CHY = A7;
constexpr auto VDD_CHZ = A12;

constexpr auto OUT2_INV_CHX = A3;
constexpr auto OUT2_INV_CHY = A8;
constexpr auto OUT2_INV_CHZ = A13;

constexpr auto OUT2_NINV_CHX = A4;
constexpr auto OUT2_NINV_CHY = A9;
constexpr auto OUT2_NINV_CHZ = A14;

/*
constexpr uint8_t INA_CHX = 0x40;
constexpr uint8_t INA_CHY = 0x44;
constexpr uint8_t INA_CHZ = 0x41;

constexpr auto TempA           = LTC2983::Channel::CH4;
constexpr auto TempC           = LTC2983::Channel::CH6;
constexpr auto TempB           = LTC2983::Channel::CH8;
const LTC2983::Channel Temp[3] = {TempA, TempB, TempC};*/

/*
template<uint8_t RST_pin, uint8_t CS_pin> struct SPI_dev_t                  //Creat a template of SPI_dev with 2 8bits unsigned int
{
  template<int PIN> void _set_pin(bool state)
  {
    if constexpr(PIN != 0xff)                                               //If the PIN exist
    {
      if(state) { digitalWrite(PIN, HIGH); }                                //set it to the desired "state"
      else
      {
          digitalWrite(PIN, LOW);
      }
    }
  }
  void setup()
  {
    SPI.begin();
    SPI.setClockDivider(SPI_CLOCK_DIV2);                                    //SPI Communication frequency at 8MHz (16MHz/2)
    SPI.setBitOrder(MSBFIRST);
    SPI.setDataMode(SPI_MODE2);                                             //For AD7490BRUZ CLK default is at 1, Get data at falling edge, Send at Rising
    if constexpr(CS_pin != 0xff) pinMode(CS_pin, OUTPUT);                   //Setup CS Pin
    if constexpr(RST_pin != 0xff) pinMode(RST_pin, OUTPUT);                 //Setup RST Pin
  }
  void reset(bool rst) { _set_pin<RST_pin>(rst); }
  void select(bool select) { _set_pin<CS_pin>(!select); }
  uint8_t write(const uint8_t val) const { return SPI.transfer(val); }
  uint16_t write(const uint16_t val) const { return SPI.transfer16(val); }
};

static Ina226<500000, 50> currentMonitor{};
using SPI_dev = SPI_dev_t<0xff, 23>;                                         //Setup SPI with CS_pin an pin 23 (PWM 10), RSt_pin as NULL
static Ltc2983<SPI_dev> ltc2983(SPI_dev{});

*/

void setupADC() {
  // take the SS pin low to select the chip:
  digitalWrite(CS_ADC, LOW);
  delay(100);
  //  send the control :
  SPI.transfer(0b101110110000);                                             //AD7490 Control register
  delay(100);
  // take the SS pin high to de-select the chip:
  digitalWrite(CS_ADC, HIGH);
}

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(2000000);
  delay(1000);
  
  SPI.begin();
  SPI.setClockDivider(SPI_CLOCK_DIV2);                                      //SPI Communication frequency at 8MHz (16MHz/2)
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE2);                                               //For AD7490BRUZ CLK default is at 1, Get data at falling edge, Send at Rising
  pinMode(CS_ADC, OUTPUT);                                                  // initalize the  data ready and chip select pins:
  setupADC();


  /*
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
                          LTC2983::ExcitationCurrent::Cur250uA, 3500000,
                          LTC2983::MeasurementMode::TwoWires,
                          LTC2983::ExcitationMode::GroundInternal,
                          LTC2983::RTDCurve::EuropeanStandard);
    delay(10);
  }

  ltc2983.configure_MultipleConv(
      {LTC2983::Channel::CH4, LTC2983::Channel::CH6, LTC2983::Channel::CH8});
  delay(200);
  ltc2983.start_Conv(LTC2983::Channel::Multiple);
  */

  std::cout << "# Found " << 3 << " channels" << std::endl;
  std::cout << "V_BIAS_LNA_CHX\t"
            << "V_BIAS_LNA_CHY\t"
            << "V_BIAS_LNA_CHZ\t"
            << "M_CHX\t"
            << "M_CHY\t"
            << "M_CHZ\t"
            << "VDD_CHX\t"
            << "VDD_CHY\t"
            << "VDD_CHZ\t"
            << "OUT2_INV_CHX\t"
            << "OUT2_INV_CHY\t"
            << "OUT2_INV_CHZ\t"
            << "OUT2_NINV_CHX\t"
            << "OUT2_NINV_CHY\t"
            << "OUT2_NINV_CHZ\t"
            << "FrameNumber" << std::endl;
}

void loop()
{

  digitalWrite(LED_BUILTIN, HIGH);
  for(auto i : {V_BIAS_LNA_CHX, V_BIAS_LNA_CHY, V_BIAS_LNA_CHZ,
                M_CHX, M_CHY, M_CHZ,
                VDD_CHX, VDD_CHY, VDD_CHZ,
                OUT2_INV_CHX, OUT2_INV_CHY, OUT2_INV_CHZ,
                OUT2_NINV_CHX, OUT2_NINV_CHY, OUT2_NINV_CHZ})
  {
    int sensorValue = analogRead(i);
    std::cout << sensorValue << "\t";
  }


  int testAdcConv = 0;

  for(auto i : {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15})
  {
    uint16_t adcValue = SPI.transfer16(0b0);
    if (i == adcValue >> 12)
    std::cout << adcValue << "\t";

    if (i == adcValue >> 12) {testAdcConv++;}
  }

  /*
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

  std::cout << frame++ << std::endl;*/
  std::cout << testAdcConv << std::endl;
  digitalWrite(LED_BUILTIN, LOW);
  delay(1);
}
