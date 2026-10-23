import React from 'react';
import Markdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// Models may use LaTeX delimiters instead of Markdown math delimiters.
// Leave fenced and inline code unchanged, where backslashes are literal.
export function normalizeMathDelimiters(content) {
  return content.split(/(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]*`)/g)
    .map((part, index) => index % 2 ? part : part
      .replace(/\\\[\s*([\s\S]*?)\s*\\\]/g, (_, math) => `\n\n$$\n${math}\n$$\n\n`)
      .replace(/\\\(([\s\S]*?)\\\)/g, (_, math) => `$${math}$`))
    .join('');
}

export default function CoachMessage({ content }) {
  return React.createElement('div', { className: 'coach-markdown' },
    React.createElement(Markdown, {
      remarkPlugins: [remarkMath],
      rehypePlugins: [[rehypeKatex, { strict: false, trust: false }]],
      // Do not interpret model-generated raw HTML.
      skipHtml: true,
    }, normalizeMathDelimiters(content)));
}
