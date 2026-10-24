# Host tests for the 0-5 V analog output: production auxout.cpp, pump_dac.cpp and can_helper.cpp with the real
# f0_module board config and fake ChibiOS headers (shim/). Separate from ../Makefile because they need the f0 config,
# which the upstream suite replaces with its own test/wideband_board_config.h.
#
#   make BUILDDIR=/absolute/dir && /absolute/dir/aux_out_test
#   make BUILDDIR=/absolute/dir AUXOUT_SRC=/path/to/other/auxout.cpp   # run the same tests against another version

FW := $(abspath ../../firmware)
GT := $(abspath ../googletest/googletest)
BUILDDIR ?= build
AUXOUT_SRC ?= $(FW)/auxout.cpp
CAN_SRC ?= $(FW)/can.cpp
CAN_HELPER_SRC ?= $(FW)/can_helper.cpp
CXX ?= g++
EXTRA ?=

CXXFLAGS = -std=c++17 -g -O1 -Wall -Wextra -Wno-unused-parameter -Wno-missing-field-initializers \
	-fsanitize=address,undefined -fno-omit-frame-pointer -DMOCK_TIMER -DWB_PROD=0 $(EXTRA) \
	-I$(CURDIR) -I$(CURDIR)/shim -I$(FW)/boards/f0_module -I$(FW)/boards/f0_module/io -I$(FW)/boards -I$(FW) \
	-I$(FW)/util -I$(FW)/libfirmware/util/include -I$(GT)/include -I$(GT)

SRC = test_aux_out.cpp fakes.cpp $(AUXOUT_SRC) $(FW)/pump_dac.cpp $(CAN_HELPER_SRC) $(CAN_SRC) \
	$(FW)/libfirmware/util/src/math.cpp $(GT)/src/gtest-all.cc $(GT)/src/gtest_main.cc

$(BUILDDIR)/aux_out_test: $(SRC) $(wildcard shim/*.h) fakes.h
	mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(SRC) -o $@ -lpthread

.PHONY: run
run: $(BUILDDIR)/aux_out_test
	ASAN_OPTIONS=detect_stack_use_after_return=1 $<
