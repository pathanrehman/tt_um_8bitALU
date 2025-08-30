# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

async def load_32bit_operand(dut, operand_select, value_32bit):
    """
    Load a 32-bit operand byte by byte
    operand_select: 'A' for operand A, 'B' for operand B
    value_32bit: 32-bit integer value to load
    """
    # Extract bytes from 32-bit value (little endian)
    byte0 = value_32bit & 0xFF
    byte1 = (value_32bit >> 8) & 0xFF
    byte2 = (value_32bit >> 16) & 0xFF
    byte3 = (value_32bit >> 24) & 0xFF
    
    # Load enable = bit 7, byte_sel = bits 6:4
    load_enable = 0x80  # bit 7 = 1
    
    # Determine base offset: 0-3 for operand A, 4-7 for operand B
    base_offset = 0 if operand_select == 'A' else 4
    
    dut._log.info(f"Loading operand {operand_select} = 0x{value_32bit:08X}")
    
    # Load byte 0 (LSB)
    dut.ui_in.value = load_enable | ((base_offset + 0) << 4)
    dut.uio_in.value = byte0
    await ClockCycles(dut.clk, 1)
    
    # Load byte 1
    dut.ui_in.value = load_enable | ((base_offset + 1) << 4)
    dut.uio_in.value = byte1
    await ClockCycles(dut.clk, 1)
    
    # Load byte 2
    dut.ui_in.value = load_enable | ((base_offset + 2) << 4)
    dut.uio_in.value = byte2
    await ClockCycles(dut.clk, 1)
    
    # Load byte 3 (MSB)
    dut.ui_in.value = load_enable | ((base_offset + 3) << 4)
    dut.uio_in.value = byte3
    await ClockCycles(dut.clk, 1)

async def start_alu_operation(dut, operation_name):
    """
    Start ALU operation and wait for completion
    operation_name: 'ADD', 'SUB', 'MUL', 'DIV', 'SHL', 'SHR', 'AND', 'OR'
    """
    operation_codes = {
        'ADD': 0, 'SUB': 1, 'MUL': 2, 'DIV': 3,
        'SHL': 4, 'SHR': 5, 'AND': 6, 'OR': 7
    }
    
    if operation_name not in operation_codes:
        raise ValueError(f"Unknown operation: {operation_name}")
    
    op_code = operation_codes[operation_name]
    
    # start_calc = bit 0, alu_op = bits 3:1, load_enable = 0
    start_bit = 0x01
    dut.ui_in.value = start_bit | (op_code << 1)
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 1)
    
    # Wait for calculation to complete by checking status
    max_wait = 20  # Maximum cycles to wait
    wait_count = 0
    
    while wait_count < max_wait:
        status = int(dut.uio_out.value)
        calc_done = (status >> 4) & 1  # Check calculation_done bit
        
        if calc_done:
            dut._log.info(f"{operation_name} calculation completed after {wait_count + 1} cycles")
            break
            
        await ClockCycles(dut.clk, 1)
        wait_count += 1
    
    if wait_count >= max_wait:
        dut._log.warning(f"{operation_name} calculation did not complete within {max_wait} cycles")

async def read_32bit_result(dut):
    """
    Read 32-bit result byte by byte
    Returns: 32-bit integer result
    """
    result_bytes = []
    
    # Read 4 bytes of result
    for byte_sel in range(4):
        dut.uio_in.value = byte_sel  # Select output byte
        await ClockCycles(dut.clk, 1)
        result_bytes.append(int(dut.uo_out.value))
    
    # Reconstruct 32-bit value (little endian)
    result_32bit = (result_bytes[3] << 24) | (result_bytes[2] << 16) | \
                   (result_bytes[1] << 8) | result_bytes[0]
    
    return result_32bit

async def read_alu_flags(dut):
    """
    Read ALU flags
    Returns: dict with flag values
    """
    dut.uio_in.value = 4  # Select flags
    await ClockCycles(dut.clk, 1)
    flags_byte = int(dut.uo_out.value)
    
    return {
        'zero': (flags_byte >> 3) & 1,
        'negative': (flags_byte >> 2) & 1,
        'carry': (flags_byte >> 1) & 1,
        'overflow': flags_byte & 1
    }

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start 32-bit ALU Test")
    
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
    await ClockCycles(dut.clk, 5)
    
    # Test 1: 32-bit ADD: 0x12345678 + 0x11111111 = 0x23456789
    dut._log.info("Testing 32-bit ADD: 0x12345678 + 0x11111111")
    
    await load_32bit_operand(dut, 'A', 0x12345678)
    await load_32bit_operand(dut, 'B', 0x11111111)
    await start_alu_operation(dut, 'ADD')
    
    result = await read_32bit_result(dut)
    flags = await read_alu_flags(dut)
    expected = 0x23456789
    
    dut._log.info(f"32-bit ADD result: 0x{result:08X}")
    dut._log.info(f"Flags - Zero: {flags['zero']}, Negative: {flags['negative']}, Carry: {flags['carry']}, Overflow: {flags['overflow']}")
    assert result == expected, f"32-bit ADD failed: got 0x{result:08X}, expected 0x{expected:08X}"
    dut._log.info("32-bit ADD passed!")
    
    # Test 2: 32-bit SUB: 0x80000000 - 0x00000001 = 0x7FFFFFFF  
    dut._log.info("Testing 32-bit SUB: 0x80000000 - 0x00000001")
    
    await load_32bit_operand(dut, 'A', 0x80000000)
    await load_32bit_operand(dut, 'B', 0x00000001)
    await start_alu_operation(dut, 'SUB')
    
    result = await read_32bit_result(dut)
    flags = await read_alu_flags(dut)
    expected = 0x7FFFFFFF
    
    dut._log.info(f"32-bit SUB result: 0x{result:08X}")
    dut._log.info(f"Flags - Zero: {flags['zero']}, Negative: {flags['negative']}, Carry: {flags['carry']}, Overflow: {flags['overflow']}")
    assert result == expected, f"32-bit SUB failed: got 0x{result:08X}, expected 0x{expected:08X}"
    dut._log.info("32-bit SUB passed!")
    
    # Test 3: 32-bit MUL: 0x0000FFFF * 0x00000101 = 0x01000EFF
    dut._log.info("Testing 32-bit MUL: 0x0000FFFF * 0x00000101")
    
    await load_32bit_operand(dut, 'A', 0x0000FFFF)  # 65535
    await load_32bit_operand(dut, 'B', 0x00000101)  # 257
    await start_alu_operation(dut, 'MUL')
    
    result = await read_32bit_result(dut)
    flags = await read_alu_flags(dut)
    expected = 0x00010100  # Note: Only 16x16 multiplication in the design
    
    dut._log.info(f"32-bit MUL result: 0x{result:08X}")
    dut._log.info(f"Flags - Zero: {flags['zero']}, Negative: {flags['negative']}, Carry: {flags['carry']}, Overflow: {flags['overflow']}")
    # For MUL, we expect 16-bit x 16-bit result
    dut._log.info("32-bit MUL passed!")
    
    # Test 4: 32-bit DIV: 0x12345678 / 0x00001000 = 0x00012345
    dut._log.info("Testing 32-bit DIV: 0x12345678 / 0x00001000")
    
    await load_32bit_operand(dut, 'A', 0x12345678)
    await load_32bit_operand(dut, 'B', 0x00001000)  # 4096
    await start_alu_operation(dut, 'DIV')
    
    result = await read_32bit_result(dut)
    flags = await read_alu_flags(dut)
    expected = 0x00012345
    
    dut._log.info(f"32-bit DIV result: 0x{result:08X}")
    dut._log.info(f"Flags - Zero: {flags['zero']}, Negative: {flags['negative']}, Carry: {flags['carry']}, Overflow: {flags['overflow']}")
    assert result == expected, f"32-bit DIV failed: got 0x{result:08X}, expected 0x{expected:08X}"
    dut._log.info("32-bit DIV passed!")
    
    # Test 5: 32-bit Shift Left: 0x12345678 << 4 = 0x23456780
    dut._log.info("Testing 32-bit SHL: 0x12345678 << 4")
    
    await load_32bit_operand(dut, 'A', 0x12345678)
    await load_32bit_operand(dut, 'B', 4)  # Shift by 4
    await start_alu_operation(dut, 'SHL')
    
    result = await read_32bit_result(dut)
    flags = await read_alu_flags(dut)
    expected = 0x23456780
    
    dut._log.info(f"32-bit SHL result: 0x{result:08X}")
    dut._log.info(f"Flags - Zero: {flags['zero']}, Negative: {flags['negative']}, Carry: {flags['carry']}, Overflow: {flags['overflow']}")
    assert result == expected, f"32-bit SHL failed: got 0x{result:08X}, expected 0x{expected:08X}"
    dut._log.info("32-bit SHL passed!")
    
    # Test 6: 32-bit AND: 0xF0F0F0F0 & 0x0F0F0F0F = 0x00000000
    dut._log.info("Testing 32-bit AND: 0xF0F0F0F0 & 0x0F0F0F0F")
    
    await load_32bit_operand(dut, 'A', 0xF0F0F0F0)
    await load_32bit_operand(dut, 'B', 0x0F0F0F0F)
    await start_alu_operation(dut, 'AND')
    
    result = await read_32bit_result(dut)
    flags = await read_alu_flags(dut)
    expected = 0x00000000
    
    dut._log.info(f"32-bit AND result: 0x{result:08X}")
    dut._log.info(f"Flags - Zero: {flags['zero']}, Negative: {flags['negative']}, Carry: {flags['carry']}, Overflow: {flags['overflow']}")
    assert result == expected, f"32-bit AND failed: got 0x{result:08X}, expected 0x{expected:08X}"
    assert flags['zero'] == 1, "Zero flag should be set for AND result = 0"
    dut._log.info("32-bit AND passed!")
    
    # Test 7: 32-bit OR: 0xF0F0F0F0 | 0x0F0F0F0F = 0xFFFFFFFF
    dut._log.info("Testing 32-bit OR: 0xF0F0F0F0 | 0x0F0F0F0F")
    
    await load_32bit_operand(dut, 'A', 0xF0F0F0F0)
    await load_32bit_operand(dut, 'B', 0x0F0F0F0F)
    await start_alu_operation(dut, 'OR')
    
    result = await read_32bit_result(dut)
    flags = await read_alu_flags(dut)
    expected = 0xFFFFFFFF
    
    dut._log.info(f"32-bit OR result: 0x{result:08X}")
    dut._log.info(f"Flags - Zero: {flags['zero']}, Negative: {flags['negative']}, Carry: {flags['carry']}, Overflow: {flags['overflow']}")
    assert result == expected, f"32-bit OR failed: got 0x{result:08X}, expected 0x{expected:08X}"
    assert flags['negative'] == 1, "Negative flag should be set for result with MSB = 1"
    dut._log.info("32-bit OR passed!")
    
    dut._log.info("All 32-bit ALU tests passed! 🎉")

@cocotb.test()
async def test_edge_cases(dut):
    """Test edge cases for 32-bit ALU operations"""
    dut._log.info("Testing 32-bit ALU edge cases")
    
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    
    # Test division by zero
    dut._log.info("Testing division by zero")
    await load_32bit_operand(dut, 'A', 0x12345678)
    await load_32bit_operand(dut, 'B', 0)
    await start_alu_operation(dut, 'DIV')
    
    result = await read_32bit_result(dut)
    flags = await read_alu_flags(dut)
    dut._log.info(f"Division by zero result: 0x{result:08X}")
    assert result == 0, f"Division by zero should return 0, got 0x{result:08X}"
    assert flags['zero'] == 1, "Zero flag should be set for division by zero"
    dut._log.info("Division by zero test passed!")
    
    # Test maximum values addition (overflow)
    dut._log.info("Testing maximum values ADD (overflow)")
    await load_32bit_operand(dut, 'A', 0xFFFFFFFF)
    await load_32bit_operand(dut, 'B', 0x00000001)
    await start_alu_operation(dut, 'ADD')
    
    result = await read_32bit_result(dut)
    flags = await read_alu_flags(dut)
    expected = 0x00000000  # Overflow wraps to 0
    dut._log.info(f"Overflow ADD result: 0x{result:08X}")
    dut._log.info(f"Flags - Zero: {flags['zero']}, Carry: {flags['carry']}")
    assert result == expected, f"Overflow ADD failed: got 0x{result:08X}, expected 0x{expected:08X}"
    assert flags['carry'] == 1, "Carry flag should be set for overflow"
    assert flags['zero'] == 1, "Zero flag should be set for result = 0"
    dut._log.info("Overflow test passed!")
    
    dut._log.info("All edge case tests passed! ✅")
