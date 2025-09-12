# cocotb_tb_axi4lite.py
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

async def wait_done(dut, max_cycles=2000):
    """Wait for uo_out[0] (done) to assert, with timeout"""
    for i in range(max_cycles):
        val = int(dut.uo_out.value) & 0x1  # safe read
        if val:
            dut._log.info(f"DONE detected at cycle {i} ✅")
            return True
        await RisingEdge(dut.clk)
    dut._log.error("Timeout waiting for DONE ❌")
    return False

@cocotb.test()
async def axi4lite_master_slave_test(dut):
    """
    Cocotb test for tt_um_axi4lite_top
    - Writes data to address 1
    - Reads back data from address 1
    """

    # ---------------- INITIALIZE ----------------
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    # Start clock: 100 MHz
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    await Timer(20, units="ns")
    dut.rst_n.value = 1

    # Wait a few cycles for signals to settle after reset
    for _ in range(5):
        await RisingEdge(dut.clk)

    # ---------------- WRITE ----------------
    write_addr = 0x1
    write_data = 0x4

    dut.ui_in.value = 0
    dut.ui_in.value |= (write_addr << 1)  # bits 2:1 = write_addr
    dut.ui_in.value |= 0x1                 # bit 0 = start_write
    dut.uio_in.value = write_data

    await RisingEdge(dut.clk)
    dut.ui_in.value &= ~0x1  # deassert start_write

    # Wait for done safely
    ok = await wait_done(dut)
    if not ok:
        return

    cocotb.log.info(f"WRITE: Addr=0x{write_addr:X} Data=0x{write_data:X}")

    # Small settle delay
    await Timer(20, units="ns")

    # ---------------- READ ----------------
    read_addr = 0x1

    dut.ui_in.value = 0
    dut.ui_in.value |= (read_addr << 3)  # bits 4:3 = read_addr
    dut.ui_in.value |= 0x20               # bit 5 = start_read

    await RisingEdge(dut.clk)
    dut.ui_in.value &= ~0x20  # deassert start_read

    # Wait for done safely
    ok = await wait_done(dut)
    if not ok:
        return

    # Safe read of output
    read_data = int(dut.uio_out.value) & 0xFF
    cocotb.log.info(f"READ: Addr=0x{read_addr:X} Data=0x{read_data:X}")

    # ---------------- CHECK ----------------
    if read_data == write_data:
        cocotb.log.info("TEST PASSED ✅")
    else:
        cocotb.log.error(f"TEST FAILED ❌ Expected 0x{write_data:X}, Got 0x{read_data:X}")
