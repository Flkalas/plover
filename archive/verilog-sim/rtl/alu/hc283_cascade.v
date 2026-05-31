// 74HC283 ×2 cascaded 4-bit adders → 8-bit ripple carry adder
`default_nettype none

module hc283_cascade (
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire       cin,
    output wire [7:0] sum,
    output wire       cout
);

    wire [3:0] sum_lo, sum_hi;
    wire       c_lo;

    hc283_nibble u_lo (
        .a  (a[3:0]),
        .b  (b[3:0]),
        .cin(cin),
        .sum(sum_lo),
        .cout(c_lo)
    );

    hc283_nibble u_hi (
        .a  (a[7:4]),
        .b  (b[7:4]),
        .cin(c_lo),
        .sum(sum_hi),
        .cout(cout)
    );

    assign sum = {sum_hi, sum_lo};

endmodule

module hc283_nibble (
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire       cin,
    output wire [3:0] sum,
    output wire       cout
);
    wire [4:0] tmp = {1'b0, a} + {1'b0, b} + {4'b0, cin};
    assign sum  = tmp[3:0];
    assign cout = tmp[4];
endmodule

`default_nettype wire
