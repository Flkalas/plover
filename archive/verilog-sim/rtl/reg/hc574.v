`default_nettype none

module hc574 (
    input  wire       clk,
    input  wire       we,
    input  wire [7:0] d,
    output reg  [7:0] q
);
    initial q = 8'd0;
    always @(posedge clk) begin
        if (we)
            q <= d;
    end
endmodule

`default_nettype wire
