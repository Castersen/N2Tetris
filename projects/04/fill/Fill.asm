// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen
// by writing 'black' in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen by writing
// 'white' in every pixel;
// the screen should remain fully clear as long as no key is pressed.

@8191 // Last screen register offset
D=A

@l
M=D

@c
M=0

(LOOP)
	@KBD
	D=M

	@WHITE
	D;JEQ // If key is not being pressed D equals 0

	(BLACK)
		@c
		D=M

		@SCREEN
		A=A+D
		M=-1

		@CONTINUE
		0;JMP

	(WHITE)
		@c
		D=M

		@SCREEN
		A=A+D
		M=0

	(CONTINUE)
		@l
		D=M
		@c
		D=D-M
		@RESET
		D;JEQ

		@c
		M=M+1

		@LOOP
		0;JMP

(RESET)
	@c
	M=0

	@LOOP
	0;JMP
