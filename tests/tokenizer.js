"use strict";

const debug = require('debug')('ast');
const keyMirror = require('keymirror');

let keywords = [
  "auto",
  "break",
  "case",
  "char",
  "const",
  "continue",
  "default",
  "do",
  "double",
  "else",
  "enum",
  "extern",
  "float",
  "for",
  "goto",
  "if",
  "int",
  "long",
  "register",
  "return",
  "short",
  "signed",
  "sizeof",
  "static",
  "struct",
  "switch",
  "typedef",
  "union",
  "unsigned",
  "void",
  "volatile",
  "while"];

// (int)(?:[ |;|*])
let keywordRegex = '(' + keywords.join(")[^a-zA-Z0-9;*]|(") + ')[^a-zA-Z0-9;*]';

const TokenType = keyMirror({
  areaComment: null,
  lineComment: null,
  quote: null,
  char: null,
  directive: null,
  openParen: null,
  closeParen: null,
  openSquare: null,
  closeSquare: null,
  openCurly: null,
  closeCurly: null,
  operator: null,
  keyword: null,
  identifier: null,
  number: null,
  whitespace: null,
  lineContinue: null
});

let rules = [
  { regex: /\/\*([^*]|\*(?!\/))*\*\//, type: TokenType.areaComment },
  // { regex: /\/\*([^*]|\*(?!\/))*\*?$/, type: TokenType.area comment continue },
  { regex: /\/\/[^\n]*/, type: TokenType.lineComment },
  { regex: /"([^"\n]|\\")*"?/, type: TokenType.quote },
  { regex: /'(\\?[^'\n]|\\')'?/, type: TokenType.char },
  // { regex: /'[^']*/, type: TokenType.char continue },
  { regex: /#(\S*)/, type: TokenType.directive },
  { regex: /\(/, type: TokenType.openParen },
  { regex: /\)/, type: TokenType.closeParen },
  { regex: /\[/, type: TokenType.openSquare },
  { regex: /\]/, type: TokenType.closeSquare },
  { regex: /{/, type: TokenType.openCurly },
  { regex: /}/, type: TokenType.closeCurly },
  { regex: /([-<>~!%^&*\/+=?|.,:;]|->|<<|>>|\*\*|\|\||&&|--|\+\+|[-+*|&%\/=]=)/,
    type: TokenType.operator },
  // { regex: keywordRegex, type: TokenType.keyword },
  { regex: /([_A-Za-z]\w*)/, type: TokenType.identifier },
  { regex: /[-+x]?[0-9]?[0-9]*\.?[0-9]+/, type: TokenType.number },
  { regex: /(\s+)/, type: TokenType.whitespace },
  { regex: /\\\n?/, type: TokenType.lineContinue }
];

function tokenize(text) {
  let tokens = createTokens(text);
  tokens = insertKeywords(tokens);


  // TODO: 
  // look for identifiers and change them to keywords
  // special case: else if() is one keyword.

  //TODO: How to handle macros?
  return tokens;
}

function createTokens(text) {
  let startIndex = 0;
  let tokens = [];
  let bestMatch = null;
  do {        
    let chunk = text.substring(startIndex, text.length);
    bestMatch = null;
    
    for(let r of rules) {
      let match = chunk.match(r.regex);
      if (match) {
        match.input = '';
        // debug(match);
        if (!bestMatch || bestMatch.index > match.index) {
          bestMatch = {
            rule: r,
            result: match,
            index: match.index,
            length: match[0].length
          };
        }
      }
    }
    if (bestMatch) {
      tokens.push({
        type: bestMatch.rule.type,
        value: bestMatch.result[0]
      });
      startIndex = startIndex + bestMatch.index + bestMatch.length;
    }    
  } while(bestMatch);
  return tokens;
}

function insertKeywords(tokens) {
  let lastToken = null;
  let newTokens = [];
  for(let token of tokens) {
    if (token.type == TokenType.identifier
        && keywords.indexOf(token.value.trim()) > -1) {
      token.type = TokenType.keyword;
    }    
    newTokens.push(token);
  }
  return tokens;
}


function parse(tokens) {
  let ctx = {
    i: 0,
    tokens: tokens
  };
  
  let body = [];
  while(ctx.i < tokens.length) {
    let obj = walk(ctx);
    if (obj) {
      body.push(obj);
    }
  }
  
  return {
    type: 'program',
    body: body
  }
}

// state machine:
// - inside method?/ block
// pgm:
//  - definition
//  - function
//     - statement

function walk(ctx) {
  let token = ctx.tokens[ctx.i];

  if (token.type == TokenType.areaComment) {
    ctx.i ++;
    return {
      type: 'AreaCommentLiteral',
      value: token.value
    };
  }
  if (token.type == TokenType.lineComment) {
    ctx.i ++;
    return {
      type: 'LineCommentLiteral',
      value: token.value
    }
  }
  if (token.type == TokenType.directive) {
    ctx.i ++;
    let directive = {
      type: 'DirectiveLiteral',
      name: token.value,
      body: []
    }
    ctx.i ++;
    // call walk recursively and add to body?
  }
  ctx.i ++;
}

module.exports = {
  tokenize,
  parse
};
