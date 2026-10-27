#ifndef BUCK_CALIBRATION_H
#define BUCK_CALIBRATION_H
/* Nominal only. Calibrate VREF+ and divider with two measured DMM/count pairs. */
#define BUCK_ADC_VOLTS_PER_COUNT (3.3f * (15.0f + 2.2f) / 2.2f / 4095.0f)
#define BUCK_ADC_OFFSET_VOLTS 0.0f
#endif
