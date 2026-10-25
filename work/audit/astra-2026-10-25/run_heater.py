#!/usr/bin/env python3
import pathlib, subprocess, tempfile
here=pathlib.Path(__file__).resolve().parent
repo=here.parents[2]
gt=repo/'test/googletest/googletest'
build=pathlib.Path(tempfile.mkdtemp(prefix='wb_r6_heater_'))
cmd=['g++','-std=c++20','-g','-O1','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DMOCK_TIMER','-DWB_PROD=0']
cmd += ['-I'+str(p) for p in [repo/'test',repo/'firmware',repo/'firmware/boards',repo/'firmware/util',repo/'firmware/libfirmware/util/include',gt/'include',gt]]
cmd += [str(p) for p in [here/'heater_recovery.cpp',repo/'firmware/heater_control.cpp',repo/'firmware/pid.cpp',repo/'firmware/util/timer.cpp',repo/'test/test_stubs.cpp',gt/'src/gtest-all.cc',gt/'src/gtest_main.cc']]
cmd += ['-lpthread','-o',str(build/'heater')]
subprocess.run(cmd,check=True)
subprocess.run([str(build/'heater'),'--gtest_filter=HeaterUpdate.Audit*'],check=True)
