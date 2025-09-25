module vector_sync (
    input  wire clk,
    input  wire async_in,
    output reg  [1:0] sync
);

    always @(posedge clk) begin
        sync <= {sync[0], async_in};
    end

endmodule
