# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# Simulator selection
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Project directory and sources
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES = project.v

ifneq ($(GATES),yes)
# RTL Simulation Section
SIM_BUILD         = sim_build/rtl
VERILOG_SOURCES  += $(addprefix $(SRC_DIR)/, $(PROJECT_SOURCES))
else
# Gate Level Simulation Section
SIM_BUILD         = sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DUSE_POWER_PINS
COMPILE_ARGS    += -DSIM
COMPILE_ARGS    += -DUNIT_DELAY=\#1
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v
endif

# Share configuration between design and testbench via `include`
COMPILE_ARGS     += -I$(SRC_DIR)

# Include testbench source file
VERILOG_SOURCES += $(PWD)/tb.v

# Top-level module for simulation
TOPLEVEL = tb

# Python test module (without .py extension)
MODULE = test

# Include cocotb's make rules for simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
