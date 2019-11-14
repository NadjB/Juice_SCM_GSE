#include "ina226.h"
#include "ltc2983.h"

#include <Arduino.h>
#include <ArduinoSTL.h>
#include <SPI.h>


constexpr auto ChipSelect_ADC = 10;
String recievedString;

constexpr auto VDD_CHX = A0;
constexpr auto VDD_CHY = A5;
constexpr auto VDD_CHZ = A10;

constexpr auto M_CHX = A1;
constexpr auto M_CHY = A6;
constexpr auto M_CHZ = A11;

constexpr auto V_BIAS_LNA_CHX = A2;
constexpr auto V_BIAS_LNA_CHY = A7;
constexpr auto V_BIAS_LNA_CHZ = A12;

constexpr auto S_CHX = A3;
constexpr auto S_CHY = A8;
constexpr auto S_CHZ = A13;

constexpr auto RTN_CHX = A4;
constexpr auto RTN_CHY = A9;
constexpr auto RTN_CHZ = A14;

constexpr auto Enable_alim_X = 11;
constexpr auto Enable_alim_Y = 12;
constexpr auto Enable_alim_Z = 13;

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

uint16_t communicateADC(int ch)
{
    uint16_t adcValue = 0;
    digitalWrite(ChipSelect_ADC, LOW);                                              // write the ChipSelect_ADC pin low to initiate ADC sample and data transmit
    if (ch == 0)
    {
        SPI.transfer16(0b1111101110010000);
        digitalWrite(ChipSelect_ADC, HIGH);
        digitalWrite(ChipSelect_ADC, LOW);

    }


    adcValue = SPI.transfer16(0) & 0b0000111111111111;                      //read the value sent in 16b an derase the 4 MSB identifying the chanel

    digitalWrite(ChipSelect_ADC, HIGH);
    return adcValue;

}

void setup()
{
  //pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(2000000);
  delay(1000);

  pinMode(ChipSelect_ADC, OUTPUT);                                          // initalize the  data ready and chip select pins:
  digitalWrite(ChipSelect_ADC, HIGH);                                       //For the ADC, High is disable

  SPI.begin();
  SPI.setClockDivider(SPI_CLOCK_DIV2);                                      //SPI Communication frequency at 8MHz (16MHz/2) ==> Checked & OK
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE2);                                               //For AD7490BRUZ CLK default is at 1, Get data at falling edge, Send at Rising

  digitalWrite(ChipSelect_ADC, LOW);                                        // take the SS pin low to select the chip:
  SPI.transfer16(0b1011101100000000);                                       //send the AD7490 Control register ==> Checked & OK
  //delay(100);
  digitalWrite(ChipSelect_ADC, HIGH);                                       // take the SS pin high to de-select the chip

  digitalWrite(Enable_alim_X, LOW);
  digitalWrite(Enable_alim_Y, LOW);
  digitalWrite(Enable_alim_Z, LOW);

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
  std::cout << "VDD_CHX\t"
            << "M_CHX\t"
            << "V_BIAS_LNA_CHX\t"
            << "RTN_CHX\t"
            << "S_CHX\t"
            << "VDD_CHY\t"
            << "M_CHY\t"
            << "V_BIAS_LNA_CHY\t"
            << "S_CHY\t"
            << "RTN_CHY\t"
            << "VDD_CHZ\t"
            << "M_CHZ\t"
            << "V_BIAS_LNA_CHZ\t"
            << "RTN_CHZ\t"
            << "S_CHZ\t"
            << "ADC00_VDD_CHX\t"
            << "ADC01_M_CHX\t"
            << "ADC02_V_BIAS_LNA_CHX\t"
            << "ADC03_RTN_CHX\t"
            << "ADC04_S_CHX\t"
            << "ADC05_VDD_CHY\t"
            << "ADC06_M_CHY\t"
            << "ADC07_V_BIAS_LNA_CHY\t"
            << "ADC08_RTN_CHY\t"
            << "ADC09_S_CHX\t"
            << "ADC10_VDD_CHZ\t"
            << "ADC11_M_CHZ\t"
            << "ADC12_V_BIAS_LNA_CHZ\t"
            << "ADC13_RTN_CHZ\t"
            << "ADC14_S_CHX\t"
            << "FrameNumber" << std::endl;
}

void loop()
{

  //digitalWrite(LED_BUILTIN, HIGH);

  if(Serial.available())
  {
      recievedString = Serial.readStringUntil('\n');

      if(recievedString.equals("Enable alims"))
      {
          digitalWrite(Enable_alim_X, HIGH);
          digitalWrite(Enable_alim_Y, HIGH);
          digitalWrite(Enable_alim_Z, HIGH);
      }
      if(recievedString.equals("Disable alims"))
      {
          digitalWrite(Enable_alim_X, LOW);
          digitalWrite(Enable_alim_Y, LOW);
          digitalWrite(Enable_alim_Z, LOW);
      }

      if(recievedString.equals("Enable alim X")){digitalWrite(Enable_alim_X, HIGH);}
      if(recievedString.equals("Disable alim X")){digitalWrite(Enable_alim_X, LOW);}

      if(recievedString.equals("Enable alim Y")){digitalWrite(Enable_alim_X, HIGH);}
      if(recievedString.equals("Disable alim Y")){digitalWrite(Enable_alim_X, LOW);}

      if(recievedString.equals("Enable alim Z")){digitalWrite(Enable_alim_X, HIGH);}
      if(recievedString.equals("Disable alim Z")){digitalWrite(Enable_alim_X, LOW);}
  }

  for(auto i : {VDD_CHX, M_CHX, V_BIAS_LNA_CHX, RTN_CHX, S_CHX,
                VDD_CHY, M_CHY, V_BIAS_LNA_CHY, RTN_CHY, S_CHY,
                VDD_CHZ, M_CHZ, V_BIAS_LNA_CHZ, RTN_CHZ, S_CHZ})
  {
    int sensorValue = analogRead(i);                                        //Checkt he corresponding pin
    std::cout << sensorValue << "\t";
  }



   int testAdcConv = 0;

  for(auto i : {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14})
  {
    uint16_t adcValue = communicateADC(i);             //read the value sent in 16b
    if (i == adcValue >> 12) {testAdcConv++;}                               //to check the ADC channel (sent on the first 3 bits)
    std::cout << adcValue << "\t";
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
//digitalWrite(LED_BUILTIN, LOW);
  delay(1);
}
