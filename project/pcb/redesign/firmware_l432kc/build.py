"""Build review firmware only. Never flashes a connected device."""
from pathlib import Path
import os,subprocess,json,sys
F=Path(__file__).resolve().parent;R=F.parents[3]
O=R/'artifacts/buck_nucleo_update_20261025/firmware_build';O.mkdir(parents=True,exist_ok=True)
tool=Path(os.environ.get('ARM_GCC_BIN',str(Path.home()/'.platformio/packages/toolchain-gccarmnoneeabi/bin')))
gcc=tool/'arm-none-eabi-gcc.exe';assert gcc.is_file(), 'Set ARM_GCC_BIN to Arm GCC bin directory'
incs=[F,F/'vendor/hal/Inc',F/'vendor/cmsis/Include',F/'vendor/device/Include']
flags=['-mcpu=cortex-m4','-mthumb','-mfpu=fpv4-sp-d16','-mfloat-abi=hard','-DSTM32L432xx','-DUSE_HAL_DRIVER','-DBUCK_BOARD_REVIEWED=0','-Os','-g3','-ffunction-sections','-fdata-sections','-fno-common']+['-I'+str(p) for p in incs]
sources=list((F/'vendor/hal/Src').glob('*.c'))+[F/'vendor/device/system_stm32l4xx.c',F/'vendor/device/startup_stm32l432xx.s',F/'main.c',F/'runtime.c',F/'buck_control.c']
records=[]
def run(args):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
 records.append({'command':[str(x) for x in args],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 if p.stdout:print(p.stdout)
 if p.stderr:print(p.stderr,file=sys.stderr)
 if p.returncode:
  (O/'commands.json').write_text(json.dumps(records,indent=2));raise SystemExit(p.returncode)
run([gcc,'--version']);objects=[]
for src in sources:
 obj=O/(src.stem+'.o');objects.append(obj)
 warnings=['-Wall','-Wextra','-Werror'] if src.parent==F else ['-Wall','-Wextra']
 run([gcc,*flags,*warnings,'-std=gnu11','-c',src,'-o',obj])
elf=O/'buck_l432kc_review.elf'
run([gcc,*flags,*objects,'-T',F/'stm32l432kc.ld','-nostartfiles','--specs=nosys.specs','-Wl,--gc-sections,-Map='+str(O/'buck_l432kc_review.map'),'-lm','-o',elf])
run([tool/'arm-none-eabi-size.exe',elf])
run([tool/'arm-none-eabi-objcopy.exe','-O','ihex',elf,O/'buck_l432kc_review.hex'])
run([tool/'arm-none-eabi-objcopy.exe','-O','binary',elf,O/'buck_l432kc_review.bin'])
run([tool/'arm-none-eabi-readelf.exe','-h','-A',elf])
(O/'commands.json').write_text(json.dumps(records,indent=2),encoding='utf8')
print('Built Cortex-M4F review image. Hardware NOT programmed; RUN locked OFF.')
