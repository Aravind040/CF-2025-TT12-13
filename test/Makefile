# Makefile for Cocotb-based simulation

# Simulator: choose icarus (default) or verilator
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Source directory
SRC_DIR = $(PWD)/../src

# Project sources (RTL)
PROJECT_SOURCES = \
    tt_um_axi4lite_top.v \
    axi4lite_master.v \
    axi4lite_slave.v

ifneq ($(GATES),yes)

# ---------------- RTL Simulation ----------------
SIM_BUILD        = sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

else

# ---------------- Gate-Level Simulation (GLS) ----------------
SIM_BUILD        = sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DUSE_POWER_PINS
COMPILE_ARGS    += -DSIM
COMPILE_ARGS    += -DUNIT_DELAY=\#1

VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v

# Gate-level netlist (inserted by CI workflow after synthesis)
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Allow shared include paths
COMPILE_ARGS += -I$(SRC_DIR)

# ---------------- Top and Python test ----------------
TOPLEVEL = tt_um_axi4lite_top
MODULE   = test 

# ---------------- Cocotb include ----------------
include $(shell cocotb-config --makefiles)/Makefile.sim
