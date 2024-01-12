// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// The inputs of this program are the values stored in R0
// and R1 (RAM[0] and RAM[1]). The program computes the product
// R0 * R1 and stores the result in R2 (RAM[2]).
// Assume that R0 ≥ 0, R1 ≥ 0, and R0 * R1 < 32768
// (your program need not test these conditions).
// Your code should not change the values of R0 and R1.
// The supplied Multi.test script and Mult.cmp compare file
// are designed to test your program on some representative values.

@0
D=M

// Initialize counter
@c
M=D

// sum = 0
@sum
M=0

// Stop early if R0 less than 0
@0
D=M
@STOP
D;JLE

(LOOP)
	@1
	D=M

	@sum
	M=M+D

	@c
	M=M-1
	D=M

	@LOOP
	D;JGT
(STOP)
	@sum
	D=M
	// R2 = sum
	@2
	M=D
(END)
	@END
	0;JMP
