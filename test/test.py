import os
# Treat all unknown X/Z as 0
os.environ["COCOTB_RESOLVE_X"] = "ZERO"

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def axi4lite_basic_test(dut):
    """AXI4-Lite basic test with X handling"""

    # Start a clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1

    # Wait a few cycles for all signals to settle
    for _ in range(3):
        await RisingEdge(dut.clk)

    # Example write/read sequence
    dut.start_write.value = 1
    dut.write_addr.value = 0
    await RisingEdge(dut.clk)
    dut.start_write.value = 0

    await RisingEdge(dut.clk)

    dut.start_read.value = 1
    dut.read_addr.value = 0
    await RisingEdge(dut.clk)
    dut.start_read.value = 0

    # Wait a few more cycles for outputs to settle
    for _ in range(2):
        await RisingEdge(dut.clk)

    # Read outputs safely
    uo_val = int(dut.uo_out.value)
    uio_val = int(dut.uio_out.value)

    cocotb.log.info(f"uo_out={uo_val}, uio_out={uio_val}")

    # You can add assertions here
    # assert uo_val == expected_value
    # assert uio_val == expected_value
