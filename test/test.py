import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def wait_done(dut, max_cycles=200):
    """Wait for uo_out[0] (done) or timeout."""
    for i in range(max_cycles):
        if int(dut.uo_out.value) & 0x1:
            dut._log.info(f"DONE detected after {i} cycles ✅")
            return True
        await RisingEdge(dut.clk)
    dut._log.error("Timeout: DONE not seen ❌")
    return False


async def axi_write(dut, addr, data):
    """Perform a write transaction (addr=0..3, data=8-bit)."""
    dut.ui_in.value = (addr & 0x3) << 1  # put addr on ui_in[2:1]
    dut.ui_in.value = dut.ui_in.value | 0x1  # set start_write
    dut.uio_in.value = data & 0xFF
    await RisingEdge(dut.clk)
    dut.ui_in.value = 0  # deassert
    dut._log.info(f"WRITE launched: Addr=0x{addr:X}, Data=0x{data:02X}")
    return await wait_done(dut)


async def axi_read(dut, addr):
    """Perform a read transaction (addr=0..3)."""
    dut.ui_in.value = (addr & 0x3) << 3  # put addr on ui_in[4:3]
    dut.ui_in.value = dut.ui_in.value | (1 << 5)  # set start_read
    await RisingEdge(dut.clk)
    dut.ui_in.value = 0  # deassert
    dut._log.info(f"READ launched: Addr=0x{addr:X}")
    ok = await wait_done(dut)
    if ok:
        data = int(dut.uio_out.value) & 0xFF
        dut._log.info(f"READ got Data=0x{data:02X}")
        return data
    return None


@cocotb.test(timeout_time=5, timeout_unit="us")
async def axi4lite_smoke(dut):
    """Simple AXI4Lite-like write/read test."""

    # Start clock (10 ns period -> 100 MHz)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut._log.info("Clock started ✅")

    # Reset
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    for _ in range(20):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    dut._log.info("Reset released ✅")

    # ---- WRITE ----
    write_addr = 1
    write_data = 0x04
    ok = await axi_write(dut, write_addr, write_data)
    if not ok:
        dut._log.error("WRITE failed ❌")
        return

    # ---- READ ----
    await Timer(50, units="ns")
    read_data = await axi_read(dut, write_addr)
    if read_data is None:
        dut._log.error("READ failed ❌")
        return

    # ---- CHECK ----
    if read_data == write_data:
        dut._log.info("TEST PASSED ✅ (read matches write)")
    else:
        dut._log.error(
            f"TEST FAILED ❌ Expected 0x{write_data:02X}, Got 0x{read_data:02X}"
        )

    await Timer(100, units="ns")
    dut._log.info("Smoke test complete ✅")
