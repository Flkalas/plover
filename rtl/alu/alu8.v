// 8-bit ALU: 74HC283 cascade + 86/08/32 logic + 153 output mux
`default_nettype none

module alu8 #(
    parameter ALU_NOP    = 4'd0,
    parameter ALU_ADD    = 4'd1,
    parameter ALU_SUB    = 4'd2,
    parameter ALU_AND    = 4'd3,
    parameter ALU_OR     = 4'd4,
    parameter ALU_XOR    = 4'd5,
    parameter ALU_NOT    = 4'd6,
    parameter ALU_PASS_A = 4'd7,
    parameter ALU_PASS_B = 4'd8,
    parameter ALU_INC    = 4'd9,
    parameter ALU_DEC    = 4'd10,
    parameter ALU_CMP    = 4'd11
) (
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [3:0] alu_sel,
    output wire [7:0] y,
    output wire       cout,
    output wire       zero
);

    wire [7:0] b_sub   = b ^ 8'hFF;
    wire [7:0] b_adder = (alu_sel == ALU_SUB) ? b_sub : b;

    wire [7:0] sum_arith;
    wire       cout_arith;

    hc283_cascade u_add (
        .a   (a),
        .b   (b_adder),
        .cin ((alu_sel == ALU_SUB) ? 1'b1 : 1'b0),
        .sum (sum_arith),
        .cout(cout_arith)
    );

    wire [7:0] and_out = a & b;
    wire [7:0] or_out  = a | b;
    wire [7:0] xor_out = a ^ b;
    wire [7:0] not_out = ~a;

    wire [7:0] inc_sum;
    wire       inc_cout;
    hc283_cascade u_inc (
        .a   (a),
        .b   (8'd1),
        .cin (1'b0),
        .sum (inc_sum),
        .cout(inc_cout)
    );

    wire [7:0] dec_sum;
    wire       dec_cout;
    hc283_cascade u_dec (
        .a   (a),
        .b   (8'hFF),
        .cin (1'b1),
        .sum (dec_sum),
        .cout(dec_cout)
    );

    // 153-style: pick arithmetic vs logic path nibble-wise (simplified 8b mux)
    reg [7:0] result;
    reg       carry_out;

    always @(*) begin
        result    = 8'd0;
        carry_out = 1'b0;
        case (alu_sel)
            ALU_NOP: begin
                result    = 8'd0;
                carry_out = 1'b0;
            end
            ALU_ADD: begin
                result    = sum_arith;
                carry_out = cout_arith;
            end
            ALU_SUB, ALU_CMP: begin
                result    = sum_arith;
                // Borrow flag: C=1 when A>=B (no borrow), invert 283 carry-out
                carry_out = ~cout_arith;
            end
            ALU_AND: begin
                result    = and_out;
                carry_out = 1'b0;
            end
            ALU_OR: begin
                result    = or_out;
                carry_out = 1'b0;
            end
            ALU_XOR: begin
                result    = xor_out;
                carry_out = 1'b0;
            end
            ALU_NOT: begin
                result    = not_out;
                carry_out = 1'b0;
            end
            ALU_PASS_A: begin
                result    = a;
                carry_out = 1'b0;
            end
            ALU_PASS_B: begin
                result    = b;
                carry_out = 1'b0;
            end
            ALU_INC: begin
                result    = inc_sum;
                carry_out = inc_cout;
            end
            ALU_DEC: begin
                result    = dec_sum;
                carry_out = dec_cout;
            end
            default: begin
                result    = 8'd0;
                carry_out = 1'b0;
            end
        endcase
    end

    assign y    = result;
    assign cout = carry_out;
    assign zero = (result == 8'd0);

endmodule

`default_nettype wire
