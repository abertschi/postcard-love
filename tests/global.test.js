const assert = require('assert');
const ast = require('./tokenizer');
const path = require('path');
const debug = require('debug')('ast')

const fs = require('fs');

describe('tokenize', () => {
  it('test', () => {
    var code = fs.readFileSync(path.resolve(__dirname, 'c-code.c'), 'utf8');
    let tokens = ast.tokenize(code);
    let a = ast.parse(tokens);
    
    fs.writeFile(path.resolve(__dirname, 'tokenize.json'), JSON.stringify(tokens), function(err) {
      if(err) {
        return console.log(err);
      }
      console.log("The file was saved!");
    }); 
    
    /* console.log(t);*/
    debug(a);
  });
});
