// 74HC153 dual 4-to-1 multiplexer (behavioral)
`default_nettype none

module hc153_mux4 (
    input  wire [3:0] d0,
    input  wire [3:0] d1,
    input  wire [3:0] d2,
    input  wire [3:0] d3,
    input  wire [1:0] sel,
    output wire [3:0] y
);
    assign y = (sel == 2'd0) ? d0 :
               (sel == 2'd1) ? d1 :
               (sel == 2'd2) ? d2 : d3;
endmodule

`default_nettype wire
