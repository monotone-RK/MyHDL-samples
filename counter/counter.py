#!/usr/bin/env python
# -*- coding: utf-8 -*-

import myhdl

#***** Parameter
#*******************************************************************************
WIDTH = 32                               # Data Width
CLK_FREQ = 100E6                         # 100MHz
CLK_PERIOD = int(1 / CLK_FREQ / (1E-9))  # nano-sec
RST_TIME = 500
HALT_VALUE = 30

#**** Module Declaration
#*******************************************************************************

#**** input
#***************************************
CLK = myhdl.Signal(bool(1))
RST_X = myhdl.Signal(bool(1))

#**** output
#***************************************
VALUE = myhdl.Signal(myhdl.intbv(0)[WIDTH:])


#**** Module
#***************************************
def counter(CLK, RST_X, VALUE):

    cnt = myhdl.Signal(myhdl.intbv(0)[WIDTH:])

    @myhdl.always(CLK.posedge)
    def main_proc():
        if not RST_X:
            cnt.next = 0
        else:
            cnt.next = cnt + 1

    @myhdl.always_comb
    def combination():
        VALUE.next = cnt

    return main_proc, combination


#**** Testbench
#*******************************************************************************
def tb_counter():
    inst = counter(CLK, RST_X, VALUE)

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
            if (VALUE > HALT_VALUE): raise myhdl.StopSimulation
            print "VALUE is %d" % VALUE

    return inst, clkgen, stimulus

tb_cnt = myhdl.traceSignals(tb_counter)  # enable to generate vcd file
sim = myhdl.Simulation(tb_cnt)
sim.run()


#**** Generate Verilog HDL
#*******************************************************************************
myhdl.toVerilog(counter, CLK, RST_X, VALUE)
