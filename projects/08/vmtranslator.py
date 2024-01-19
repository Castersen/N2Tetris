#!/usr/bin/env python3
import argparse
from pathlib import Path

GENERIC_TRANSLATION = {
  'local': 'LCL',
  'argument': 'ARG',
  'this': 'THIS',
  'that': 'THAT',
  'pointer': '3',
  'temp': '5',
}

BINARY_OPS = {
  'add': 'D+A',
  'sub': 'A-D',
  'and': 'D&A',
  'or': 'D|A',
}

UNARY_OPS = {
  'not': '!D',
  'neg': '-D',
}

LOGICAL_OPS = {
  'eq': 'JEQ',
  'gt': 'JGT',
  'lt': 'JLT',
}

class LabelValue:
  def __init__(self):
    self.label_id = 0

  def get_label(self):
    self.label_id += 1
    return str(self.label_id)

def is_blank(line):
  return line == ''

def is_comment(line):
  return len(line) > 2 and line[0] == '/' and line[1] == '/'

def format_comment(line):
  return '// ' + line

def binary_op(c):
  return ['@SP', 'M=M-1', '@SP', 'A=M', 'D=M', '@SP', 'M=M-1', '@SP', 'A=M', 'A=M', 'D=' + c, '@SP',
            'A=M', 'M=D', '@SP', 'M=M+1']

def unary_op(c):
  return ['@SP', 'M=M-1', '@SP', 'A=M', 'D=M', 'D=' + c, '@SP', 'A=M', 'M=D', '@SP', 'M=M+1']

def logical_op(c, label_id):
  ll = '(JL' + label_id + ')'
  return ['@SP', 'M=M-1', '@SP', 'A=M', 'D=M', '@SP', 'M=M-1', '@SP', 'A=M', 'A=M', 'D=A-D', '@SP',
                          'A=M', 'M=-1', '@JL' + label_id, 'D;' + c, '@SP', 'A=M', 'M=0', ll, '@SP', 'M=M+1']

def call(fn, nArgs, label_id):
  ll = '(L' + label_id + ')'
  i_buffer = []

  i_buffer += ['@L' + label_id, 'D=A', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1'] # push return address
  i_buffer += ['@LCL', 'D=M', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1'] # push LCL
  i_buffer += ['@ARG', 'D=M', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1'] # push ARG
  i_buffer += ['@THIS', 'D=M', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1'] # push THIS
  i_buffer += ['@THAT', 'D=M', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1'] # push THAT
  i_buffer += ['@SP', 'D=M', '@LCL', 'M=D', '@5', 'D=D-A', '@' + nArgs, 'D=D-A', '@ARG', 'M=D'] # reposition LCL
  i_buffer += ['@' + fn, '0;JMP'] # goto function
  i_buffer += [ll] # add return label

  return i_buffer

def translate(file_path, generate_comments, label_value):
  buffer = []
  static_label = str(file_path).split('/')[-1]
  buffer.append('// File: ' + str(file_path).split('/')[-1]) if generate_comments else None

  with open(file_path, 'r') as f:
    for line in f:
      line = line.strip('\n').strip()
      instruction_buffer = []

      if is_blank(line) or is_comment(line):
        continue
      line = line.split('//')[0].strip() # Remove any trailing comments

      if 'push' in line:
        push, segment, value = line.split()
        a = '@' + value
        if segment == 'constant':
          instruction_buffer = [a, 'D=A', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1']
        elif segment in ['local', 'argument', 'this', 'that']:
            v = '@' + GENERIC_TRANSLATION[segment]
            instruction_buffer = [a, 'D=A', v, 'A=M', 'A=D+A', 'D=M', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1']
        elif segment == 'static':
          v = '@' + static_label + '.' + value
          instruction_buffer = [v, 'D=M', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1']
        elif segment == 'temp' or segment == 'pointer':
          v = '@' + GENERIC_TRANSLATION[segment]
          instruction_buffer = [a, 'D=A', v, 'A=D+A', 'D=M', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1']
      elif 'pop' in line:
        pop, segment, value = line.split()
        a = '@' + value
        v = '@' + static_label + '.' + value if segment == 'static' else '@' + GENERIC_TRANSLATION[segment]
        if segment in ['local', 'argument', 'this', 'that']:
          instruction_buffer = ['@SP', 'M=M-1', a, 'D=A', v, 'A=M', 'D=D+A', '@R13', 'M=D', '@SP', 'A=M', 'D=M',
                                  '@R13', 'A=M', 'M=D']
        elif segment == 'static':
          instruction_buffer = [v, 'D=A', '@R13', 'M=D', '@SP', 'AM=M-1', 'D=M', '@R13', 'A=M', 'M=D']
        else:
          instruction_buffer = ['@SP', 'M=M-1', a, 'D=A', v, 'D=D+A', '@R13', 'M=D', '@SP', 'A=M', 'D=M',
                                  '@R13', 'A=M', 'M=D']
      elif line.split()[0] in ['label', 'goto', 'if-goto']:
        v,d = line.split()
        if v == 'label':
          instruction_buffer = ['(' + d + ')']
        elif v == 'goto':
          instruction_buffer = ['@' + d, '0;JMP']
        elif v == 'if-goto':
          instruction_buffer = ['@SP', 'M=M-1', 'A=M', 'D=M', '@' + d, 'D;JNE']
      elif line.split()[0] in ['function', 'call']:
        c,fn,nArgs = line.split()
        if c == 'call':
          instruction_buffer = call(fn, nArgs, label_value.get_label())
        if c == 'function':
          a = '@0'
          const_instruction = [a, 'D=A', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1']
          instruction_buffer = ['(' + fn + ')']
          for ci in range(int(nArgs)):
            instruction_buffer.append(format_comment('push const 0')) if generate_comments else None
            instruction_buffer += const_instruction
      elif line.split()[0] == 'return':
        instruction_buffer = ['@LCL', 'D=M', '@R13', 'M=D', '@5', 'A=D-A', 'D=M', '@R14', 'M=D',
                              '@SP', 'AM=M-1', 'D=M', '@ARG', 'A=M', 'M=D',
                              '@ARG', 'D=M+1', '@SP', 'M=D',
                              '@R13', 'AM=M-1', 'D=M', '@THAT', 'M=D',
                              '@R13', 'AM=M-1', 'D=M', '@THIS', 'M=D',
                              '@R13', 'AM=M-1', 'D=M', '@ARG', 'M=D',
                              '@R13', 'AM=M-1', 'D=M', '@LCL', 'M=D',
                              '@R14', 'A=M', '0;JMP']
      else:
        c = line
        if c in BINARY_OPS:
          instruction_buffer = binary_op(BINARY_OPS[c])
        elif c in UNARY_OPS:
          instruction_buffer = unary_op(UNARY_OPS[c])
        elif c in LOGICAL_OPS:
          instruction_buffer = logical_op(LOGICAL_OPS[c], label_value.get_label())

      buffer.append(format_comment(line)) if generate_comments else None
      buffer += instruction_buffer

    return buffer

def main():
  parser = argparse.ArgumentParser(description='Translates VM code into Hack assembly')
  parser.add_argument('--f', help='VM code (.vm) or folder containing VM code to translate into Hack assembly')
  parser.add_argument('--o', help='Hack assembly output file')
  parser.add_argument('-c', '--comments', help='Add comments', action='store_true')
  parser.add_argument('-b', '--bootstrap', help='Generate bootstrap assembly', action='store_true')

  args = parser.parse_args()
  file_path = Path(args.f)
  output_file = args.o
  generate_comments = args.comments

  candidates = [file_path] if not file_path.is_dir() else [file for file in file_path.glob('*.vm')]

  label_value = LabelValue()
  buffer = []

  if args.bootstrap:
    buffer = ['// Bootstrap', '@256', 'D=A', '@SP', 'M=D']
    buffer = buffer if generate_comments else buffer[1:]
    buffer.append(format_comment('Call Sys.init')) if generate_comments else None
    buffer += call('Sys.init', '0', label_value.get_label())

  for fp in candidates:
    buffer += translate(fp, generate_comments, label_value)

  with open(output_file, 'w') as f:
    f.writelines(line + '\n' for line in buffer)

if __name__ == '__main__':
  main()
