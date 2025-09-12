# Makefile
# Cocotb + Verilog testbench

# Simulator and language
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Source directory
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES = tt_um_axi4lite_top.v axi4lite_master.v axi4lite_slave.v

ifneq ($(GATES),yes)

# ---------------- RTL simulation ----------------
SIM_BUILD        = sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

else

# ---------------- Gate Level simulation ----------------
SIM_BUILD        = sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DUSE_POWER_PINS
COMPILE_ARGS    += -DSIM
COMPILE_ARGS    += -DUNIT_DELAY=\#1

# Sky130 primitives + standard cells
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v

# GDS workflow netlist (injected later)
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Common include path
COMPILE_ARGS += -I$(SRC_DIR)

# Include the Verilog testbench wrapper
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = axi4lite_tb

# Python test module
MODULE = test

# Resolve X/Z automatically → ZERO
export COCOTB_RESOLVE_X = ZERO

# Include cocotb make rules
include $(shell cocotb-config --makefiles)/Makefile.sim
