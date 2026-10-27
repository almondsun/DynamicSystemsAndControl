/* Host test for the L432 runtime (no HAL). Build and run:
 * gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -g \
 *     runtime.c buck_control.c test_runtime_host.c -lm -o test_runtime_host && ./test_runtime_host
 */
#include "runtime.h"
#include "calibration.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>

static BuckRuntime r;

static uint16_t counts(float volts)
{
    return (uint16_t)(volts / BUCK_ADC_VOLTS_PER_COUNT + .5f);
}

static void enter_closed(float reference)
{
    runtime_init(&r);
    assert(runtime_start(&r, BUCK_CLOSED, reference, false));
    (void)runtime_tick(&r, counts(reference), true, false);
    assert(r.mode == BUCK_CLOSED);
}

static void test_rev_b_scale(void)
{
    /* R14 15k, R15 2.2k, R20 1k, TMUX1511 RON 2 ohm, R21 100k; VDDA 3.3 V, 4095 counts. */
    const double rth = 15e3 * 2.2e3 / 17.2e3;
    const double gain = 2.2 / 17.2 * 100e3 / (100e3 + 1e3 + 2 + rth);
    assert(fabs(BUCK_ADC_VOLTS_PER_COUNT - 3.3 / 4095 / gain) < 1e-7);
}

static void test_collapse_trips_after_2ms(void)
{
    enter_closed(6);
    for (int i = 0; i < 20; ++i) (void)runtime_tick(&r, counts(2), true, false);
    assert(r.mode == BUCK_CLOSED);
    assert(runtime_tick(&r, counts(2), true, false) == 1);
    assert(r.mode == BUCK_FAULT);
}

static void test_short_dip_does_not_trip(void)
{
    enter_closed(7);
    for (int round = 0; round < 3; ++round) {
        for (int i = 0; i < 20; ++i) (void)runtime_tick(&r, counts(3), true, false);
        (void)runtime_tick(&r, counts(7), true, false);
    }
    assert(r.mode == BUCK_CLOSED);
}

int main(void)
{
    test_rev_b_scale();
    test_collapse_trips_after_2ms();
    test_short_dip_does_not_trip();
    puts("runtime host tests passed");
    return 0;
}
