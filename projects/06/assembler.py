#!/usr/bin/env python3
import argparse

DEST = {
  'M'   : '001',
  'D'   : '010',
  'DM'  : '011',
  'MD'  : '011',
  'A'   : '100',
  'AM'  : '101',
  'MA'  : '101',
  'AD'  : '110',
  'DA'  : '110',
  'ADM' : '111',
  'AMD' : '111',
  'DAM' : '111',
  'DMA' : '111',
  'MAD' : '111',
  'MDA' : '111',
}

JUMP = {
  'JGT' : '001',
  'JEQ' : '010',
  'JGE' : '011',
  'JLT' : '100',
  'JNE' : '101',
  'JLE' : '110',
  'JMP' : '111',
}

COMP = {
  0 : {
    '0'   : '101010',
    '1'   : '111111',
    '-1'  : '111010',
    'D'   : '001100',
    'A'   : '110000',
    '!D'  : '001101',
    '!A'  : '110001',
    '-D'  : '001111',
    '-A'  : '110011',
    'D+1' : '011111',
    'A+1' : '110111',
    'D-1' : '001110',
    'A-1' : '110010',
    'D+A' : '000010',
    'D-A' : '010011',
    'A-D' : '000111',
    'D&A' : '000000',
    'D|A' : '010101',
  },
  1 : {
    'M'   : '110000',
    '!M'  : '110001',
    '-M'  : '110011',
    'M+1' : '110111',
    'M-1' : '110010',
    'D+M' : '000010',
    'D-M' : '010011',
    'M-D' : '000111',
    'D&M' : '000000',
    'D|M' : '010101',
  }
}

PREDEF_SYMBOLS = {
  'R0'     : 0,
  'R1'     : 1,
  'R2'     : 2,
  'R3'     : 3,
  'R4'     : 4,
  'R5'     : 5,
  'R6'     : 6,
  'R7'     : 7,
  'R8'     : 8,
  'R9'     : 9,
  'R10'    : 10,
  'R11'    : 11,
  'R12'    : 12,
  'R13'    : 13,
  'R14'    : 14,
  'R15'    : 15,
  'SCREEN' : 16384,
  'KBD'    : 24576,
  'SP'     : 0,
  'LCL'    : 1,
  'ARG'    : 2,
  'THIS'   : 3,
  'THAT'   : 4,
}

def is_blank(line):
  return line == ''

def is_comment(line):
  return len(line) > 2 and line[0]=='/' and line[1]=='/'

def is_label(line):
  return '(' in line and ')' in line

def parse_a_instruction(data):
  return ('0'+('0'*(15-int(data).bit_length()))+bin(int(data)).lstrip('-0b'))

def assemble(file_path,output_file):
  buffer = []
  cache = {}
  goto_map = {}
  slot = 16
  abs_index = 0

  # Generate goto_map
  with open(file_path, 'r') as f:
    for line in f:
      line = line.strip('\n').strip()
      if is_blank(line) or is_comment(line):
        continue
      if is_label(line):
        goto_map[line.strip('(').strip(')').strip()] = abs_index
        continue
      abs_index+=1

  # Generate final machine code
  with open(file_path, 'r') as f:
    for line in f:
      line = line.strip('\n').strip()
      instruction = ''

      if is_blank(line) or is_comment(line) or is_label(line):
        continue
      elif line in cache:
        buffer.append(cache[line])
        continue
      elif line[0] == '@':
        var = line[1:]
        if str.isdigit(var[0]):
          instruction = parse_a_instruction(var)
        elif var in PREDEF_SYMBOLS:
          instruction = parse_a_instruction(PREDEF_SYMBOLS[var])
        elif var in goto_map:
          instruction = parse_a_instruction(goto_map[var])
        else:
          instruction = parse_a_instruction(slot)
          slot += 1
      else:
        dst = '000' if '=' not in line else DEST[line.split('=')[0].strip()]
        RHS = line.split('=')[1] if '=' in line else line
        jmp = JUMP[RHS.split(';')[-1].strip()] if ';' in line else '000'
        a = 1 if 'M' in RHS.split(';')[0].strip() else 0
        c_bits = COMP[a][RHS.split(';')[0].strip()]
        instruction = '111' + str(a) + c_bits + dst + jmp

      buffer.append(instruction)
      cache[line]=instruction

    with open(output_file, 'w') as f:
      f.writelines(line + '\n' for line in buffer)

def main():
  parser = argparse.ArgumentParser(description='Assembles Hack assembly')
  parser.add_argument('--f', help='File to assemble')
  parser.add_argument('--o', help='Name of output file')

  arg_dict = parser.parse_args()
  file_path = arg_dict.f
  output_file = arg_dict.o

  assemble(file_path,output_file)

if __name__ == '__main__':
  main()
