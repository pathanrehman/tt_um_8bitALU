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
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # Test ADD (example: set opcode and operands accordingly)
    dut.ui_in.value = 0b00000  # Opcode for ADD
    dut.uio_in.value = 0b00010100  # Operand B = 20
    dut._log.info("Testing ADD: 20 + 30")
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b00011110  # Operand A = 30
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == 50, f"ADD failed: {dut.uo_out.value}"
    dut._log.info("ADD passed.")

    # Test SUB (example)
    dut.ui_in.value = 0b00001  # Opcode for SUB
    dut.uio_in.value = 40  # Operand B
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 10  # Operand A
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == -30, f"SUB failed: {dut.uo_out.value}"
    dut._log.info("SUB passed.")

    # Test MUL (example)
    dut.ui_in.value = 0b00010  # Opcode for MUL
    dut.uio_in.value = 6
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 7
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == 42, f"MUL failed: {dut.uo_out.value}"
    dut._log.info("MUL passed.")

    # Additional tests: DIV, SHIFT, etc.

    # For each operation, set opcode and operands, then check for correct output.
    # Example (Barrel Shift Left):
    dut.ui_in.value = 0b00100  # Opcode for SHL
    dut.uio_in.value = 2  # shift amount
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 8  # value to shift
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == 32, f"SHL failed: {dut.uo_out.value}"
    dut._log.info("SHIFT passed.")

    dut._log.info("All basic ALU tests passed.")
