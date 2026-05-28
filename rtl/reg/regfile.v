`default_nettype none

module regfile #(
    parameter REG_COUNT = 7
) (
    input  wire       clk,
    input  wire [2:0] rd_idx,
    input  wire [2:0] wr_idx,
    input  wire       wr_en,
    input  wire [7:0] wr_data,
    output wire [7:0] rd_data,
    output wire [7:0] q0,
    output wire [7:0] q1,
    output wire [7:0] q2,
    output wire [7:0] q3,
    output wire [7:0] q4,
    output wire [7:0] q5,
    output wire [7:0] q6
);

    wire [7:0] q [0:REG_COUNT-1];
    genvar i;
    generate
        for (i = 0; i < REG_COUNT; i = i + 1) begin : regs
            hc574 u (
                .clk(clk),
                .we (wr_en && (wr_idx == i[2:0])),
                .d  (wr_data),
                .q  (q[i])
            );
        end
    endgenerate

    assign rd_data = q[rd_idx];
    assign q0 = q[0];
    assign q1 = q[1];
    assign q2 = q[2];
    assign q3 = q[3];
    assign q4 = q[4];
    assign q5 = q[5];
    assign q6 = q[6];

endmodule

`default_nettype wire
