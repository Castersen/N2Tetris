#!/usr/bin/env python3
import argparse

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

def is_blank(line):
  return line == ''

def is_comment(line):
  return len(line) > 2 and line[0] == '/' and line[1] == '/'

def format_comment(line):
  return '// ' + line

def binary_op(c):
  v = 'D=' + c
  return ['@SP', 'M=M-1', '@SP', 'A=M', 'D=M', '@SP', 'M=M-1', '@SP', 'A=M', 'A=M', v, '@SP',
            'A=M', 'M=D', '@SP', 'M=M+1']

def unary_op(c):
  v = 'D=' + c
  return ['@SP', 'M=M-1', '@SP', 'A=M', 'D=M', v, '@SP', 'A=M', 'M=D', '@SP', 'M=M+1']

def logical_op(c, ABS):
  label = 'JL' + str(ABS)
  goto_label = '@' + label
  ji = 'D;' + c
  ll = '(' + label + ')'
  instruction_buffer = ['@SP', 'M=M-1', '@SP', 'A=M', 'D=M', '@SP', 'M=M-1', '@SP', 'A=M', 'A=M', 'D=A-D', '@SP',
                          'A=M', 'M=-1', goto_label, ji, '@SP', 'A=M', 'M=0', ll, '@SP', 'M=M+1']
  return instruction_buffer

def translate(file_path, output_file, generate_comments):
  ABS = 1
  buffer = []
  cache = {}
  static_label = file_path.split('/')[-1]

  with open(file_path, 'r') as f:
    for line in f:
      line = line.strip('\n').strip()
      instruction_buffer = []

      if is_blank(line) or is_comment(line):
        continue
      elif line in cache and line.split()[-1] not in ['eq', 'gt', 'lt']:
        buffer.append(format_comment(line)) if generate_comments else None
        buffer += cache[line]
        continue
      elif 'push' in line:
        push, segment, value = line.split()
        a = '@' + value
        if segment == 'constant':
          instruction_buffer = [a, 'D=A', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1']
        elif segment in ['local', 'argument', 'this', 'that']:
            v = '@' + GENERIC_TRANSLATION[segment]
            instruction_buffer = [a, 'D=A', v, 'A=M', 'A=D+A', 'D=M', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1']
        elif segment == 'static':
          v = '@' + static_label + '.' + value
          instruction_buffer = [a, 'D=A', v, 'A=D+A', 'D=M', '@SP', 'A=M', 'M=D', '@SP', 'M=M+1']
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
        else:
          instruction_buffer = ['@SP', 'M=M-1', a, 'D=A', v, 'D=D+A', '@R13', 'M=D', '@SP', 'A=M', 'D=M',
                                  '@R13', 'A=M', 'M=D']
      else:
        c = line
        if c in BINARY_OPS:
          instruction_buffer = binary_op(BINARY_OPS[c])
        elif c in UNARY_OPS:
          instruction_buffer = unary_op(UNARY_OPS[c])
        elif c in LOGICAL_OPS:
          instruction_buffer = logical_op(LOGICAL_OPS[c], ABS)
          ABS+=1

      buffer.append(format_comment(line)) if generate_comments else None
      buffer += instruction_buffer
      cache[line] = instruction_buffer

    with open(output_file, 'w') as f:
      f.writelines(line + '\n' for line in buffer)

def main():
  parser = argparse.ArgumentParser(description='Translates VM code into Hack assembly')
  parser.add_argument('--f', help='VM code to translate into Hack assembly')
  parser.add_argument('--o', help='Hack assembly output file')
  parser.add_argument('-c', '--comments', help='Add comments', action='store_true')

  args = parser.parse_args()
  file_path = args.f
  output_file = args.o
  generate_comments = True if args.comments else False

  translate(file_path, output_file, generate_comments)

if __name__ == '__main__':
  main()
