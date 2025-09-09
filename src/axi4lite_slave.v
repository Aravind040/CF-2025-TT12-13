`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 06.09.2025 15:00:27
// Design Name: 
// Module Name: axi4lite_slave
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


`timescale 1ns / 1ps

module axi4lite_slave #
(
    parameter C_S_AXI_ADDR_WIDTH = 2,
    parameter C_S_AXI_DATA_WIDTH = 8
)
(
    input  wire                          s_axi_aclk,
    input  wire                          s_axi_aresetn,

    // Write address channel
    input  wire [C_S_AXI_ADDR_WIDTH-1:0] s_axi_awaddr,
    input  wire                          s_axi_awvalid,
    output reg                           s_axi_awready,

    // Write data channel
    input  wire [C_S_AXI_DATA_WIDTH-1:0] s_axi_wdata,
    input  wire [C_S_AXI_DATA_WIDTH/8-1:0] s_axi_wstrb,
    input  wire                          s_axi_wvalid,
    output reg                           s_axi_wready,

    // Write response channel
    output reg [1:0]                     s_axi_bresp,
    output reg                           s_axi_bvalid,
    input  wire                          s_axi_bready,

    // Read address channel
    input  wire [C_S_AXI_ADDR_WIDTH-1:0] s_axi_araddr,
    input  wire                          s_axi_arvalid,
    output reg                           s_axi_arready,

    // Read data channel
    output reg [C_S_AXI_DATA_WIDTH-1:0]  s_axi_rdata,
    output reg [1:0]                     s_axi_rresp,
    output reg                           s_axi_rvalid,
    input  wire                          s_axi_rready
);

    // Register file (word addressed)
    reg [C_S_AXI_DATA_WIDTH-1:0] regfile [0:7];  // 256 x 32-bit

    always @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            s_axi_awready <= 0;
            s_axi_wready  <= 0;
            s_axi_bvalid  <= 0;
            s_axi_bresp   <= 2'b00;
            s_axi_arready <= 0;
            s_axi_rvalid  <= 0;
            s_axi_rresp   <= 2'b00;
            s_axi_rdata   <= 0;
        end else begin
            s_axi_awready <= 0;
            s_axi_wready  <= 0;
            s_axi_bvalid  <= 0;
            s_axi_arready <= 0;
            s_axi_rvalid  <= 0;

            // Write transaction
            if (s_axi_awvalid) begin
                s_axi_awready <= 1;
            end
            if (s_axi_wvalid) begin
                s_axi_wready <= 1;
                regfile[s_axi_awaddr[1:0]] <= s_axi_wdata; // word-aligned
                s_axi_bresp  <= 2'b00; // OKAY
                s_axi_bvalid <= 1;
            end

            // Read transaction
            if (s_axi_arvalid) begin
                s_axi_arready <= 1;
                s_axi_rdata   <= regfile[s_axi_araddr[1:0]]; // word-aligned
                s_axi_rresp   <= 2'b00; // OKAY
                s_axi_rvalid  <= 1;
            end
        end
    end

endmodule
