#!/usr/bin/env python3
import argparse
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import string

ARGUMENT = 'argument'
LOCAL = 'local'
CONSTANT = 'constant'
TEMP = 'temp'
ARRAY = 'Array'
MAIN = 'main'
NEW = 'new'
POINTER = 'pointer'
MEMORY_ALLOC = 'Memory.alloc'
METHOD = 'method'
CONSTRUCTOR = 'constructor'
FUNCTION = 'function'
STATIC = 'static'
FIELD = 'field'
INT = 'int'
CHAR = 'char'
BOOLEAN = 'boolean'
VOID = 'void'
THIS = 'this'
TRUE = 'true'
FALSE = 'false'
NULL = 'null'

FIELD_CONV = {'field': 'this'}

KEYWORDS = {'class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char', 
            'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while', 
            'return'}

SYMBOLS = {'{', '}', '|', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', 
           '<', '>', '=', '~'}

INT_RANGE = range(0,32767)

OP_CONV = {'+': 'add', '-': 'sub', '&': 'and', '|': 'or', '<': 'lt',
            '>': 'gt', '=': 'eq', '*': 'call Math.multiply 2', '/': 'call Math.divide 2'}
UNARY_OP_CONV = {'-': 'neg', '~': 'not'}

CONST_CONV = {'true': 'constant', 'false': 'constant', 'null': 'constant', 'this': 'pointer'}
INDEX_CONV = {'true': '1', 'false': '0', 'null': '0', 'this': '0'}

class LexicalLabels(Enum):
  KEYWORD = 'keyword'
  SYMBOL = 'symbol'
  INT_CONST = 'integerConstant'
  STR_CONST = 'stringConstant'
  IDENTIFIER = 'identifier'

  def __str__(self):
    return self.value

class LabelValue:
  def __init__(self):
    self.value = 0

  @property
  def get_value(self):
    self.value += 1
    return self.value

class Tokenizer:
  def __init__(self, file_path):
    self.tokens = tokenize(file_path)
    self.index = 0

  def advance(self):
    self.index += 1 

  @property
  def token_type(self):
    token = self.current_token
    if token in KEYWORDS: return LexicalLabels.KEYWORD
    elif token in SYMBOLS: return LexicalLabels.SYMBOL
    elif token[0] in string.digits and int(token) in INT_RANGE: return LexicalLabels.INT_CONST
    elif token[0] == '"' and token[-1] == '"': return LexicalLabels.STR_CONST
    else: return LexicalLabels.IDENTIFIER

  @property
  def current_token(self):
    return self.tokens[self.index]

@dataclass
class SymbolData:
  type_of: str
  kind: str
  index: int

class SymbolTable:
  def __init__(self):
    self.symbol_table: dict[str, SymbolData] = {}
    self.kind_id = {}
    self.num_of_fields = 0

  def add(self, name: str, type_of: str, kind: str):
    index = self.__kind_lookup(kind)
    if kind == FIELD: self.num_of_fields += 1
    self.symbol_table[name] = SymbolData(type_of, kind, index)

  def __kind_lookup(self, kind: str) -> int:
    self.kind_id[kind] = 0 if kind not in self.kind_id else self.kind_id[kind] + 1
    return self.kind_id[kind]

  def reset(self):
    self.symbol_table = {}; self.kind_id = {}

  def get_symbol(self, name: str) -> None | SymbolData:
    return self.symbol_table.get(name)

class CompilationEngine:
  def __init__(self, jack_tokenizer: Tokenizer, label_value: LabelValue):
    self.tokenizer = jack_tokenizer
    self.label_value = label_value
    self.cst = SymbolTable()
    self.sst = SymbolTable()
    self.buffer = []
    self.class_name = ''

  @property
  def current_token(self):
    return self.tokenizer.current_token

  @property
  def token_type(self):
    return self.tokenizer.token_type

  def __process_st_kind(self, expected_token):
    if self.current_token != expected_token:
      raise Exception(f'Token {expected_token} did not match current token {self.current_token}')
    self.tokenizer.advance()
    return expected_token

  def __process_st_type(self, expected_tokens: list[str], fallback: LexicalLabels = None):
    if self.current_token not in expected_tokens and self.token_type != fallback:
      raise Exception(f'Token {self.current_token} of type {self.token_type} not in {expected_tokens} or {fallback}')
    token = self.current_token
    self.tokenizer.advance()
    return token

  def __process_st_name(self, expected_type: LexicalLabels):
    if self.token_type != expected_type:
      raise Exception(f'Token type {self.token_type} does not match {expected_type}')
    token = self.current_token
    self.tokenizer.advance()
    return token

  def __process_token(self, expected_token):
    if self.current_token != expected_token:
      raise Exception(f'Token {expected_token} did not match current token {self.current_token}')
    self.tokenizer.advance()

  def __process_type(self, expected_type: LexicalLabels):
    if self.token_type != expected_type:
      raise Exception(f'Token type {self.token_type} does not match {expected_type}')
    self.tokenizer.advance()

  def __process_list(self, expected_tokens: list[str], fallback: LexicalLabels = None):
    if self.current_token not in expected_tokens and self.token_type != fallback:
      raise Exception(f'Token {self.current_token} of type {self.token_type} not in {expected_tokens} or {fallback}')
    self.tokenizer.advance()

  def __lookup(self, name: str) -> SymbolData:
    s_data = self.cst.get_symbol(name) if name in self.cst.symbol_table else self.sst.get_symbol(name)
    if s_data is None:
      raise Exception(f'Symbol {name} was not found in either symbol table')
    return s_data

  def __is_in_symbol_table(self, name: str) -> bool:
    return True if name in self.cst.symbol_table or name in self.sst.symbol_table else False

  def __write_pop(self, segment: str, index: int):
    segment = FIELD_CONV[segment] if segment in FIELD_CONV else segment
    self.buffer.append(f'pop {segment} {index}')

  def __write_push(self, segment: str, index: int):
    segment = FIELD_CONV[segment] if segment in FIELD_CONV else segment
    self.buffer.append(f'push {segment} {index}')

  def __write_arithmetic(self, command: str):
    self.buffer.append(command)

  def __write_label(self, label: str):
    self.buffer.append(f'label {label}')

  def __write_goto(self, label: str):
    self.buffer.append(f'goto {label}')

  def __write_if(self, label: str):
    self.buffer.append(f'if-goto {label}')

  def __write_call(self, name: str, n_args: int):
    self.buffer.append(f'call {name} {n_args}')

  def __write_function(self, name: str, n_args):
    self.buffer.append(f'function {name} {n_args}')

  def __write_return(self):
    self.buffer.append('return')

  def __generate_label(self):
    return f'L{self.label_value.get_value}'

  def compile_class(self):
    self.__process_token('class')
    self.class_name = self.current_token
    self.__process_type(LexicalLabels.IDENTIFIER)
    self.__process_token('{')
    while self.current_token in [STATIC, FIELD]:
      self.__compile_class_var_dec()
    while self.current_token in [VOID, FUNCTION, METHOD]:
      self.sst.reset()
      self.__compile_subroutine_dec()
    self.__process_token('}')

  def __compile_class_var_dec(self):
    s_kind = self.__process_st_kind(STATIC) if self.current_token == STATIC else self.__process_st_kind(FIELD)
    s_type = self.__process_st_type([INT, CHAR, BOOLEAN], LexicalLabels.IDENTIFIER)
    s_name = self.__process_st_name(LexicalLabels.IDENTIFIER)
    self.cst.add(s_name, s_type, s_kind)
    while self.current_token != ';':
      self.__process_token(',')
      s_name = self.__process_st_name(LexicalLabels.IDENTIFIER)
      self.cst.add(s_name, s_type, s_kind)
    self.__process_token(';')

  def __compile_subroutine_dec(self):
    fn_type = self.current_token
    self.__process_list([VOID, FUNCTION, METHOD])
    self.__process_list([INT, CHAR, BOOLEAN, VOID], LexicalLabels.IDENTIFIER)
    fn_name = self.current_token
    if fn_name == MAIN or fn_type == METHOD: self.sst.add(THIS, self.class_name, ARGUMENT)
    self.__process_type(LexicalLabels.IDENTIFIER)
    self.__process_token('(')
    self.__compile_parameter_list()
    self.__process_token(')')
    self.__compile_subroutine_body(fn_name, fn_type)

  def __compile_parameter_list(self):
    if self.current_token != ')':
      s_type = self.__process_st_type([INT, CHAR, BOOLEAN], LexicalLabels.IDENTIFIER)
      s_name = self.__process_st_name(LexicalLabels.IDENTIFIER)
      s_kind = ARGUMENT
      self.sst.add(s_name, s_type, s_kind)
      while self.current_token == ',':
        self.__process_token(',')
        s_type = self.__process_st_type([INT, CHAR, BOOLEAN], LexicalLabels.IDENTIFIER)
        s_name = self.__process_st_name(LexicalLabels.IDENTIFIER)
        self.sst.add(s_name, s_type, s_kind)

  def __compile_subroutine_body(self, fn_name: str, fn_type):
    n_vars = 0
    self.__process_token('{')
    while self.current_token == 'var':
      n_vars += self.__compile_var_dec()
    self.__write_function(self.class_name + '.' + fn_name, n_vars)
    if fn_type == CONSTRUCTOR:
      self.__write_push(CONSTANT, self.cst.num_of_fields)
      self.__write_call(MEMORY_ALLOC, 1)
      self.__write_pop(POINTER, 0)
    if fn_type == METHOD:
      self.__write_push(ARGUMENT, 0)
      self.__write_pop(POINTER, 0)
    self.__compile_statements()
    self.__process_token('}')

  def __compile_var_dec(self) -> int:
    self.__process_token('var')
    n_vars = 1
    s_type = self.__process_st_type([INT, CHAR, BOOLEAN], LexicalLabels.IDENTIFIER)
    s_name = self.__process_st_name(LexicalLabels.IDENTIFIER)
    s_kind = LOCAL
    self.sst.add(s_name, s_type, s_kind)
    while self.current_token != ';' and self.current_token == ',':
      self.__process_token(',')
      s_name = self.__process_st_name(LexicalLabels.IDENTIFIER)
      self.sst.add(s_name, s_type, s_kind)
      n_vars += 1
    self.__process_token(';')
    return n_vars

  def __compile_statements(self):
    while self.current_token in ['let', 'while', 'if', 'do', 'return']:
      if self.current_token == 'let':
        self.__compile_let()
      elif self.current_token == 'while':
        self.__compile_while()
      elif self.current_token == 'if':
        self.__compile_if()
      elif self.current_token == 'do':
        self.__compile_do()
      elif self.current_token == 'return':
        self.__compile_return()

  def __compile_let(self):
    self.__process_token('let')
    symbol = self.__lookup(self.__process_st_name(LexicalLabels.IDENTIFIER))
    is_array_manipulation = True if symbol.type_of == ARRAY and self.current_token == '[' else False
    if self.current_token == '[':
      self.__process_token('[')
      self.__compile_expression()
      self.__write_push(symbol.kind, symbol.index)
      self.__write_arithmetic('add')
      self.__process_token(']')
    self.__process_token('=')
    self.__compile_expression()
    if is_array_manipulation:
      self.__write_pop('temp', 0)
      self.__write_pop('pointer', 1)
      self.__write_push('temp', 0)
    self.__write_pop(symbol.kind, symbol.index) if not is_array_manipulation else self.__write_pop('that', 0)
    self.__process_token(';')

  def __compile_if(self):
    self.__process_token('if')
    self.__process_token('(') 
    self.__compile_expression()
    label_true = self.__generate_label()
    label_false = self.__generate_label()
    label_end = self.__generate_label()
    has_else = False
    self.__write_if(label_true)
    self.__write_goto(label_false)
    self.__write_label(label_true)
    self.__process_token(')')
    self.__process_token('{')
    self.__compile_statements()
    self.__process_token('}')
    if self.current_token == 'else':
      has_else = True
      self.__process_token('else')
      self.__process_token('{')
      self.__write_goto(label_end)
      self.__write_label(label_false)
      self.__compile_statements()
      self.__process_token('}')
    if has_else: self.__write_label(label_end)
    else: self.__write_label(label_false)

  def __compile_while(self):
    label_one = self.__generate_label()
    label_two = self.__generate_label()
    self.__write_label(label_one)
    self.__process_token('while')
    self.__process_token('(')
    self.__compile_expression()
    self.__write_arithmetic('not')
    self.__write_if(label_two)
    self.__process_token(')')
    self.__process_token('{')
    self.__compile_statements()
    self.__write_goto(label_one)
    self.__process_token('}')
    self.__write_label(label_two)

  def __compile_do(self):
    self.__process_token('do')
    self.__compile_expression()
    self.__write_pop(TEMP, 0)
    self.__process_token(';')

  def __compile_return(self):
    self.__process_token('return')
    self.__compile_expression() if self.current_token != ';' else self.__write_push(CONSTANT, 0)
    self.__write_return()
    self.__process_token(';')

  def __compile_expression(self):
    self.__compile_term()
    while self.current_token in ['+', '-', '*', '/', '&', '|', '<', '>', '=']:
      op = OP_CONV[self.current_token]
      self.tokenizer.advance()
      self.__compile_term()
      self.__write_arithmetic(op)

  def __compile_term(self):
    if self.current_token in [TRUE, FALSE, NULL, THIS]:
      self.__write_push(CONST_CONV[self.current_token], INDEX_CONV[self.current_token])
      if self.current_token == TRUE: self.__write_arithmetic('neg')
      self.tokenizer.advance()
    elif self.__is_in_symbol_table(self.current_token):
      symbol = self.__lookup(self.current_token)
      name = symbol.type_of
      self.tokenizer.advance()
      if symbol.type_of == ARRAY and self.current_token == '[':
        self.__process_token('[')
        self.__compile_expression()
        self.__write_push(symbol.kind, symbol.index)
        self.__write_arithmetic('add')
        self.__process_token(']')
        self.__write_pop('pointer', 1)
        self.__write_push('that', 0)
      else:
        self.__write_push(symbol.kind, symbol.index)
      if self.current_token == '.':
        self.__process_token('.')
        method = self.current_token
        self.__process_type(LexicalLabels.IDENTIFIER)
        self.__process_token('(')
        n_args = self.__compile_expression_list()
        self.__process_token(')')
        self.__write_call(name + '.' + method, n_args + 1)
    elif self.token_type is LexicalLabels.INT_CONST:
      self.__write_push(CONSTANT, self.current_token)
      self.__process_type(LexicalLabels.INT_CONST)
    elif self.token_type is LexicalLabels.STR_CONST:
      token = self.current_token[1:-1]
      self.__write_push(CONSTANT, len(token))
      self.__write_call('String.new', 1)
      for c in token:
        self.__write_push(CONSTANT, ord(c))
        self.__write_call('String.appendChar', 2)
      self.__process_type(LexicalLabels.STR_CONST)
    elif self.current_token == '(':
      self.__process_token('(')
      self.__compile_expression()
      self.__process_token(')')
    elif self.current_token in ['-', '~']:
      unary_op = UNARY_OP_CONV[self.current_token]
      self.tokenizer.advance()
      self.__compile_term()
      self.__write_arithmetic(unary_op)
    elif self.token_type is LexicalLabels.IDENTIFIER:
      name = self.current_token
      self.__process_type(LexicalLabels.IDENTIFIER)
      if self.current_token == '(':
        self.__process_token('(')
        self.__write_push(POINTER, 0)
        n_args = self.__compile_expression_list()
        self.__process_token(')')
        self.__write_call(self.class_name + '.' + name, n_args + 1)
      elif self.current_token == '.':
        self.__process_token('.')
        method = self.current_token
        self.__process_type(LexicalLabels.IDENTIFIER)
        self.__process_token('(')
        n_args = self.__compile_expression_list()
        self.__process_token(')')
        self.__write_call(name + '.' + method, n_args)
      elif self.current_token == '[':
        self.__process_token('[')
        self.__compile_expression()
        self.__process_token(']')
    else:
      raise Exception(f'Token {self.current_token} of type {self.token_type} was not expected token')

  def __compile_expression_list(self) -> int:
    n_args = 0
    if self.current_token != ')':
      self.__compile_expression()
      n_args += 1
      while self.current_token == ',':
        self.__process_token(',')
        self.__compile_expression()
        n_args += 1
    return n_args

def is_blank(line: str):
  return line == ''

def is_comment(line: str):
  return len(line) > 2 and line[0] == '/' and line[1] == '/'

def block_comment_start(line: str):
  return len(line) > 2 and line[0:3] == '/**'

def remove_trailing_comments(line: str):
  return line.split('//')[0].strip() if '//' in line else line.split('/**')[0].strip()

def tokenize_line(line):
  tokens = []; s = ''; otl = 0; cs = ''

  for index, c in enumerate(line):
    if otl != len(tokens):
      s = ''; cs = ''; otl = len(tokens)
    s += c; cs += c; s = s.strip()
    if len(s) > 0 and (s[0] in string.ascii_letters or s[0] == '_') and c == ' ':
      tokens.append(s)
    elif len(s) > 1 and s[0] == '"' and s[-1] == '"':
      tokens.append(cs.strip())
    elif s in SYMBOLS:
      tokens.append(s)
    elif s in KEYWORDS and (len(tokens) <= 0 or tokens[-1] != '.') and (index+1 < len(line) and line[index+1] not in string.ascii_letters):
      tokens.append(s)
    elif c in SYMBOLS and s != c and (len(s) > 0 and s[0] != '"'):
      tokens.append(s[:-1])
      tokens.append(c)

  return tokens

def tokenize(file_path):
  token_buffer = []
  in_block_comment = False

  with open(file_path, 'r') as f:
    for line in f:
      line = line.strip('\n').strip()
      if block_comment_start(line):
        in_block_comment = True

      if in_block_comment and '*/' in line:
        in_block_comment = False
      elif not is_blank(line) and not is_comment(line) and not in_block_comment:
        token_buffer += tokenize_line(remove_trailing_comments(line))

  return token_buffer

def main():
  parser = argparse.ArgumentParser(description='Translates Jack language into XML code')
  parser.add_argument('--f', help='Input Jack program or folder containing jack programs')

  args = parser.parse_args()
  file_path = Path(args.f)

  candidates = [file_path] if not file_path.is_dir() else [file for file in file_path.glob('*.jack')]

  label_value = LabelValue()
  for fp in candidates:
    compilation_engine = CompilationEngine(Tokenizer(fp), label_value)
    compilation_engine.compile_class()

    with open(str(fp).split('/')[-1][:-4] + 'vm', 'w') as f:
      f.writelines(line + '\n' for line in compilation_engine.buffer)

if __name__ == '__main__':
  main()