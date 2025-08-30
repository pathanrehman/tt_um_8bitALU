
## How it works

This project implements a 32-bit fully pipelined Arithmetic Logic Unit (ALU) in Verilog, supporting arithmetic, logical, multiply, divide, and barrel shift operations. It features advanced flag management, integrated pipeline stages for increased throughput, and bypass logic to resolve data hazards. Inputs select operations and operands; results and flags are updated in each clock cycle via dedicated outputs.

## How to test

1. Connect the chip to a Tiny Tapeout demo board or compatible FPGA.
2. Provide 32-bit operands and an operation code through the input pins (`ui_in` and `uio_in`).
3. Set the reset (`rst_n`) and clock (`clk`) signals appropriately.
4. Observe output pins (`uo_out`) for the result and flag status—verify correct output for additions, multiplications, shifts, etc.
5. Test sequential operations to confirm pipelined operation and proper bypassing of results.
6. Optionally, use simulation tools (e.g., Cocotb or GTKWave) for automated verification.

## External hardware

This project does not require any external hardware beyond the standard Tiny Tapeout test/demo boards. Optionally, it can be connected to an FPGA development board for initial verification prior to tapeout. There are no dependencies on displays, sensors, or PMODs.[4][1]
