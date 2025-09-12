import os
os.environ["COCOTB_RESOLVE_X"] = "zero"

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def wait_done(dut, max_cycles=2000):
    """Wait for uo_out[0] (done) to assert, with timeout"""
    for i in range(max_cycles):
        val = int(dut.uo_out.value) & 0x1
        if val:
            dut._log.info(f"DONE detected at cycle {i} ✅")
            return True
        await RisingEdge(dut.clk)
    dut._log.error("Timeout waiting for DONE ❌")
    return False


async def axi_write(dut, addr, data):
    """Drive ui_in/uio_in to perform a write"""
    dut.ui_in.value = (addr & 0x3) << 1  # bits [2:1] = addr
    dut.ui_in.value |= 0x1               # bit 0 = start_write
    dut.uio_in.value = data & 0xFF
    await RisingEdge(dut.clk)
    dut.ui_in.value &= ~0x1               # deassert start_write
    return await wait_done(dut)


async def axi_read(dut, addr):
    """Drive ui_in to perform a read"""
    dut.ui_in.value = (addr & 0x3) << 3  # bits [4:3] = addr
    dut.ui_in.value |= 1 << 5            # bit 5 = start_read
    await RisingEdge(dut.clk)
    dut.ui_in.value &= ~(1 << 5)         # deassert start_read
    ok = await wait_done(dut)
    if ok:
        return int(dut.uio_out.value) & 0xFF
    return None


@cocotb.test()
async def axi4lite_ui_smoke(dut):
    """GL-safe test using packed ui_in/uio_in interface"""

    # Clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut._log.info("Clock started ✅")

    # Reset
    dut.rst_n.value = 0
    dut.ena.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    dut.ena.value = 1
    await RisingEdge(dut.clk)
    dut._log.info("Reset released ✅")

    # ---------------- WRITE ----------------
    write_addr = 0x1
    write_data = 0x04
    dut._log.info(f"WRITE: Addr={write_addr} Data=0x{write_data:02X}")
    ok = await axi_write(dut, write_addr, write_data)
    if not ok:
        dut._log.error("WRITE failed ❌")
        return

    # ---------------- READ ----------------
    await Timer(20, units="ns")
    read_data = await axi_read(dut, write_addr)
    if read_data is None:
        dut._log.error("READ failed ❌")
        return
    dut._log.info(f"READ: Addr={write_addr} Data=0x{read_data:02X}")

    # ---------------- CHECK ----------------
    if read_data == write_data:
        dut._log.info("TEST PASSED ✅")
    else:
        dut._log.error(f"TEST FAILED ❌ Expected 0x{write_data:02X}, Got 0x{read_data:02X}")
