#ifndef BUCK_CALIBRATION_H
#define BUCK_CALIBRATION_H
/* Nominal only. Calibrate VREF+ and divider with two measured DMM/count pairs.
 * Rev B path: R14 15k / R15 2.2k divider, R20 1k series, TMUX1511 RON (2 ohm typ),
 * R21 100k discharge at the ADC pin: gain = 2.2/17.2 * 100k / (100k + 1k + 2 + R14||R15).
 */
#define BUCK_ADC_R_THEVENIN_K (15.0f * 2.2f / (15.0f + 2.2f))
#define BUCK_ADC_LOAD_FACTOR ((100.0f + 1.0f + 0.002f + BUCK_ADC_R_THEVENIN_K) / 100.0f)
#define BUCK_ADC_VOLTS_PER_COUNT (3.3f * (15.0f + 2.2f) / 2.2f * BUCK_ADC_LOAD_FACTOR / 4095.0f)
#define BUCK_ADC_OFFSET_VOLTS 0.0f
#endif
