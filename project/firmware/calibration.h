#ifndef BUCK_CALIBRATION_H
#define BUCK_CALIBRATION_H
/* Replace using TWO measured (ADC count, DMM output volts) pairs.
 * These nominal values are NOT laboratory calibration evidence. */
#define BUCK_ADC_VOLTS_PER_COUNT (3.3f * 4.0f / 4095.0f)
#define BUCK_ADC_OFFSET_VOLTS 0.0f
#endif
