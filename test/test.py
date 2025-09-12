import os
# Resolve any X/Z bits to ZERO before cocotb starts
os.environ["COCOTB_RESOLVE_X"] = "zero"

import cocotb
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut, cycles=5):
    """Reset the DUT"""
    dut._log.info("Applying reset...")
    dut.rst_n.value = 0
    for _ in range(cycles):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    dut._log.info("Reset released")


@cocotb.test()
async def axi4lite_smoke(dut):
    """Simple AXI4Lite write/read test"""

    # Clock generator (10ns period = 100 MHz)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset DUT
    await reset_dut(dut)

    # ---------------- WRITE PHASE ----------------
    write_addr = 0x1
    write_data = 0x04

    dut._log.info(f"WRITE: Addr=0x{write_addr:X} Data=0x{write_data:02X}")
    dut.write_addr.value = write_addr
    dut.write_data.value = write_data
    dut.start_write.value = 1
    await RisingEdge(dut.clk)
    dut.start_write.value = 0

    # Wait for write to settle
    await Timer(20, units="ns")

    # ---------------- READ PHASE ----------------
    dut.read_addr.value = write_addr
    dut.start_read.value = 1
    await RisingEdge(dut.clk)
    dut.start_read.value = 0

    # Wait for read data
    await Timer(20, units="ns")

    # Resolve X/Z → 0 automatically
    read_val = dut.read_data.value.integer

    dut._log.info(f"READ:  Addr=0x{write_addr:X} Data=0x{read_val:02X}")

    # ---------------- CHECK ----------------
    assert read_val == write_data, (
        f"TEST FAILED ❌ : Expected 0x{write_data:02X}, Got 0x{read_val:02X}"
    )

    dut._log.info("TEST PASSED ✅ (read matches write)")
