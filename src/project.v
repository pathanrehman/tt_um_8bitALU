/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */
`default_nettype none
module tt_um_8bitalu (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

  // ALU inputs - properly mapped from input pins
  wire [31:0] alu_in_a, alu_in_b;
  wire [4:0]  alu_op;
  wire [31:0] alu_result;
  wire        alu_zero, alu_neg, alu_carry, alu_overflow;

  // Pipeline stage registers
  reg [31:0] pipe1_result, pipe2_result, pipe3_result;
  reg [3:0]  pipe3_flags;

  // Map inputs - extend 8-bit inputs to 32-bit
  assign alu_in_a = {24'b0, ui_in};           // ui_in as operand A
  assign alu_in_b = {24'b0, uio_in[7:3]};     // upper 5 bits of uio_in as operand B  
  assign alu_op = uio_in[4:0];                // lower 5 bits of uio_in as opcode

  // 3-stage pipeline to match typical ALU pipeline depth
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pipe1_result <= 32'b0;
      pipe2_result <= 32'b0;
      pipe3_result <= 32'b0;
      pipe3_flags <= 4'b0;
    end else if (ena) begin
      pipe1_result <= alu_result;
      pipe2_result <= pipe1_result;
      pipe3_result <= pipe2_result;
      pipe3_flags <= {alu_zero, alu_neg, alu_carry, alu_overflow};
    end
  end

  // ALU instantiation
  alu32_pipelined u_alu (
    .a(alu_in_a), 
    .b(alu_in_b), 
    .op(alu_op),
    .result(alu_result),
    .zero(alu_zero), 
    .neg(alu_neg),
    .carry(alu_carry), 
    .overflow(alu_overflow),
    .clk(clk), 
    .rst_n(rst_n)
  );

  // Output assignments
  assign uo_out = pipe3_result[7:0];          // Lower 8 bits of pipelined result
  assign uio_out = {4'b0, pipe3_flags};       // Flags on lower 4 bits
  assign uio_oe = 8'h0F;                      // Enable lower 4 bits for output

endmodule

// Updated ALU Module
module alu32_pipelined (
  input  wire [31:0] a, b,
  input  wire [4:0]  op,
  output reg  [31:0] result,
  output reg         zero, neg, carry, overflow,
  input  wire        clk, rst_n
);
  
  reg [32:0] temp_result;
  
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      result <= 32'b0;
      zero <= 1'b0;
      neg <= 1'b0;
      carry <= 1'b0;
      overflow <= 1'b0;
    end else begin
      case (op[2:0])  // Use only lower 3 bits for simplicity
        3'b000: temp_result = a + b;        // ADD
        3'b001: temp_result = a - b;        // SUB
        3'b010: temp_result = a * b;        // MUL (lower 32 bits)
        3'b011: temp_result = (b != 0) ? a / b : 32'b0;  // DIV
        3'b100: temp_result = a << b[4:0];  // SHIFT LEFT
        3'b101: temp_result = a >> b[4:0];  // SHIFT RIGHT
        default: temp_result = 33'b0;
      endcase
      
      result <= temp_result[31:0];
      carry <= temp_result[32];
      zero <= (temp_result[31:0] == 32'b0);
      neg <= temp_result[31];
      overflow <= (op[2:0] == 3'b000) ? // Only for ADD
        ((a[31] == b[31]) && (temp_result[31] != a[31])) : 1'b0;
    end
  end
endmodule
