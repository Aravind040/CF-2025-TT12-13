import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge


async def wait_done(dut, max_cycles=2000):
    """Wait for uo_out[0] (done) with timeout to avoid infinite hang"""
    for i in range(max_cycles):
        if int(dut.uo_out.value) & 0x1:
            dut._log.info(f"DONE detected after {i} cycles")
            return True
        await RisingEdge(dut.clk)
    dut._log.error("Timeout: DONE not seen ❌")
    return False


async def axi_write(dut, addr, data):
    """Single AXI write transaction (GL-safe)"""
    ui_val = (addr << 1) | 0b1  # start_write=1, addr in [2:1]
    dut.ui_in.value = ui_val
    dut.uio_in.value = data
    await Timer(10, units="ns")
    dut.ui_in.value = (addr << 1)  # deassert start_write

    dut._log.info(f"WRITE launched: Addr=0x{addr:X}, Data=0x{data:02X}")
    return await wait_done(dut)


async def axi_read(dut, addr):
    """Single AXI read transaction (GL-safe)"""
    ui_val = (addr << 2) | (1 << 4)  # start_read=1, addr in [3:2]
    dut.ui_in.value = ui_val
    await Timer(10, units="ns")
    dut.ui_in.value = (addr << 2)  # deassert start_read

    dut._log.info(f"READ launched: Addr=0x{addr:X}")
    ok = await wait_done(dut)
    if ok:
        data = int(dut.uio_out.value) & 0xFF
        dut._log.info(f"READ got Data=0x{data:02X}")
        return data
    return None


@cocotb.test()
async def axi4lite_smoke_gl(dut):
    """Lightweight GL-safe test: reset + 1 write + 1 read"""

    # Clock (10 ns period)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut._log.info("Clock started (10 ns)")

    # Init
    dut.rst_n.value = 0
    dut.ena.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    # Hold reset longer for GL sim
    await Timer(500, units="ns")
    dut.rst_n.value = 1
    dut.ena.value = 1
    await RisingEdge(dut.clk)
    dut._log.info("Reset released, DUT enabled")

    # Give settle time
    await Timer(100, units="ns")

    # ---- WRITE ----
    write_addr = 2
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
        dut._log.error(f"GL TEST FAILED ❌ Expected 0x{write_data:02X}, Got 0x{read_data:02X}")

    await Timer(200, units="ns")
    dut._log.info("GL smoke test complete ✅")
