#!/usr/bin/env python3
import argparse
from pathlib import Path
from enum import Enum
import string

KEYWORDS = {'class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char', 
            'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while', 
            'return'}

SYMBOLS = {'{', '}', '|', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', 
           '<', '>', '=', '~'}

INT_RANGE = range(0,32767)

OP_CONV = { '<': '&lt;', '>': '&gt;', '&': '&amp;'}

class LexicalLabels(Enum):
  KEYWORD = 'keyword'
  SYMBOL = 'symbol'
  INT_CONST = 'integerConstant'
  STR_CONST = 'stringConstant'
  IDENTIFIER = 'identifier'

  def __str__(self):
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

class CompilationEngine:
  def __init__(self, jack_tokenizer: Tokenizer):
    self.tokenizer = jack_tokenizer
    self.buffer = []

  def add_start_tag(self, tag_name: str):
    self.buffer.append(f'<{tag_name}>')

  def add_end_tag(self, tag_name: str):
    self.buffer.append(f'</{tag_name}>')

  @property
  def current_token(self):
    return self.tokenizer.current_token

  @property
  def token_type(self):
    return self.tokenizer.token_type

  def process_token(self, expected_token):
    if self.current_token != expected_token:
      raise Exception(f'Token {expected_token} did not match current token {self.current_token}')
    self.buffer += [f'<{self.token_type}> {self.current_token} </{self.token_type}>']
    self.tokenizer.advance()

  def process_type(self, expected_type: LexicalLabels):
    if self.token_type != expected_type:
      raise Exception(f'Token type {self.token_type} does not match {expected_type}')
    self.buffer.append(f'<{expected_type}> {self.current_token} </{expected_type}>')
    self.tokenizer.advance()

  def process_list(self, expected_tokens: list[str], fallback: LexicalLabels = None):
    if self.current_token not in expected_tokens and self.token_type != fallback:
      raise Exception(f'Token {self.current_token} of type {self.token_type} not in {expected_tokens} or {fallback}')
    self.buffer.append(f'<{self.token_type}> {self.current_token} </{self.token_type}>')
    self.tokenizer.advance()

  def compile_class(self):
    self.add_start_tag('class')
    self.process_token('class')
    self.process_type(LexicalLabels.IDENTIFIER)
    self.process_token('{')
    while self.current_token in ['static', 'field']:
      self.compile_class_var_dec()
    while self.current_token in ['constructor', 'function', 'method']:
      self.compile_subroutine_dec()
    self.process_token('}')
    self.add_end_tag('class')

  def compile_class_var_dec(self):
    self.add_start_tag('classVarDec')
    self.process_token('static') if self.current_token == 'static' else self.process_token('field')
    self.process_list(['int', 'char', 'boolean'], LexicalLabels.IDENTIFIER)
    self.process_type(LexicalLabels.IDENTIFIER)
    while self.current_token != ';':
      self.process_token(',')
      self.process_type(LexicalLabels.IDENTIFIER)
    self.process_token(';')
    self.add_end_tag('classVarDec')

  def compile_subroutine_dec(self):
    self.add_start_tag('subroutineDec')
    self.process_list(['constructor', 'function', 'method'])
    self.process_list(['int', 'char', 'boolean', 'void'], LexicalLabels.IDENTIFIER)
    self.process_type(LexicalLabels.IDENTIFIER)
    self.process_token('(')
    self.compile_parameter_list()
    self.process_token(')')
    self.compile_subroutine_body()
    self.add_end_tag('subroutineDec')

  def compile_parameter_list(self):
    self.add_start_tag('parameterList')
    if self.current_token != ')':
      self.process_list(['int', 'char', 'boolean'], LexicalLabels.IDENTIFIER)
      self.process_type(LexicalLabels.IDENTIFIER)
      while self.current_token == ',':
        self.process_token(',')
        self.process_list(['int', 'char', 'boolean'], LexicalLabels.IDENTIFIER)
        self.process_type(LexicalLabels.IDENTIFIER)
    self.add_end_tag('parameterList')

  def compile_subroutine_body(self):
    self.add_start_tag('subroutineBody')
    self.process_token('{')
    while self.current_token == 'var':
      self.compile_var_dec()
    self.compile_statements()
    self.process_token('}')
    self.add_end_tag('subroutineBody')

  def compile_var_dec(self):
    self.add_start_tag('varDec')
    self.process_token('var')
    self.process_list(['int', 'char', 'boolean'], LexicalLabels.IDENTIFIER)
    self.process_type(LexicalLabels.IDENTIFIER)
    while self.current_token != ';' and self.current_token == ',':
      self.process_token(',')
      self.process_type(LexicalLabels.IDENTIFIER)
    self.process_token(';')
    self.add_end_tag('varDec')

  def compile_statements(self):
    self.add_start_tag('statements')
    while self.current_token in ['let', 'while', 'if', 'do', 'return']:
      if self.current_token == 'let':
        self.compile_let()
      elif self.current_token == 'while':
        self.compile_while()
      elif self.current_token == 'if':
        self.compile_if()
      elif self.current_token == 'do':
        self.compile_do()
      elif self.current_token == 'return':
        self.compile_return()
    self.add_end_tag('statements')

  def compile_let(self):
    self.add_start_tag('letStatement')
    self.process_token('let')
    self.process_type(LexicalLabels.IDENTIFIER)
    if self.current_token == '[':
      self.process_token('[')
      self.compile_expression()
      self.process_token(']')
    self.process_token('=')
    self.compile_expression()
    self.process_token(';')
    self.add_end_tag('letStatement')

  def compile_if(self):
    self.add_start_tag('ifStatement')
    self.process_token('if')
    self.process_token('(') 
    self.compile_expression()
    self.process_token(')')
    self.process_token('{')
    self.compile_statements()
    self.process_token('}')
    if self.current_token == 'else':
      self.process_token('else')
      self.process_token('{')
      self.compile_statements()
      self.process_token('}')
    self.add_end_tag('ifStatement')

  def compile_while(self):
    self.add_start_tag('whileStatement')
    self.process_token('while')
    self.process_token('(')
    self.compile_expression()
    self.process_token(')')
    self.process_token('{')
    self.compile_statements()
    self.process_token('}')
    self.add_end_tag('whileStatement')

  def compile_do(self):
    self.add_start_tag('doStatement')
    self.process_token('do')
    self.subroutine_call()
    self.process_token(';')
    self.add_end_tag('doStatement')

  def subroutine_call(self):
    self.process_type(LexicalLabels.IDENTIFIER)
    if self.current_token == '.':
      self.process_token('.')
      self.process_type(LexicalLabels.IDENTIFIER)

    self.process_token('(') 
    self.compile_expression_list()
    self.process_token(')')

  def compile_return(self):
    self.add_start_tag('returnStatement')
    self.process_token('return')
    if self.current_token != ';':
      self.compile_expression()
    self.process_token(';')
    self.add_end_tag('returnStatement')

  def compile_expression(self):
    self.add_start_tag('expression')
    self.compile_term()
    while self.current_token in ['+', '-', '*', '/', '&', '|', '<', '>', '=']:
      op = self.current_token if self.current_token not in OP_CONV else OP_CONV[self.current_token]
      self.buffer += [f'<symbol> {op} </symbol>']
      self.tokenizer.advance()
      self.compile_term()
    self.add_end_tag('expression')

  def compile_term(self):
    self.add_start_tag('term')
    if self.token_type in [LexicalLabels.IDENTIFIER, LexicalLabels.INT_CONST, LexicalLabels.STR_CONST, LexicalLabels.KEYWORD]:
      token = self.current_token[1:-1] if self.token_type == LexicalLabels.STR_CONST else self.current_token
      self.buffer += [f'<{self.token_type}> {token} </{self.token_type}>']
      self.tokenizer.advance()
      if self.current_token == '[':
        self.process_token('[')
        self.compile_expression()
        self.process_token(']')
      elif self.current_token == '.':
        self.process_token('.')
        self.process_type(LexicalLabels.IDENTIFIER)
        self.process_token('(') 
        self.compile_expression_list()
        self.process_token(')')
      elif self.current_token == '(':
        self.process_token('(')
        self.compile_expression()
        self.process_token(')')

    elif self.current_token == '(':
      self.process_token('(')
      self.compile_expression()
      self.process_token(')')
    elif self.current_token in ['-', '~']:
      self.buffer += [f'<symbol> {self.current_token} </symbol>']
      self.tokenizer.advance()
      self.compile_term()
    else:
      raise Exception(f'Token {self.current_token} of type {self.token_type} was not expected token')
    self.add_end_tag('term')

  def compile_expression_list(self):
    self.add_start_tag('expressionList')
    if self.current_token != ')':
      self.compile_expression()
      while self.current_token == ',':
        self.process_token(',')
        self.compile_expression()
    self.add_end_tag('expressionList')

def is_blank(line):
  return line == ''

def is_comment(line):
  return len(line) > 2 and line[0] == '/' and line[1] == '/'

def is_block_comment(line):
  return ('/**' in line) or (len(line) >= 1 and line[0] == '*') or (len(line) >= 2 and line[0:1] == '*/')

def tokenize_line(line):
  tokens = []; s = ''; otl = 0; cs = ''

  for c in line:
    if otl != len(tokens):
      s = ''; cs = ''; otl = len(tokens)
    s += c; cs += c; s = s.strip()
    if len(s) > 0 and (s[0] in string.ascii_letters or s[0] == '_') and c == ' ':
      tokens.append(s)
    elif len(s) > 1 and s[0] == '"' and s[-1] == '"':
      tokens.append(cs.strip())
    elif s in KEYWORDS or s in SYMBOLS:
      tokens.append(s)
    elif c in SYMBOLS and s != c:
      tokens.append(s[:-1])
      tokens.append(c)

  return tokens

def tokenize(file_path):
  token_buffer = []

  with open(file_path, 'r') as f:
    for line in f:
      line = line.strip('\n').strip()
      if is_blank(line) or is_comment(line) or is_block_comment(line):
        continue
      token_buffer += tokenize_line(line.split('//')[0].strip())

  return token_buffer

def main():
  parser = argparse.ArgumentParser(description='Translates Jack language into XML code')
  parser.add_argument('--f', help='Input Jack program or folder containing jack programs')

  args = parser.parse_args()
  file_path = Path(args.f)

  candidates = [file_path] if not file_path.is_dir() else [file for file in file_path.glob('*.jack')]

  for fp in candidates:
    compilation_engine = CompilationEngine(Tokenizer(fp))
    compilation_engine.compile_class()

    with open(str(fp).split('/')[-1][:-4] + 'xml', 'w') as f:
      f.writelines(line + '\n' for line in compilation_engine.buffer)

if __name__ == '__main__':
  main()