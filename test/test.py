import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer


@cocotb.test()
async def axi4lite_test(dut):
    """AXI4-Lite cocotb testbench"""

    # Start clock (100 MHz -> period 10 ns)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    dut.rst_n.value = 0
    dut.ena.value   = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    await Timer(20, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # ---------------- WRITE ----------------
    await Timer(20, units="ns")
    dut.ui_in.value = (2 << 1) | 0b1   # write_addr=2, start_write=1
    dut.uio_in.value = 0x4             # write_data = 0x04
    await Timer(10, units="ns")
    dut.ui_in.value = (2 << 1)         # deassert start_write

    # wait for done
    while dut.uo_out.value[0] != 1:
        await RisingEdge(dut.clk)

    cocotb.log.info(f"WRITE: Addr=0x{2:X} Data=0x{int(dut.uio_in.value):02X}")

    # ---------------- READ ----------------
    await Timer(20, units="ns")
    dut.ui_in.value = (2 << 2) | (1 << 4)   # read_addr=2, start_read=1
    await Timer(10, units="ns")
    dut.ui_in.value = (2 << 2)              # deassert start_read

    while dut.uo_out.value[0] != 1:
        await RisingEdge(dut.clk)

    read_data = int(dut.uio_out.value)
    cocotb.log.info(f"READ: Addr=0x{2:X} Data=0x{read_data:02X}")

    # ---------------- CHECK ----------------
    if read_data == 0x4:
        cocotb.log.info("TEST PASSED ✅")
    else:
        cocotb.log.error(f"TEST FAILED ❌ (Expected 0x04, Got 0x{read_data:02X})")

    await Timer(100, units="ns")
