#include "buck_control.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>

int main(void)
{
    BuckControl c;
    buck_reset(&c);
    assert(fabsf(buck_update(&c, 6, 6, true)-0.5f)<1e-6f);
    assert(buck_update(&c, 6, 7, true)<0.5f); /* Correct inverted sign. */
    buck_reset(&c);
    assert(buck_update(&c, 6, 5, true)>0.5f);
    buck_reset(&c);
    for (int k=0; k<10000; ++k) {
        float out = buck_update(&c, 0, 7, true);
        assert(out >= 0.04999f && out <= 0.95001f);
    }
    assert(c.integral < 0.6f); /* Saturation must not accumulate indefinitely. */
    float prior = c.integral;
    buck_update(&c, 7, 6, true);
    assert(c.integral < prior); /* Must unwind after error changes sign. */
    assert(buck_update(&c, NAN, 6, true)==1.0f && c.fault);
    assert(buck_update(&c, 6, 6, true)==1.0f); /* Fault latch. */
    buck_reset(&c);
    assert(buck_update(&c, 8.6f, 6, true)==1.0f && c.fault);
    buck_reset(&c);
    assert(buck_update(&c, 6, 6, false)==1.0f && !c.fault);
    assert(buck_update(NULL, 6, 6, true)==1.0f);
    puts("PASS: polarity, bounds, anti-windup, recovery, disabled state and fault latch");
    return 0;
}
