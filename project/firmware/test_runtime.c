#include "runtime.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
static BuckRuntime r;
int main(void)
{
    runtime_init(&r);
    assert(runtime_tick(&r, 0, true, false) == 1);
    assert(!runtime_start(&r, BUCK_OPEN, .9f, false));
    assert(!runtime_start(&r, BUCK_OPEN, .5f, true));
    assert(runtime_start(&r, BUCK_OPEN, .5f, false));
    float last=1;
    for (unsigned i=0;i<6000;i++) {
        float dp=runtime_tick(&r, 1800, true, false);
        assert(dp <= last+1e-6f && dp >= .5f);
        assert(last-dp < .00011f);
        last=dp;
    }
    assert(r.mode==BUCK_OPEN && last==.5f);
    runtime_capture(&r);
    r.open_dprime=.6f;
    runtime_tick(&r,1800,true,false);
    runtime_tick(&r,1800,true,false);
    runtime_tick(&r,1800,true,false);
    assert(r.samples[0].dprime_10000==5000 && r.samples[1].dprime_10000==5000);
    assert(r.samples[2].dprime_10000==6000);
    r.capture=false;
    assert(runtime_capture(&r) && !runtime_capture(&r));
    for (unsigned i=0;i<600;i++) runtime_tick(&r,1800,true,false);
    assert(r.count==512 && !r.capture);
    assert(r.samples[511].tick-r.samples[0].tick==511);
    assert(runtime_tick(&r,1800,false,false)==1 && r.mode==BUCK_FAULT);
    assert(!runtime_start(&r,BUCK_CLOSED,6,false));
    assert(runtime_tick(&r,1800,true,false)==1);
    runtime_stop(&r);
    assert(runtime_start(&r,BUCK_CLOSED,6,false));
    for(unsigned i=0;i<13000;i++) runtime_tick(&r,0,true,false);
    assert(r.mode==BUCK_FAULT);
    runtime_stop(&r);
    assert(runtime_start(&r,BUCK_CLOSED,6,false));
    assert(runtime_tick(&r,4095,true,false)==1 && r.mode==BUCK_FAULT);
    runtime_stop(&r);
    r.adc_offset=NAN;
    assert(!runtime_start(&r,BUCK_CLOSED,6,false));
    runtime_tick(&r,0,true,false);
    assert(r.mode==BUCK_FAULT);
    puts("PASS: start interlocks, ramp, applied-command capture timing, buffer bounds, stale ADC, fault latch, startup timeout, invalid calibration");
}
