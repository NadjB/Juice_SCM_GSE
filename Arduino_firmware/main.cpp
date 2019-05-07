#include "ina226.h"

#include <Arduino.h>
#include <ArduinoSTL.h>

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

static Ina226<500000, 50> currentMonitor{};

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(2000000);
  delay(1000);
  for(auto ina : {INA_CHX, INA_CHY, INA_CHZ})
  {
    currentMonitor.setup(ina, INA226::OperatingMode::BothVoltageContinuous,
                         INA226::ConvTime::cnv_140us,
                         INA226::ConvTime::cnv_140us, INA226::AvgNum::avg_16);
  }

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
            << "V_CHZ\t" << std::endl;
}

void loop()
{
  digitalWrite(LED_BUILTIN, HIGH);
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
  std::cout << std::endl;
  digitalWrite(LED_BUILTIN, LOW);
  delay(1);
}
