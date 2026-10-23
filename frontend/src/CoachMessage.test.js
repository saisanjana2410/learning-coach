import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import CoachMessage, { normalizeMathDelimiters } from './CoachMessage.js';

test('renders tutor bold text, lists and both LaTeX math delimiters', () => {
  const content = String.raw`**Linear Regression** predicts a number.

\[
\hat{y} = b + m \times x
\]

- \(x\) is the input.
- **Slope** has units.
`;
  const html = renderToStaticMarkup(React.createElement(CoachMessage, {content}));
  assert.match(html, /<strong>Linear Regression<\/strong>/);
  assert.match(html, /<ul>/);
  assert.match(html, /katex-display/);
  assert.match(html, /<math/);
  assert.doesNotMatch(html, /\\\[|\\\(/);
});

test('leaves code examples intact and does not render raw HTML or unsafe links', () => {
  const code = '```python\nvalue = "\\(x\\)"\n```';
  assert.equal(normalizeMathDelimiters(code), code);
  const inline = '`\\(x\\)`';
  assert.equal(normalizeMathDelimiters(inline), inline);
  const html = renderToStaticMarkup(React.createElement(CoachMessage, {
    content: '<script>alert(1)</script>\n\n[bad](javascript:alert%281%29)\n\n' + code,
  }));
  assert.doesNotMatch(html, /<script|href="javascript:/);
  assert.match(html, /language-python/);
});
