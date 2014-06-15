NAME=uart
PY=.py
V=.v
SRCS=$(NAME)$(PY)

HDL=$(NAME)$(V)
TB=tb_$(NAME)$(V)
VCD = tb_$(NAME).vcd

all:clean
	python $(SRCS)

view:
	gtkwave $(VCD) &

clean:
	rm -f $(HDL) $(TB) $(VCD) *_flymake*
