# "ptch" instead of "patch", b/c Windows assumes files with "patch" in the name
# should be run as administrator.
OUTPUT = run_ptch_client.exe

# A 32-bit Windows executable should be the output regardless of build system.
CC =  i686-w64-mingw32-gcc

# Build the executable
all: run_patch_client.c
	$(CC) -o $(OUTPUT) run_patch_client.c -lkernel32 -static-libgcc -s

clean:
	rm  $(OUTPUT)
