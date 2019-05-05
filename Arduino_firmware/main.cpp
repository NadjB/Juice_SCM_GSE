#include <Arduino.h>
#include <ArduinoSTL.h>
#include <INA.h>

INA_Class INA;

constexpr auto V_BIAS_LNA_CHX = A6;
constexpr auto V_BIAS_LNA_CHY = A3;
constexpr auto V_BIAS_LNA_CHZ = A0;

constexpr auto M_CHX = A7;
constexpr auto M_CHY = A4;
constexpr auto M_CHZ = A1;

constexpr auto VDD_CHX = A8;
constexpr auto VDD_CHY = A5;
constexpr auto VDD_CHZ = A2;

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(2000000);
  auto devicesFound = INA.begin(1, static_cast<uint32_t>(500 * 1000));
  INA.setBusConversion(8500);
  INA.setShuntConversion(8500);
  INA.setAveraging(128);
  INA.setMode(INA_MODE_CONTINUOUS_BOTH);
  std::cout << "found " << static_cast<int>(devicesFound) << std::endl;
}

void loop()
{
  for(auto i : {V_BIAS_LNA_CHX, V_BIAS_LNA_CHY, V_BIAS_LNA_CHZ, M_CHX, M_CHY,
                M_CHZ, VDD_CHX, VDD_CHY, VDD_CHZ})
  {
    int sensorValue = analogRead(i);
    std::cout << sensorValue << "\t";
  }
  for(uint8_t i = 0; i < 3; i++)
  {
    std::cout << INA.getBusMicroAmps(i) << "\t";
  }
  for(uint8_t i = 0; i < 3; i++)
  {
    std::cout << INA.getBusMilliVolts(i) << "\t";
  }
  std::cout << std::endl;
  delay(1);
}
