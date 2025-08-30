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

  // ALU inputs - properly driven from input pins
  wire [31:0] alu_in_a, alu_in_b;
  wire [4:0]  alu_op;
  wire [31:0] alu_result;
  wire        alu_zero, alu_neg, alu_carry, alu_overflow;

  // Pipeline stage registers
  reg [31:0] ex_result, mem_result, wb_result;
  reg [3:0]  wb_flags;

  // Connect input pins to ALU inputs
  assign alu_in_a = {24'b0, ui_in};        // Extend 8-bit input to 32-bit
  assign alu_in_b = {24'b0, uio_in[7:3]};  // Use upper 5 bits for operand B
  assign alu_op = uio_in[4:0];             // Use lower 5 bits for operation

  // Pipeline registers
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      ex_result <= 32'b0;
      mem_result <= 32'b0;
      wb_result <= 32'b0;
      wb_flags <= 4'b0;
    end else if (ena) begin
      ex_result <= alu_result;
      mem_result <= ex_result;
      wb_result <= mem_result;
      wb_flags <= {alu_zero, alu_neg, alu_carry, alu_overflow};
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
  assign uo_out = wb_result[7:0];         // Lower 8 bits of result
  assign uio_out = {4'b0, wb_flags};      // Flags output
  assign uio_oe = 8'h0F;                  // Enable lower 4 bits for flag output

endmodule

// ALU Module (updated to use clock properly)
module alu32_pipelined (
  input  wire [31:0] a, b,
  input  wire [4:0]  op,
  output reg  [31:0] result,
  output reg         zero, neg, carry, overflow,
  input  wire        clk, rst_n
);
  
  wire [31:0] add_sub_out, mul_out, div_out, shift_out;
  wire        add_carry, add_overflow;

  // Combinational operations
  assign {add_carry, add_sub_out} = (op[0] == 0) ? a + b : a - b;
  assign add_overflow = (op[0] == 0) ? 
    ((a[31] == b[31]) && (add_sub_out[31] != a[31])) : 
    ((a[31] != b[31]) && (add_sub_out[31] != a[31]));
  
  assign mul_out = a * b;
  assign div_out = (b != 0) ? a / b : 32'b0;
  assign shift_out = (op[0] == 0) ? a << b[4:0] : a >> b[4:0];

  // Registered outputs for pipeline
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      result <= 32'b0;
      zero <= 1'b0;
      neg <= 1'b0;
      carry <= 1'b0;
      overflow <= 1'b0;
    end else begin
      case (op[4:1])
        4'b0000: result <= add_sub_out;     // ADD/SUB
        4'b0001: result <= mul_out;         // MUL
        4'b0010: result <= div_out;         // DIV
        4'b0011: result <= shift_out;       // SHIFT
        default: result <= 32'b0;
      endcase
      
      zero <= (result == 0);
      neg <= result[31];
      carry <= (op[4:1] == 4'b0000) ? add_carry : 1'b0;
      overflow <= (op[4:1] == 4'b0000) ? add_overflow : 1'b0;
    end
  end
endmodule
