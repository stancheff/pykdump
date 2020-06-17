# Compiling kernel modules for testing our API
obj-m   += testmod.o
KDIR        := /lib/modules/$(shell uname -r)/build
DBGSYM      := /usr/lib/debug/boot/vmlinux-$(shell uname -r)
PWD         := $(shell pwd)

all:
	$(MAKE) CC='gcc -g' -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

run:
	-rmmod testmod
	insmod ./testmod.ko
	crash64 $(DBGSYM)
