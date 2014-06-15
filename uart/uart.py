#!/usr/bin/env python
# -*- coding: utf-8 -*-

import myhdl

#***** Parameter
#*******************************************************************************
# for simulation
CLK_FREQ = 100E6                         # 100MHz
CLK_PERIOD = int(1 / CLK_FREQ / (1E-9))  # nano-sec
RST_TIME = 500

# for synthesis
SERIAL_WCNT = 100  # 100MHz/1M baud, parameter for UartRx and UartTx
SS_SER_WAIT = 0    # Do not modify this. RS232C deserializer, State WAIT
SS_SER_RCV0 = 1    # Do not modify this. RS232C deserializer, State Receive0
SS_SER_DONE = 9    # Do not modify this. RS232C deserializer, State DONE

#**** Module Declaration
#*******************************************************************************

#**** input
#***************************************
CLK = myhdl.Signal(bool(1))
RST_X = myhdl.Signal(bool(1))
RXD = myhdl.Signal(bool(1))  # RS232C input

#**** output
#***************************************
DOUT = myhdl.Signal(myhdl.intbv(0)[8:])  # 8bit output data
EN = myhdl.Signal(bool(1))               # 8bit output data enable


#**** Module
#***************************************
def uartRx(CLK, RST_X, RXD, DOUT, EN):

    # reg
    stage = myhdl.Signal(myhdl.intbv(0)[4:])
    cnt = myhdl.Signal(myhdl.intbv(0)[21:])                  # counter to latch D0, D1, ..., D7
    cnt_detect_startbit = myhdl.Signal(myhdl.intbv(0)[20:])  # counter to detect the Start Bit

    @myhdl.always_comb
    def assign():
        EN.next = (stage == SS_SER_DONE)

    @myhdl.always(CLK.posedge)
    def detect_startbit():
        if not RST_X:
            cnt_detect_startbit.next = 0
        else:
            cnt_detect_startbit.next = 0 if (RXD) else cnt_detect_startbit + 1

    @myhdl.always(CLK.posedge)
    def main_proc():
        if not RST_X:
            stage.next = SS_SER_WAIT
            cnt.next = 1
            DOUT.next = 0
        elif (stage == SS_SER_WAIT):
            stage.next = SS_SER_RCV0 if (cnt_detect_startbit == (SERIAL_WCNT >> 1)) else stage
        else:
            if (cnt != SERIAL_WCNT):
                cnt.next = cnt + 1
            else:
                stage.next = SS_SER_WAIT if (stage == SS_SER_DONE) else stage + 1
                DOUT.next = myhdl.ConcatSignal(RXD, DOUT[8:1])
                cnt.next = 1

    return assign, detect_startbit, main_proc

#**** Module Declaration
#*******************************************************************************

#**** input
#***************************************
CLK = myhdl.Signal(bool(1))
RST_X = myhdl.Signal(bool(1))
WE = myhdl.Signal(bool(1))
DIN = myhdl.Signal(myhdl.intbv(0)[8:])

#**** output
#***************************************
TXD = myhdl.Signal(bool(1))
READY = myhdl.Signal(bool(1))


#**** Module
#***************************************
def uartTx(CLK, RST_X, WE, DIN, TXD, READY):

    # reg
    cmd = myhdl.Signal(myhdl.intbv(0)[9:])
    waitnum = myhdl.Signal(myhdl.intbv(0)[12:])
    cnt = myhdl.Signal(myhdl.intbv(0)[4:])
    ready = myhdl.Signal(bool(1))
    startbit = myhdl.Signal(bool(1))
    stopbit = myhdl.Signal(bool(1))

    @myhdl.always_comb
    def assign():
        READY.next = ready
        startbit.next = 0
        stopbit.next = 1

    @myhdl.always(CLK.posedge)
    def main_proc():
        if not RST_X:
            TXD.next = 1
            ready.next = 1
            cmd.next = 0x1ff
            waitnum.next = 0
            cnt.next = 0
        elif (ready):
            TXD.next = 1
            waitnum.next = 0
            if (WE):
                ready.next = 0
                cmd.next = myhdl.ConcatSignal(DIN, startbit)  # set start bit
                # cmd.next = myhdl.concat(DIN, False)  # set start bit
                cnt.next = 10
        elif (waitnum >= SERIAL_WCNT):
            TXD.next = cmd[0]
            ready.next = (cnt == 1)
            cmd.next = myhdl.ConcatSignal(stopbit, cmd[9:1])
            # cmd.next = myhdl.concat(True, cmd[9:1])
            waitnum.next = 1
            cnt.next = cnt - 1
        else:
            waitnum.next = waitnum + 1

    return assign, main_proc


POSITION = myhdl.Signal(bool(1))


def main(CLK, RST_X, RXD, TXD, POSITION):

    # wire
    send_data = myhdl.Signal(myhdl.intbv(0)[8:])
    ready = myhdl.Signal(bool(1))
    recv_data = myhdl.Signal(myhdl.intbv(0)[8:])
    en = myhdl.Signal(bool(1))

    # reg
    we = myhdl.Signal(bool(1))
    init_left = myhdl.Signal(bool(1))
    init_done = myhdl.Signal(bool(1))

    # module instance
    send = uartTx(CLK, RST_X, we, send_data, TXD, ready)
    recv = uartRx(CLK, RST_X, RXD, recv_data, en)

    @myhdl.always_comb
    def assign():
        if ((not init_done) and we):
            send_data.next = 0x61
        elif (we):
            send_data.next = recv_data + 1
        else:
            send_data.next = 0

    @myhdl.always(CLK.posedge)
    def logic():
        if not RST_X:
            we.next = 0
            init_left.next = 0
            init_done.next = 0
        elif (POSITION == 0 and (not init_left)):
            we.next = 1
            init_left.next = 1
        else:
            if not init_done: init_done.next = 1
            if (recv_data == 0x7a): raise myhdl.StopSimulation
            we.next = (en and (not we) and ready)
            if (we):
                print "send data %x from" % send_data,
                if (POSITION == 0): print "left"
                if (POSITION == 1): print "right"

    return send, recv, assign, logic


#**** Testbench
#*******************************************************************************
def tb_uart():
    left_tx = myhdl.Signal(bool(1))
    left_rx = myhdl.Signal(bool(1))
    right_tx = myhdl.Signal(bool(1))
    right_rx = myhdl.Signal(bool(1))

    left = main(CLK, RST_X, left_rx, left_tx, 0)
    right = main(CLK, RST_X, right_rx, right_tx, 1)

    @myhdl.always_comb
    def assign():
        right_rx.next = left_tx
        left_rx.next = right_tx

    @myhdl.always(myhdl.delay(CLK_PERIOD / 2))
    def clkgen():
        CLK.next = not CLK

    @myhdl.instance
    def stimulus():
        RST_X.next = 0
        yield myhdl.delay(RST_TIME)
        RST_X.next = 1
        while (1):
            yield CLK.posedge

    return left, right, assign, clkgen, stimulus

test_uart = myhdl.traceSignals(tb_uart)  # enable to generate vcd file
sim = myhdl.Simulation(test_uart)
sim.run()


#**** Generate Verilog HDL
#*******************************************************************************
#myhdl.toVerilog(uartTx, CLK, RST_X, WE, DIN, TXD, READY)
