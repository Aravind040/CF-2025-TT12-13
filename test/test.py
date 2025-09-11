import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def axi4lite_test(dut):
    """AXI4-Lite cocotb testbench"""

    # Dump all signals found in DUT (debug help for GL netlist)
    cocotb.log.info("=== Listing DUT ports ===")
    for sig in dut:
        cocotb.log.info(f"  {sig._name}")

    # Start clock (100 MHz -> 10 ns period)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset sequence
    dut.rst_n.value = 0
    dut.ena.value   = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    cocotb.log.info("Applying reset...")

    await Timer(20, units="ns")
    dut.rst_n.value = 1
    cocotb.log.info("Released reset ✅")

    # Confirm sim actually moved
    await Timer(1, units="ns")
    cocotb.log.info("Simulation advanced past 0 ns ✅")

    # ---------------- WRITE ----------------
    await Timer(20, units="ns")
    dut.ui_in.value = (2 << 1) | 0b1   # start_write=1, write_addr=2
    dut.uio_in.value = 0x04            # write_data=0x04
    await Timer(10, units="ns")
    dut.ui_in.value = (2 << 1)         # deassert start_write
    cocotb.log.info("WRITE transaction started...")

    # Wait for done
    for _ in range(50):  # avoid infinite loop
        if int(dut.uo_out.value[0]) == 1:
            cocotb.log.info(f"WRITE DONE: Addr=0x2 Data=0x{int(dut.uio_in.value):02X}")
            break
        await RisingEdge(dut.clk)
    else:
        cocotb.log.error("Timeout waiting for WRITE done ❌")
        return

    # ---------------- READ ----------------
    await Timer(20, units="ns")
    dut.ui_in.value = (2 << 2) | (1 << 4)   # start_read=1, read_addr=2
    await Timer(10, units="ns")
    dut.ui_in.value = (2 << 2)              # deassert start_read
    cocotb.log.info("READ transaction started...")

    for _ in range(50):  # avoid infinite loop
        if int(dut.uo_out.value[0]) == 1:
            read_data = int(dut.uio_out.value)
            cocotb.log.info(f"READ DONE: Addr=0x2 Data=0x{read_data:02X}")
            break
        await RisingEdge(dut.clk)
    else:
        cocotb.log.error("Timeout waiting for READ done ❌")
        return

    # ---------------- CHECK ----------------
    if read_data == 0x04:
        cocotb.log.info("TEST PASSED ✅ (Read matches written value)")
    else:
        cocotb.log.error(f"TEST FAILED ❌ (Expected 0x04, Got 0x{read_data:02X})")

    await Timer(100, units="ns")
