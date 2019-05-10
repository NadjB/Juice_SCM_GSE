#include <stdint.h>
#include <vector>

namespace
{
  template<class T, T v> struct integral_constant
  {
    static constexpr T value = v;
    typedef T value_type;
    typedef integral_constant type;
    constexpr operator value_type() const noexcept { return value; }
    constexpr value_type operator()() const noexcept { return value; }
  };

  using false_type = integral_constant<bool, false>;
  using true_type  = integral_constant<bool, true>;

  template<class T, class U> struct is_same : false_type
  {};

  template<class T> struct is_same<T, T> : true_type
  {};
} // namespace

namespace LTC2983
{
  enum class SensorType : uint8_t
  {
    Unassigned,
    J_Thermocouple,
    K_Thermocouple,
    E_Thermocouple,
    N_Thermocouple,
    R_Thermocouple,
    S_Thermocouple,
    T_Thermocouple,
    B_Thermocouple,
    Custom_Thermocouple,
    PT_10,
    PT_50,
    PT_100,
    PT_200,
    PT_500,
    PT_1000,
    PT_1000_00375,
    RTD_NI_120,
    RTD_Custom,
    Thermistor_44004_44033,
    Thermistor_44005_44030,
    Thermistor_44007_44034,
    Thermistor_44006_44031,
    Thermistor_44008_44032,
    Thermistor_YSI_400,
    Thermistor_Spectrum_1003k,
    Thermistor_Custom_Steinhart_Hart,
    Thermistor_Custom_Table,
    Diode,
    Sense_Resistor,
    Direct_ADC,
    Reserved
  };

  enum class Channel : uint8_t
  {
    Multiple = 0,
    CH1      = 0x1,
    CH2      = 0x2,
    CH3      = 0x3,
    CH4      = 0x4,
    CH5      = 0x5,
    CH6      = 0x6,
    CH7      = 0x7,
    CH8      = 0x8,
    CH9      = 0x9,
    CH10     = 0xA,
    CH11     = 0xB,
    CH12     = 0xC,
    CH13     = 0xD,
    CH14     = 0xE,
    CH15     = 0xF,
    CH16     = 0x10,
    CH17     = 0x11,
    CH18     = 0x12,
    CH19     = 0x13,
    CH20     = 0x14
  };

  enum class MeasurementMode : uint8_t
  {
    TwoWires        = 0,
    ThreeWires      = 1,
    FourWires       = 2,
    FourWiresKelvin = 3
  };

  enum class ExcitationMode : uint8_t
  {
    GroundExternal = 0,
    GroundInternal = 1
  };

  enum class ExcitationCurrent : uint8_t
  {
    Cur5uA   = 1,
    Cur10uA  = 2,
    Cur25uA  = 3,
    Cur50uA  = 4,
    Cur100uA = 5,
    Cur250uA = 6,
    Cur500uA = 7,
    Cur100mA = 8
  };

  enum class RTDCurve : uint8_t
  {
    EuropeanStandard = 0,
    American         = 1,
    Japanese         = 2,
    ITS_90           = 3,
    RTD_1000_375     = 0,
    NI_120           = 0
  };

} // namespace LTC2983

template<typename SPIDev_t> class Ltc2983
{
  const SPIDev_t _spi;

  template<uint8_t CMD, typename T>
  T transaction(const uint16_t address, const T data)
  {
    T result = 0;
    _spi.select(true);
    _spi.write(CMD);
    _spi.write(address);
    if constexpr(is_same<T, uint16_t>::value or is_same<T, uint8_t>::value)
    { result = _spi.write(static_cast<T>(data)); }
    else if constexpr(is_same<T, uint32_t>::value)
    {
      result = _spi.write(static_cast<uint16_t>(data >> 16)) << 16;
      result += _spi.write(static_cast<uint16_t>(data));
    }
    _spi.select(false);
    return result;
  }

  template<typename T> void writMem(const uint16_t address, const T data) const
  {
    transaction<0x2>(address, data);
  }

  template<typename T> T readMem(const uint16_t address) const
  {
    return transaction<0x3>(address, static_cast<T>(0x0));
  }

  template<uint16_t base_addr>
  uint16_t _chan_addr(const LTC2983::Channel channel)
  {
    return (base_addr - 4) + ((static_cast<uint16_t>(channel)) * 4);
  }

  inline uint16_t _chan_cfg_addr(const LTC2983::Channel channel) const
  {
    return _chan_addr<0x200>(channel);
  }

  inline uint16_t _chan_data_addr(const LTC2983::Channel channel) const
  {
    return _chan_addr<0x010>(channel);
  }

public:
  Ltc2983(const SPIDev_t&& spi) : _spi{spi} {}
  inline void setup() { _spi.setup(); }
  inline uint8_t status() { return readMem<uint8_t>(static_cast<uint16_t>(0)); }

  inline void start_Conv(const LTC2983::Channel channel) const
  {
    writMem(0, static_cast<uint8_t>(0x80 | static_cast<uint8_t>(channel)));
  }

  inline uint32_t adc_raw_result(const LTC2983::Channel channel) const
  {
    return readMem<uint32_t>(_chan_data_addr(channel));
  }

  inline double temperature(const LTC2983::Channel channel) const
  {
    auto raw = static_cast<int32_t>(adc_raw_result(channel))<<8;
    return static_cast<double>(raw>>8)/1024.;
  }

  inline void configure_RTD(
      const LTC2983::Channel channel, const LTC2983::SensorType type,
      const LTC2983::Channel rsense, const LTC2983::ExcitationCurrent current,
      const uint32_t rsense_milli_ohms, const LTC2983::MeasurementMode m_mode,
      const LTC2983::ExcitationMode e_mode,
      const LTC2983::RTDCurve curve = LTC2983::RTDCurve::EuropeanStandard) const
  {
    uint32_t config_reg = static_cast<uint32_t>(type) << 27 |
                          static_cast<uint32_t>(rsense) << 22 |
                          static_cast<uint32_t>(m_mode) << 20 |
                          static_cast<uint32_t>(e_mode) << 18 |
                          static_cast<uint32_t>(current) << 14 |
                          static_cast<uint32_t>(curve) << 12;
    writMem(_chan_cfg_addr(channel), config_reg);
    config_reg = static_cast<uint32_t>(LTC2983::SensorType::Sense_Resistor)
                     << 27 |
                 ((rsense_milli_ohms * 1000) / 1024);
    writMem(_chan_cfg_addr(rsense), config_reg);
  }

  inline void
  configure_MultipleConv(std::initializer_list<LTC2983::Channel> channels) const
  {
    uint32_t config_reg = 0;
    for(const auto ch : channels)
    {
      config_reg |= 1 << (static_cast<unsigned int>(ch) - 1);
    }
    writMem(0xf4, config_reg);
  }
};
