/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */
`default_nettype none
module tt_um_example (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

  // Control signal decoding from ui_in
  wire load_enable = ui_in[7];           // Bit 7: Enable loading operands
  wire [2:0] byte_sel = ui_in[6:4];      // Bits 6:4: Byte select (0-7)
  wire [2:0] alu_op = ui_in[3:1];        // Bits 3:1: ALU operation code
  wire start_calc = ui_in[0];            // Bit 0: Start calculation

  // 32-bit operand registers
  reg [31:0] operand_a, operand_b;
  reg [31:0] alu_result_reg;
  reg [3:0] alu_flags_reg;
  reg calculation_done;
  reg [2:0] calc_state;

  // ALU signals
  wire [31:0] alu_result;
  wire alu_zero, alu_neg, alu_carry, alu_overflow;

  // Pipeline registers for ALU result
  reg [31:0] pipe1_result, pipe2_result, pipe3_result;
  reg [3:0] pipe1_flags, pipe2_flags, pipe3_flags;

  // State machine for calculation
  localparam IDLE = 3'b000;
  localparam CALC1 = 3'b001;
  localparam CALC2 = 3'b010;
  localparam CALC3 = 3'b011;
  localparam DONE = 3'b100;

  // Operand loading logic
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      operand_a <= 32'b0;
      operand_b <= 32'b0;
      alu_result_reg <= 32'b0;
      alu_flags_reg <= 4'b0;
      calculation_done <= 1'b0;
      calc_state <= IDLE;
      pipe1_result <= 32'b0;
      pipe2_result <= 32'b0;
      pipe3_result <= 32'b0;
      pipe1_flags <= 4'b0;
      pipe2_flags <= 4'b0;
      pipe3_flags <= 4'b0;
    end else if (ena) begin
      // Loading operands byte by byte
      if (load_enable) begin
        case (byte_sel)
          3'b000: operand_a[7:0]   <= uio_in;   // Load A byte 0 (LSB)
          3'b001: operand_a[15:8]  <= uio_in;   // Load A byte 1
          3'b010: operand_a[23:16] <= uio_in;   // Load A byte 2
          3'b011: operand_a[31:24] <= uio_in;   // Load A byte 3 (MSB)
          3'b100: operand_b[7:0]   <= uio_in;   // Load B byte 0 (LSB)
          3'b101: operand_b[15:8]  <= uio_in;   // Load B byte 1
          3'b110: operand_b[23:16] <= uio_in;   // Load B byte 2
          3'b111: operand_b[31:24] <= uio_in;   // Load B byte 3 (MSB)
        endcase
        calculation_done <= 1'b0;
        calc_state <= IDLE;
      end
      // Start calculation
      else if (start_calc && calc_state == IDLE) begin
        calc_state <= CALC1;
        calculation_done <= 1'b0;
      end
      // Calculation state machine (3-stage pipeline)
      else begin
        case (calc_state)
          CALC1: begin
            pipe1_result <= alu_result;
            pipe1_flags <= {alu_zero, alu_neg, alu_carry, alu_overflow};
            calc_state <= CALC2;
          end
          CALC2: begin
            pipe2_result <= pipe1_result;
            pipe2_flags <= pipe1_flags;
            calc_state <= CALC3;
          end
          CALC3: begin
            pipe3_result <= pipe2_result;
            pipe3_flags <= pipe2_flags;
            alu_result_reg <= pipe2_result;
            alu_flags_reg <= pipe2_flags;
            calculation_done <= 1'b1;
            calc_state <= DONE;
          end
          DONE: begin
            if (!start_calc) begin
              calc_state <= IDLE;
              calculation_done <= 1'b0;
            end
          end
          default: calc_state <= IDLE;
        endcase
      end
    end
  end

  // ALU instantiation
  alu32_pipelined u_alu (
    .a(operand_a), 
    .b(operand_b), 
    .op({2'b00, alu_op}),  // Extend to 5 bits
    .result(alu_result),
    .zero(alu_zero), 
    .neg(alu_neg),
    .carry(alu_carry), 
    .overflow(alu_overflow),
    .clk(clk), 
    .rst_n(rst_n)
  );

  // Output result selection (byte by byte readout)
  wire [2:0] output_byte_sel = uio_in[2:0];
  reg [7:0] output_byte;
  
  always @(*) begin
    if (calculation_done) begin
      case (output_byte_sel)
        3'b000: output_byte = alu_result_reg[7:0];     // Result byte 0 (LSB)
        3'b001: output_byte = alu_result_reg[15:8];    // Result byte 1
        3'b010: output_byte = alu_result_reg[23:16];   // Result byte 2
        3'b011: output_byte = alu_result_reg[31:24];   // Result byte 3 (MSB)
        3'b100: output_byte = {4'b0, alu_flags_reg};   // Flags
        default: output_byte = 8'b0;
      endcase
    end else begin
      // During loading or calculation, show current pipeline state
      output_byte = pipe3_result[7:0];
    end
  end

  // Output assignments
  assign uo_out = output_byte;
  assign uio_out = {3'b0, calculation_done, calc_state, 1'b0};  // Status output
  assign uio_oe = 8'h1F;  // Enable lower 5 bits for status output

endmodule

// Updated ALU Module with combinational logic
module alu32_pipelined (
  input  wire [31:0] a, b,
  input  wire [4:0]  op,
  output reg  [31:0] result,
  output reg         zero, neg, carry, overflow,
  input  wire        clk, rst_n
);
  
  reg [32:0] temp_result;
  
  // Combinational ALU logic
  always @(*) begin
    case (op[2:0])
      3'b000: temp_result = {1'b0, a} + {1'b0, b};        // ADD
      3'b001: temp_result = {1'b0, a} - {1'b0, b};        // SUB
      3'b010: temp_result = {1'b0, a[15:0] * b[15:0]};    // MUL (16x16 to fit)
      3'b011: temp_result = (b != 0) ? {1'b0, a / b} : 33'b0;  // DIV
      3'b100: temp_result = {1'b0, a << b[4:0]};          // SHIFT LEFT
      3'b101: temp_result = {1'b0, a >> b[4:0]};          // SHIFT RIGHT
      3'b110: temp_result = {1'b0, a & b};                // AND
      3'b111: temp_result = {1'b0, a | b};                // OR
      default: temp_result = 33'b0;
    endcase
  end

  // Output assignments
  always @(*) begin
    result = temp_result[31:0];
    carry = temp_result[32];
    zero = (temp_result[31:0] == 32'b0);
    neg = temp_result[31];
    
    // Overflow detection for ADD/SUB
    if (op[2:0] == 3'b000) // ADD
      overflow = (a[31] == b[31]) && (temp_result[31] != a[31]);
    else if (op[2:0] == 3'b001) // SUB
      overflow = (a[31] != b[31]) && (temp_result[31] != a[31]);
    else
      overflow = 1'b0;
  end

endmodule
