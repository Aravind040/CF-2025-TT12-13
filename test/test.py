import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge


async def axi_write(dut, addr, data, timeout_cycles=200):
    """
    Perform one AXI4-Lite write transaction using the top-level UI mapping:
      ui_in[0]   = start_write
      ui_in[2:1] = write_addr
      uio_in     = write_data
    Waits for uo_out[0] (done) to assert.
    """
    # Drive inputs
    ui_val = (addr << 1) | 0b1  # start_write = 1, write_addr in bits [2:1]
    dut.ui_in.value = ui_val
    dut.uio_in.value = data
    dut._log.info(f"DRIVE WRITE : ui_in=0b{ui_val:08b}, uio_in=0x{data:02X}")

    # Short pulse for start
    await Timer(10, units="ns")
    dut.ui_in.value = (addr << 1)  # deassert start_write
    dut._log.debug("Deasserted start_write")

    # Wait for done bit uo_out[0]
    for i in range(timeout_cycles):
        done_bit = int(dut.uo_out.value) & 0x1
        if done_bit == 1:
            dut._log.info(f"WRITE DONE: Addr=0x{addr:X}, Data=0x{data:02X} (cycles waited={i})")
            return True
        await RisingEdge(dut.clk)

    dut._log.error("Timeout waiting for WRITE done ❌")
    return False


async def axi_read(dut, addr, timeout_cycles=200):
    """
    Perform one AXI4-Lite read transaction using mapping:
      ui_in[4]   = start_read
      ui_in[3:2] = read_addr
    Waits for uo_out[0] (done) and returns uio_out (read data).
    """
    ui_val = (addr << 2) | (1 << 4)  # start_read = 1, read_addr in bits [3:2]
    dut.ui_in.value = ui_val
    dut._log.info(f"DRIVE READ  : ui_in=0b{ui_val:08b}")

    # Short pulse for start
    await Timer(10, units="ns")
    dut.ui_in.value = (addr << 2)  # deassert start_read
    dut._log.debug("Deasserted start_read")

    # Wait for done bit uo_out[0]
    for i in range(timeout_cycles):
        done_bit = int(dut.uo_out.value) & 0x1
        if done_bit == 1:
            data = int(dut.uio_out.value) & 0xFF
            dut._log.info(f"READ DONE: Addr=0x{addr:X}, Data=0x{data:02X} (cycles waited={i})")
            return data
        await RisingEdge(dut.clk)

    dut._log.error("Timeout waiting for READ done ❌")
    return None


@cocotb.test()
async def axi4lite_test(dut):
    """
    Cocotb test for tt_um_axi4lite_top top-level:
      - Drives clk, rst_n, ena, ui_in, uio_in
      - Performs one write then one read and compares values
    """

    # --- Clock generation (10 ns period -> 100 MHz) ---
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut._log.info("Clock started on dut.clk (10 ns period)")

    # --- Initialize signals ---
    dut.rst_n.value = 0      # active-low reset asserted
    dut.ena.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await Timer(20, units="ns")

    # Release reset and enable DUT
    dut.rst_n.value = 1
    dut.ena.value = 1
    await RisingEdge(dut.clk)
    dut._log.info("Reset released and ena asserted")

    # Small settle time
    await Timer(20, units="ns")

    # --- WRITE transaction ---
    write_addr = 2
    write_data = 0x04
    ok = await axi_write(dut, addr=write_addr, data=write_data)
    if not ok:
        dut._log.error("Write failed -> aborting test")
        return

    # Allow the design a couple cycles to update internal state
    await Timer(20, units="ns")

    # --- READ transaction ---
    read_data = await axi_read(dut, addr=write_addr)
    if read_data is None:
        dut._log.error("Read timed out -> aborting test")
        return

    # --- VERIFY ---
    if read_data == write_data:
        dut._log.info("TEST PASSED ✅ (Read matches written value)")
    else:
        dut._log.error(f"TEST FAILED ❌ Expected 0x{write_data:02X}, Got 0x{read_data:02X}")

    # Give some time for final logging to show up in sims
    await Timer(100, units="ns")
    dut._log.info("Test finished")
