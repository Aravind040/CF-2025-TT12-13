`timescale 1ns / 1ps

module tt_um_axi4lite_top
(
    input  wire                        clk,
    input  wire                        rst_n ,
    input  wire                        ena,

    // Control interface to Master (ui_in mapping below)
    input  wire [7:0]       ui_in,
    input  wire [7:0]       uio_in,
    output wire [7:0]       uio_oe,
    output wire [7:0]       uio_out,
    output wire [7:0]       uo_out
);

    // --- ui_in mapping (consistent, non-overlapping) ---
    // ui_in[1:0] = address (2 bits)
    // ui_in[2]   = start_write (pulse)
    // ui_in[3]   = start_read  (pulse)
    wire [1:0] write_addr  = ui_in[1:0];
    wire [1:0] read_addr   = ui_in[1:0]; // share same addr field for read/write
    wire       start_write = ui_in[2];
    wire       start_read  = ui_in[3];

    // status
    wire       done;

    assign uo_out[0] = done;
    assign uo_out[7:1] = 7'b0;

    // Expose AXI signals for simulation visibility
    wire [1:0] awaddr;
    wire       awvalid;
    wire       awready;
    wire [7:0] wdata;
    wire [0:0] wstrb; // 1-bit strobe
    wire       wvalid;
    wire       wready;
    wire [1:0] bresp;
    wire       bvalid;
    wire       bready;
    wire [1:0] araddr;
    wire       arvalid;
    wire       arready;
    wire [7:0] rdata;
    wire [1:0] rresp;
    wire       rvalid;
    wire       rready;

    // Master instance
    axi4lite_master master_inst (
        .m_axi_aclk    (clk),
        .m_axi_aresetn (rst_n),

        .m_axi_awaddr  (awaddr),
        .m_axi_awvalid (awvalid),
        .m_axi_awready (awready),

        .m_axi_wdata   (wdata),
        .m_axi_wstrb   (wstrb),
        .m_axi_wvalid  (wvalid),
        .m_axi_wready  (wready),

        .m_axi_bresp   (bresp),
        .m_axi_bvalid  (bvalid),
        .m_axi_bready  (bready),

        .m_axi_araddr  (araddr),
        .m_axi_arvalid (arvalid),
        .m_axi_arready (arready),

        .m_axi_rdata   (rdata),
        .m_axi_rresp   (rresp),
        .m_axi_rvalid  (rvalid),
        .m_axi_rready  (rready),

        // User interface
        .start_write   (start_write),
        .write_addr    (write_addr),
        .uio_in        (uio_in),
        .start_read    (start_read),
        .read_addr     (read_addr),
        .read_data     (uio_out),
        .done          (done)
    );

    // Slave instance
    axi4lite_slave slave_inst (
        .s_axi_aclk    (clk),
        .s_axi_aresetn (rst_n),

        .s_axi_awaddr  (awaddr),
        .s_axi_awvalid (awvalid),
        .s_axi_awready (awready),

        .s_axi_wdata   (wdata),
        .s_axi_wstrb   (wstrb),
        .s_axi_wvalid  (wvalid),
        .s_axi_wready  (wready),

        .s_axi_bresp   (bresp),
        .s_axi_bvalid  (bvalid),
        .s_axi_bready  (bready),

        .s_axi_araddr  (araddr),
        .s_axi_arvalid (arvalid),
        .s_axi_arready (arready),

        .s_axi_rdata   (rdata),
        .s_axi_rresp   (rresp),
        .s_axi_rvalid  (rvalid),
        .s_axi_rready  (rready)
    );

    assign uio_oe = 8'hFF;

endmodule
