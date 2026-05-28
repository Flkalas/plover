`default_nettype none

module sram256 #(
    parameter ADDR_WIDTH = 15,
    parameter DEPTH      = 256  // IS62C256 32K in hardware; 256 enough for RTL sim
) (
    input  wire                  clk,
    input  wire                  we,
    input  wire [ADDR_WIDTH-1:0] addr,
    input  wire [7:0]            din,
    output wire [7:0]            dout
);

    reg [7:0] mem [0:DEPTH-1];

    assign dout = mem[addr];

    always @(posedge clk) begin
        if (we)
            mem[addr] <= din;
    end

endmodule

`default_nettype wire
