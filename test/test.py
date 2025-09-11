import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge


async def axi_write(dut, addr, data):
    """
    Perform one AXI4-Lite write transaction.
    Maps to Verilog test sequence write.
    ui_in[0]   = start_write
    ui_in[2:1] = write_addr
    uio_in     = write_data
    """
    dut.ui_in.value = (addr << 1) | 0b1   # start_write=1
    dut.uio_in.value = data
    await Timer(10, units="ns")
    dut.ui_in.value = (addr << 1)         # deassert start_write

    # Wait for done
    for _ in range(50):  # avoid infinite loop
        if int(dut.uo_out.value[0]) == 1:
            dut._log.info(f"WRITE DONE: Addr=0x{addr:X}, Data=0x{data:02X}")
            return
        await RisingEdge(dut.clk)

    dut._log.error("Timeout waiting for WRITE done ❌")


async def axi_read(dut, addr):
    """
    Perform one AXI4-Lite read transaction.
    Maps to Verilog test sequence read.
    ui_in[4]   = start_read
    ui_in[3:2] = read_addr
    """
    dut.ui_in.value = (addr << 2) | (1 << 4)   # start_read=1
    await Timer(10, units="ns")
    dut.ui_in.value = (addr << 2)              # deassert start_read

    # Wait for done
    for _ in range(50):  # avoid infinite loop
        if int(dut.uo_out.value[0]) == 1:
            data = int(dut.uio_out.value)
            dut._log.info(f"READ DONE: Addr=0x{addr:X}, Data=0x{data:02X}")
            return data
        await RisingEdge(dut.clk)

    dut._log.error("Timeout waiting for READ done ❌")
    return None


@cocotb.test()
async def axi4lite_test(dut):
    """
    Cocotb testbench for AXI4-Lite interface.
    Modeled similar to JTAG TAP testbench structure.
    """

    # --- Clock generation (100 MHz, 10 ns period) ---
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # --- Initialize ---
    dut.rst_n.value = 0
    dut.ena.value   = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    # --- Reset sequence ---
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    dut._log.info("Reset deasserted, starting test sequence")

    # --- WRITE ---
    await Timer(20, units="ns")
    await axi_write(dut, addr=2, data=0x04)

    # --- READ ---
    await Timer(20, units="ns")
    read_data = await axi_read(dut, addr=2)

    # --- CHECK ---
    if read_data == 0x04:
        dut._log.info("TEST PASSED ✅ (Read matches written value)")
    else:
        dut._log.error(f"TEST FAILED ❌ (Expected 0x04, Got 0x{read_data:02X})")

    await Timer(100, units="ns")
    dut._log.info("TEST COMPLETE ✅")
