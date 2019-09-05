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


void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(2000000);
  delay(1000);
  
  pinMode(CS_ADC, OUTPUT);                                                  // initalize the  data ready and chip select pins:
  digitalWrite(CS_ADC, HIGH);

  SPI.begin();
  SPI.setClockDivider(SPI_CLOCK_DIV2);                                      //SPI Communication frequency at 8MHz (16MHz/2) ==> Checked & OK
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE2);                                               //For AD7490BRUZ CLK default is at 1, Get data at falling edge, Send at Rising

  digitalWrite(CS_ADC, LOW);                                                // take the SS pin low to select the chip:
  SPI.transfer16(0b1011101100000000);                                       //send the AD7490 Control register ==> Checked & OK
  //delay(100);
  digitalWrite(CS_ADC, HIGH);                                               // take the SS pin high to de-select the chip

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
  for(auto i : {V_BIAS_LNA_CHX, V_BIAS_LNA_CHY, V_BIAS_LNA_CHZ,             //for each desired tension
                M_CHX, M_CHY, M_CHZ,
                VDD_CHX, VDD_CHY, VDD_CHZ,
                OUT2_INV_CHX, OUT2_INV_CHY, OUT2_INV_CHZ,
                OUT2_NINV_CHX, OUT2_NINV_CHY, OUT2_NINV_CHZ})
  {
    int sensorValue = analogRead(i);                                        //Checkt he corresponding pin
    std::cout << sensorValue << "\t";
  }


  int testAdcConv = 0;
  digitalWrite(CS_ADC, LOW);                                                // write the CS_ADC pin low to initiate ADC sample and data transmit

  for(auto i : {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15})
  {
    uint16_t adcValue = SPI.transfer16(0);                                  //read the value sent in 16b
    if (i == adcValue >> 12)
    std::cout << adcValue << "\t";

    if (i == adcValue >> 12) {testAdcConv++;}                               //to check the ADC channel (sent on the first 3 bits)
  }
  digitalWrite(CS_ADC, HIGH);                                               // wite LTC CS pin high to stop ADC from transmitting

  std::cout << testAdcConv << std::endl;
  digitalWrite(LED_BUILTIN, LOW);
  delay(1);
}
