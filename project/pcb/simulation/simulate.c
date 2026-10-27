/* Switched engineering estimate, not a manufacturer SPICE model or lab data.
 * Models external load, diode drop, MOSFET Rds, L DCR, shunt and capacitor ESR.
 * Invokes the real runtime and PI; ADC quantization and one-period delay included.
 */
#include "../../firmware/runtime.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static BuckRuntime r;
int main(int argc,char **argv)
{
    if(argc!=4) {fprintf(stderr,"usage: simulate CASE DT_SECONDS OUTPUT.csv\n");return 2;}
    const char *name=argv[1];double dt=strtod(argv[2],0);
    unsigned steps=(unsigned)lround(.0001/dt);
    if((steps!=200 && steps!=400) || fabs(steps*dt-.0001)>1e-12) return 2;
    FILE *f=fopen(argv[3],"w");if(!f)return 2;
    fprintf(f,"t_s,vo_V,il_A,vref_V,dprime,load_ohm,mode,hardware_fault\n");
    runtime_init(&r);runtime_start(&r,!strncmp(name,"open",4)?BUCK_OPEN:BUCK_CLOSED,!strncmp(name,"open",4)?.5f:6,false);
    double il=0,vc=0,sensed=0,applied=1,pending=1,previous_period_dp=1,R=6,peak=0;
    const double sensor_decay=exp(-dt/.00000075); /* (3k || 1k) * 1nF */
    bool trip=false;
    for(unsigned k=0;k<8300;k++) {
        if(k==8000) {
            if(!strcmp(name,"open_up"))r.open_dprime=.6f;
            else if(!strcmp(name,"open_down"))r.open_dprime=.4f;
            else if(!strcmp(name,"ref_up"))r.reference=7;
            else if(!strcmp(name,"ref_down"))r.reference=5;
            else if(!strcmp(name,"load_up"))R=7.2;
            else if(!strcmp(name,"load_down"))R=4.8;
            else return 2;
        }
        double vmean=0,imean=0;unsigned adc_sum=0,ns=0;
        for(unsigned j=0;j<steps;j++) {
            const double ESR=.15,L=.00066,C=.000020;
            double vo=(vc+ESR*il)*R/(R+ESR);
            if(il>=2 || vo>=8.2)trip=true;
            /* Typical IR2110 propagation delays: 120ns on, 94ns off.
             * These are estimates; VDD/VBS/load differ from datasheet tests. */
            double on=fmax(0,fmin(1,j+1-(applied+.0012)*steps));
            if(previous_period_dp+.0012<1)on+=fmax(0,fmin(1,.000000094/dt-j));
            if(trip || r.mode==BUCK_OFF || r.mode==BUCK_FAULT) on=0;
            /* Resolve fractional PWM edges, avoiding timestep-sized duty quantization. */
            double di=(on*(12-.022*il)+(1-on)*(-.45)-vo-.25*il)/L;
            double dv=(il-vo/R)/C;
            il=fmax(0,il+dt*di);vc+=dt*dv;
            if(il>peak)peak=il;
            vmean+=vo;imean+=il;
            /* 200kHz sampling; same 0.5us phase as the timer adapter. */
            if(j==steps/200+ns*(steps/20) && ns<20) {
                adc_sum+=(unsigned)fmin(4095,fmax(0,round(sensed/(3.3*4)*4095)));ns++;
            }
            sensed=vo+(sensed-vo)*sensor_decay;
        }
        if(ns!=20)return 3;
        double new_command=runtime_tick(&r,(uint16_t)((adc_sum+10)/20),true,trip);
        if(k>=7900)fprintf(f,"%.7f,%.9f,%.9f,%.3f,%.7f,%.3f,%d,%d\n",(k+1)*.0001-.79,vmean/steps,imean/steps,r.reference,applied,R,r.mode,trip);
        previous_period_dp=applied;applied=pending;pending=new_command;
    }
    fclose(f);
    printf("%s dt=%g peak_IL=%.6f A mode=%d hardware_fault=%d\n",name,dt,peak,r.mode,trip);
    return trip || r.mode==BUCK_FAULT ? 1:0;
}
