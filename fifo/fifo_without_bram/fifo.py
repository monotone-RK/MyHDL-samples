#!/usr/bin/env python
# -*- coding: utf-8 -*-

import myhdl

#***** Parameter
#*******************************************************************************
# for simulation
CLK_FREQ = 100E6                         # 100MHz
CLK_PERIOD = int(1 / CLK_FREQ / (1E-9))  # nano-sec
RST_TIME = 500
HALT_CYCLE = 30

# for synthesis
WIDTH = 32                               # Data Width
DEPTH = 5
W_CNT = 3
W_POS = 3

#**** Module Declaration
#*******************************************************************************

#**** input
#***************************************
CLK = myhdl.Signal(bool(1))
RST_X = myhdl.Signal(bool(1))
ENQ = myhdl.Signal(bool(1))
DEQ = myhdl.Signal(bool(1))
DIN = myhdl.Signal(myhdl.intbv(0)[WIDTH:])

#**** output
#***************************************
DOUT = myhdl.Signal(myhdl.intbv(0)[WIDTH:])
EMPTY = myhdl.Signal(bool(1))
FULL = myhdl.Signal(bool(1))


#**** Module
#***************************************
def fifo(CLK, RST_X, ENQ, DEQ, DIN, DOUT, EMPTY, FULL):

    # wire
    we = myhdl.Signal(bool(1))
    re = myhdl.Signal(bool(1))

    # reg
    mem = [myhdl.Signal(myhdl.intbv(0)[WIDTH:]) for i in range(DEPTH)]
    cnt = myhdl.Signal(myhdl.intbv(0)[W_CNT:])
    head = myhdl.Signal(myhdl.intbv(0)[W_POS:])
    tail = myhdl.Signal(myhdl.intbv(0)[W_POS:])

    @myhdl.always_comb
    def assign():
        EMPTY.next = (cnt == 0)
        FULL.next = (cnt == DEPTH)
        we.next = (ENQ and (not (cnt == DEPTH)))
        re.next = (DEQ and (not (cnt == 0)))

    @myhdl.always(CLK.posedge)
    def always():
        if not RST_X:
            DOUT.next = 0
            cnt.next = 0
            head.next = 0
            tail.next = 0
        else:
            if we:
                mem[tail].next = DIN
                tail.next = 0 if (tail == DEPTH - 1) else tail + 1
            if re:
                DOUT.next = mem[head]
                head.next = 0 if (head == DEPTH - 1) else head + 1
            else:
                DOUT.next = 0
            if (we and re):
                cnt.next = cnt
            elif we:
                cnt.next = cnt + 1
            elif re:
                cnt.next = cnt - 1

    return assign, always


#**** Testbench
#*******************************************************************************
def tb_fifo():
    inst = fifo(CLK, RST_X, ENQ, DEQ, DIN, DOUT, EMPTY, FULL)
    cycle = myhdl.Signal(myhdl.intbv(0)[WIDTH:])

    @myhdl.always(myhdl.delay(CLK_PERIOD / 2))
    def clkgen():
        CLK.next = not CLK

    @myhdl.always_comb
    def assign():
        ENQ.next = ((cycle < 20) and (not FULL))
        DEQ.next = ((cycle % 2) and (not EMPTY))
        DIN.next = cycle

    @myhdl.always(CLK.posedge)
    def cyclegen():
        if not RST_X:
            cycle.next = 0
        else:
            cycle.next = cycle + 1

    @myhdl.instance
    def stimulus():
        RST_X.next = 0
        yield myhdl.delay(RST_TIME)
        RST_X.next = 1
        while (cycle < HALT_CYCLE):
            yield CLK.posedge
            print "cycle(DIN): %10d DOUT: %10d ENQ: %d DEQ: %d EMPTY %d FULL %d" % (cycle, DOUT, ENQ, DEQ, EMPTY, FULL)
        raise myhdl.StopSimulation

    return inst, clkgen, assign, cyclegen, stimulus

test_fifo = myhdl.traceSignals(tb_fifo)  # enable to generate vcd file
sim = myhdl.Simulation(test_fifo)
sim.run()


#**** Generate Verilog HDL
#*******************************************************************************
myhdl.toVerilog(fifo, CLK, RST_X, ENQ, DEQ, DIN, DOUT, EMPTY, FULL)
