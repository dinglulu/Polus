VERSION=1.0.2
RELEASE=20230803

CC  := gcc
BIN := /usr/local/bin
HEADCORE := bsalign

ifeq (0, ${MAKELEVEL})
TIMESTAMP=$(shell date)
endif

ifeq (1, ${AVX2})
SIMD_FLAGS=-mavx2 -mavx
else
SIMD_FLAGS=-msse4.2
endif

# 编译选项，保留你的原本设置，fPIE是默认加的
ifeq (1, ${DEBUG})
CFLAGS=-g3 -W -Wall -Wno-unused-but-set-variable -O0 -DDEBUG=1 -DVERSION="$(VERSION)" -DRELEASE="$(RELEASE)" -D_FILE_OFFSET_BITS=64 -D_GNU_SOURCE -mpopcnt $(SIMD_FLAGS) -fPIE
else
CFLAGS=-g3 -W -Wall -Wno-unused-but-set-variable -O4 -DVERSION="$(VERSION)" -DRELEASE="$(RELEASE)" -D_FILE_OFFSET_BITS=64 -D_GNU_SOURCE -mpopcnt $(SIMD_FLAGS) -fPIE
endif

# 链接选项，强制加 -no-pie，解决 relocation 问题
LDFLAGS=-no-pie

# 需要链接的库
GLIBS=librs.a -lm -lrt -lpthread -lz

# 通用头文件
GENERIC_SRC=$(HEADCORE)/mem_share.h $(HEADCORE)/chararray.h $(HEADCORE)/list.h $(HEADCORE)/pgzf.h $(HEADCORE)/thread.h $(HEADCORE)/filereader.h

# 要生成的程序
PROGS=derrick

# 默认目标
all: $(PROGS)

# 主程序编译规则，加上 $(LDFLAGS)
derrick: $(GENERIC_SRC) derrick.h main.c
	$(CC) $(CFLAGS) -o $@ main.c $(GLIBS) $(LDFLAGS)

# 清理
clean:
	rm -f *.o *.gcda *.gcno *.gcov gmon.out $(PROGS)

clear:
	rm -f *.o *.gcda *.gcno *.gcov gmon.out

# 安装
install: $(PROGS)
	mkdir -p $(BIN) && cp -fvu $(PROGS) $(BIN)
