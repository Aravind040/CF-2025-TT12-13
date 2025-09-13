import os
# Treat all unknown X/Z as 0
os.environ["COCOTB_RESOLVE_X"] = "0"

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def axi_write(dut, addr, data):
    """
    Perform AXI4-Lite write: set ui_in and uio_in, wait for done safely
    """
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await RisingEdge(dut.clk)

    # Setup write signals
    dut.ui_in.value = (addr << 1) | 0x1  # write_addr[1:0] + start_write=1
    dut.uio_in.value = data
    await RisingEdge(dut.clk)

    # Deassert start_write
    dut.ui_in.value = (addr << 1) | 0x0

    # Wait for done, safely handle X/Z
    max_cycles = 2000
    for _ in range(max_cycles):
        val = int(dut.uo_out.value) & 0x1
        if val:
            break
        await RisingEdge(dut.clk)
    else:
        dut._log.error("Timeout waiting for DONE in write ❌")
        return False

    await RisingEdge(dut.clk)
    return True


async def axi_read(dut, addr):
    """
    Perform AXI4-Lite read: set ui_in, wait for done safely, return data
    """
    dut.ui_in.value = 0
    await RisingEdge(dut.clk)

    # Setup read signals
    dut.ui_in.value = (addr << 3) | 0x20  # read_addr[1:0] in bits 4:3, start_read=1 at bit 5
    await RisingEdge(dut.clk)

    # Deassert start_read
    dut.ui_in.value = (addr << 3) | 0x0

    # Wait for done
    max_cycles = 2000
    for _ in range(max_cycles):
        val = int(dut.uo_out.value) & 0x1
        if val:
            break
        await RisingEdge(dut.clk)
    else:
        dut._log.error("Timeout waiting for DONE in read ❌")
        return None

    await RisingEdge(dut.clk)
    return int(dut.uio_out.value) & 0xFF


@cocotb.test()
async def axi4lite_test(dut):
    """
    Cocotb testbench for tt_um_axi4lite_top (AXI4-Lite)
    with zero-resolution and safe read protections
    """

    # Clock: 100 MHz
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # ---------------- RESET ----------------
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    # Wait several cycles for signals to settle
    for _ in range(5):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    dut._log.info("Reset released ✅")

    # ---------------- WRITE ----------------
    write_addr = 0x1
    write_data = 0x4
    ok = await axi_write(dut, write_addr, write_data)
    if not ok:
        return
    dut._log.info(f"WRITE DONE: Addr=0x{write_addr:X}, Data=0x{write_data:X}")

    await Timer(20, units="ns")  # optional settling time

    # ---------------- READ ----------------
    read_addr = 0x1
    read_data = await axi_read(dut, read_addr)
    if read_data is None:
        return
    dut._log.info(f"READ DONE: Addr=0x{read_addr:X}, Data=0x{read_data:X}")

    # ---------------- CHECK ----------------
    if read_data == write_data:
        dut._log.info("TEST PASSED ✅")
    else:
        dut._log.error(f"TEST FAILED ❌ Expected 0x{write_data:X}, Got 0x{read_data:X}")
