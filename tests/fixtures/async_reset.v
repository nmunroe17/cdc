module async_reset_example (
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    output reg  state
);
    reg rst_sync;

    always @(negedge rst_n or posedge clk) begin
        if (!rst_n) begin
            rst_sync <= 1'b0;
        end else begin
            rst_sync <= start;
        end
    end

    always @(posedge clk) begin
        state <= rst_sync;
    end
endmodule
