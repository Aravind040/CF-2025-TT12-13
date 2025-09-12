import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def axi4lite_smoke(dut):
    """AXI4Lite Smoke Test: Write then Read"""

    # Start clock (10 ns period = 100 MHz)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply reset
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await Timer(50, units="ns")   # hold reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    cocotb.log.info("Reset released")

    # ---------------- WRITE ----------------
    write_addr = 0x1
    write_data = 0x04

    dut.ui_in.value = (1 << 0) | (write_addr << 1)  # start_write + addr
    dut.uio_in.value = write_data

    await RisingEdge(dut.clk)
    dut.ui_in.value = (write_addr << 1)  # deassert start_write

    # Wait for done
    while dut.uo_out.value.integer & 0x1 == 0:
        await RisingEdge(dut.clk)

    cocotb.log.info(f"WRITE: Addr=0x{write_addr:X} Data=0x{write_data:02X}")

    # ---------------- READ ----------------
    read_addr = write_addr
    dut.ui_in.value = (1 << 5) | (read_addr << 3)  # start_read + addr

    await RisingEdge(dut.clk)
    dut.ui_in.value = (read_addr << 3)  # deassert start_read

    # Wait for done
    while dut.uo_out.value.integer & 0x1 == 0:
        await RisingEdge(dut.clk)

    read_val = dut.uio_out.value.integer
    cocotb.log.info(f"READ:  Addr=0x{read_addr:X} Data=0x{read_val:02X}")

    # ---------------- CHECK ----------------
    if read_val == write_data:
        cocotb.log.info("TEST PASSED ✅ (read matches write)")
    else:
        raise cocotb.result.TestFailure(
            f"TEST FAILED ❌ Expected 0x{write_data:02X}, got 0x{read_val:02X}"
        )
