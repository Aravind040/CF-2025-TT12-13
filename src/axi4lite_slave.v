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


module axi4lite_slave 
(
    input  wire        s_axi_aclk,
    input  wire        s_axi_aresetn,

    // Write address channel
    input  wire [1:0]  s_axi_awaddr,
    input  wire        s_axi_awvalid,
    output reg         s_axi_awready,

    // Write data channel
    input  wire [7:0]  s_axi_wdata,
    input  wire        s_axi_wstrb,   // 1-bit strobe for whole byte
    input  wire        s_axi_wvalid,
    output reg         s_axi_wready,

    // Write response channel
    output reg [1:0]   s_axi_bresp,
    output reg         s_axi_bvalid,
    input  wire        s_axi_bready,

    // Read address channel
    input  wire [1:0]  s_axi_araddr,
    input  wire        s_axi_arvalid,
    output reg         s_axi_arready,

    // Read data channel
    output reg [7:0]   s_axi_rdata,
    output reg [1:0]   s_axi_rresp,
    output reg         s_axi_rvalid,
    input  wire        s_axi_rready
);

    reg [7:0] regfile [0:3]; // 4 locations (since 2-bit addr)

    reg [1:0] awaddr_reg;
    reg       awvalid_seen;

    always @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            s_axi_awready <= 0;
            s_axi_wready  <= 0;
            s_axi_bvalid  <= 0;
            s_axi_bresp   <= 2'b00;
            s_axi_arready <= 0;
            s_axi_rvalid  <= 0;
            s_axi_rresp   <= 2'b00;
            s_axi_rdata   <= 8'h00;
            awvalid_seen  <= 0;
        end else begin
            // defaults
            s_axi_awready <= 0;
            s_axi_wready  <= 0;
            s_axi_arready <= 0;

            // Capture AW
            if (!awvalid_seen && s_axi_awvalid) begin
                awaddr_reg   <= s_axi_awaddr;
                awvalid_seen <= 1'b1;
                s_axi_awready <= 1'b1;
            end

            // Capture W and commit write
            if (s_axi_wvalid && awvalid_seen) begin
                s_axi_wready <= 1'b1;
                if (s_axi_wstrb) begin
                    regfile[awaddr_reg] <= s_axi_wdata;
                end
                s_axi_bresp  <= 2'b00; // OKAY
                s_axi_bvalid <= 1'b1;
                awvalid_seen <= 1'b0; // done
            end

            // bvalid held until bready
            if (s_axi_bvalid && s_axi_bready)
                s_axi_bvalid <= 1'b0;

            // Read
            if (s_axi_arvalid && !s_axi_rvalid) begin
                s_axi_arready <= 1'b1;
                s_axi_rdata   <= regfile[s_axi_araddr];
                s_axi_rresp   <= 2'b00;
                s_axi_rvalid  <= 1'b1;
            end
            if (s_axi_rvalid && s_axi_rready)
                s_axi_rvalid <= 1'b0;
        end
    end
endmodule
