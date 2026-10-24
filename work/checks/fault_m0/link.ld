MEMORY { flash (rx) : org = 0x00000000, len = 256k  ram (rwx) : org = 0x20000000, len = 16k }
SECTIONS { .text : { KEEP(*(.vectors)) *(.text*) *(.rodata*) } > flash }
