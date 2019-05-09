#include <Arduino.h>
#include <ArduinoSTL.h>
#include <Wire.h>

constexpr uint8_t INA226_CONFIGURATION_REGISTER =
    0; ///< Configuration Register address
constexpr uint8_t INA226_SHUNT_VOLTAGE_REGISTER =
    1; ///< INA226 Shunt Voltage Register
constexpr uint8_t INA226_BUS_VOLTAGE_REGISTER =
    2;                                         ///< Bus Voltage Register address
constexpr uint8_t INA226_POWER_REGISTER   = 3; ///< Power Register address
constexpr uint8_t INA226_CURRENT_REGISTER = 4; ///< INA226 Current Register
constexpr uint8_t INA226_CALIBRATION_REGISTER =
    5; ///< Calibration Register address
constexpr uint8_t INA226_MASK_ENABLE_REGISTER =
    6; ///< Mask enable Register address (not on all devices)
constexpr uint8_t INA226_ALERT_LIMIT_REGISTER =
    7; ///< Alert Limit Register address (not on all devices)
constexpr uint8_t INA226_MANUFACTURER_ID_REGISTER =
    0xFE; ///< Manuf. ID Register address (not on all devices)
constexpr uint8_t INA226_DIE_ID_REGISTER =
    0xFF; ///< Die ID Register address (not on all devices)

namespace INA226
{
  enum class OperatingMode : uint16_t
  {
    PowerDown              = 0,
    ShuntVoltageTrig       = 1,
    BusVoltageTrig         = 2,
    BothTrig               = 3,
    PowerDown1             = 4,
    ShuntVoltageContinuous = 5,
    BusVoltageContinuous   = 6,
    BothContinuous         = 7
  };

  enum class ConvTime : uint16_t
  {
    cnv_140us  = 0,
    cnv_204us  = 1,
    cnv_332us  = 2,
    cnv_588us  = 3,
    cnv_1100us = 4,
    cnv_2116us = 5,
    cnv_4156us = 6,
    cnv_8244us = 7
  };

  enum class AvgNum : uint16_t
  {
    avg_1    = 0,
    avg_4    = 1,
    avg_16   = 2,
    avg_64   = 3,
    avg_128  = 4,
    avg_256  = 5,
    avg_512  = 6,
    avg_1024 = 7
  };
} // namespace INA226

template<uint64_t shuntMicroOhms, uint64_t maxCurrentMiliAmps> class Ina226
{
  static constexpr auto _currentLSBnano = maxCurrentMiliAmps * 1000000 / 32768;
  static constexpr auto _calibration =
      5120000000000 / (_currentLSBnano * shuntMicroOhms);

public:
  Ina226() {}

  void setup(uint8_t deviceAddress, const INA226::OperatingMode mode,
             const INA226::ConvTime shuntVoltageConvTime,
             const INA226::ConvTime busVoltageConvTime,
             const INA226::AvgNum avg) const
  {
    Wire.begin();
    writeWord(deviceAddress, INA226_CONFIGURATION_REGISTER,
              static_cast<uint16_t>(1) << 15); // reset dev
    delay(10);
    writeWord(deviceAddress, INA226_CALIBRATION_REGISTER,
              static_cast<uint16_t>(_calibration));
    uint16_t confi_reg =
        static_cast<const uint16_t>(mode) +
        (static_cast<const uint16_t>(shuntVoltageConvTime) << 3) +
        (static_cast<const uint16_t>(busVoltageConvTime) << 6) +
        (static_cast<const uint16_t>(avg) << 9);
    writeWord(deviceAddress, INA226_CONFIGURATION_REGISTER, confi_reg);
  }

  int32_t microAmps(const uint8_t deviceAddress) const
  {
    auto currentReg =
        static_cast<int16_t>(readWord(deviceAddress, INA226_CURRENT_REGISTER));
    return (static_cast<int64_t>(currentReg) *
            static_cast<int64_t>(_currentLSBnano)) /
           1000;
    return currentReg;
    return (static_cast<uint32_t>(currentReg) * 1525);
  }

  uint16_t milliVolts(const uint8_t deviceAddress) const

  {
    auto voltageReg = static_cast<uint32_t>(
        readWord(deviceAddress, INA226_BUS_VOLTAGE_REGISTER));
    return static_cast<uint16_t>((voltageReg * 125) / 100);
  }

private:
  uint16_t readWord(uint8_t deviceAddress, const uint8_t addr)
  {
    Wire.beginTransmission(deviceAddress); // Address the I2C device
    Wire.write(addr);                      // Send register address to read
    Wire.endTransmission();                // Close transmission
    delayMicroseconds(10);                 // delay required for sync
    Wire.requestFrom(deviceAddress,
                     static_cast<uint8_t>(2)); // Request 2 consecutive bytes
    uint16_t returnData = static_cast<uint16_t>(Wire.read()); // Read the msb
    returnData          = returnData << 8; // shift the data over 8 bits
    returnData |= static_cast<uint16_t>(Wire.read()); // Read the lsb
    return returnData;
  }

  void writeWord(uint8_t deviceAddress, const uint8_t addr, const uint16_t data)
  {
    Wire.beginTransmission(deviceAddress); // Address the I2C device
    Wire.write(addr);                      // Send register address to write
    Wire.write(static_cast<uint8_t>(data >> 8)); // Write the first (MSB) byte
    Wire.write(static_cast<uint8_t>(data));      // and then the second
    Wire.endTransmission(); // Close transmission and actually send data
    delayMicroseconds(10);  // delay required for sync
  }
};
