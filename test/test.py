# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start ALU Test")
    # Set clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset sequence
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)  # Allow pipeline to stabilize

    # Test ADD: 20 + 30 = 50
    dut._log.info("Testing ADD: 20 + 30")
    dut.ui_in.value = 20           # Operand A = 20
    dut.uio_in.value = (30 << 3) | 0  # Operand B = 30 (bits 7:3), opcode = 0 (bits 4:0)
    
    # Wait for pipeline delay (3 stages + ALU computation)
    await ClockCycles(dut.clk, 5)
    
    result = dut.uo_out.value
    dut._log.info(f"ADD result: {result}")
    assert result == 50, f"ADD failed: got {result}, expected 50"
    dut._log.info("ADD passed.")

    # Test SUB: 30 - 10 = 20
    dut._log.info("Testing SUB: 30 - 10")
    dut.ui_in.value = 30           # Operand A = 30
    dut.uio_in.value = (10 << 3) | 1  # Operand B = 10, opcode = 1 (SUB)
    await ClockCycles(dut.clk, 5)
    
    result = dut.uo_out.value
    dut._log.info(f"SUB result: {result}")
    assert result == 20, f"SUB failed: got {result}, expected 20"
    dut._log.info("SUB passed.")

    # Test MUL: 6 * 7 = 42
    dut._log.info("Testing MUL: 6 * 7")
    dut.ui_in.value = 6            # Operand A = 6
    dut.uio_in.value = (7 << 3) | 2   # Operand B = 7, opcode = 2 (MUL)
    await ClockCycles(dut.clk, 5)
    
    result = dut.uo_out.value
    dut._log.info(f"MUL result: {result}")
    assert result == 42, f"MUL failed: got {result}, expected 42"
    dut._log.info("MUL passed.")

    dut._log.info("All ALU tests passed.")
