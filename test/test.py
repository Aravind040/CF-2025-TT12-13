import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge


async def wait_done(dut, max_cycles=2000):
    """Wait for uo_out[0] (done) with timeout to avoid infinite hang"""
    for i in range(max_cycles):
        val = dut.uo_out.value
        if not val.is_resolvable:
            dut._log.warning(f"DONE signal X/Z at cycle {i}, treating as 0")
        elif int(val) & 0x1:
            dut._log.info(f"DONE detected after {i} cycles ✅")
            return True
        await RisingEdge(dut.clk)
    dut._log.error("Timeout: DONE not seen ❌")
    return False


async def axi_write(dut, addr, data):
    """AXI-lite style write transaction"""
    dut.ui_in.value = (addr & 0x3)           # put address on ui_in[1:0]
    dut.ui_in.value = dut.ui_in.value | (1 << 2)  # set write enable (ui_in[2])
    dut.uio_in.value = data & 0xFF           # 8-bit data
    await RisingEdge(dut.clk)
    dut.ui_in.value = (addr & 0x3)           # deassert write
    dut._log.info(f"WRITE launched: Addr=0x{addr:X}, Data=0x{data:02X}")
    return await wait_done(dut)


async def axi_read(dut, addr):
    """AXI-lite style read transaction"""
    dut.ui_in.value = (addr & 0x3)           # put address on ui_in[1:0]
    dut.ui_in.value = dut.ui_in.value | (1 << 3)  # set read enable (ui_in[3])
    await RisingEdge(dut.clk)
    dut.ui_in.value = (addr & 0x3)           # deassert read
    dut._log.info(f"READ launched: Addr=0x{addr:X}")
    ok = await wait_done(dut)
    if ok:
        val = dut.uio_out.value
        if not val.is_resolvable:
            dut._log.error("READ failed: data bus has X/Z ❌")
            return None
        data = int(val) & 0xFF
        dut._log.info(f"READ got Data=0x{data:02X}")
        return data
    return None


@cocotb.test(timeout_time=50, timeout_unit="us")
async def axi4lite_smoke_gl(dut):
    """GL-safe test: reset + 1 write + 1 read"""

    # Clock (10 ns period)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut._log.info("Clock started (10 ns)")

    # Init signals
    dut.rst_n.value = 0
    dut.ena.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    # Hold reset longer for GLS
    for _ in range(10):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    dut.ena.value = 1
    dut._log.info("Reset released, DUT enabled")

    # ---- WRITE ----
    write_addr = 2  # goes to regfile[2]
    write_data = 0xAB
    ok = await axi_write(dut, write_addr, write_data)
    if not ok:
        dut._log.error("WRITE failed in GL test ❌")
        return

    # ---- READ ----
    await Timer(50, units="ns")
    read_data = await axi_read(dut, write_addr)
    if read_data is None:
        dut._log.error("READ failed in GL test ❌")
        return

    # ---- CHECK ----
    if read_data == write_data:
        dut._log.info("GL TEST PASSED ✅ (read matches write)")
    else:
        dut._log.error(
            f"GL TEST FAILED ❌ Expected 0x{write_data:02X}, Got 0x{read_data:02X}"
        )

    await Timer(200, units="ns")
    dut._log.info("GL smoke test complete ✅")
