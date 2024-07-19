import { LitElement, css } from 'lit';
import { MutationController } from '@lit-labs/observers/mutation-controller.js';
import { iql } from './iql-language.mjs';

hljs.registerLanguage('iql', iql);
hljs.configure({ languages: ['iql'] });

class IQLCode extends LitElement {
  static styles = css`
    :host {
      margin: 0;
      padding: 0;

      display: block;

      font-family: monospace;
      line-height: 1rem;

      white-space: pre-line;
    }

    :host::part(built-in) { color: #e36209 }
    :host::part(keyword)  { color: #d73a49 }
    :host::part(number)   { color: #005cc5 }
    :host::part(operator) { color: #005cc5 }
    :host::part(string)   { color: #6a9955 }
  `;

  _observer = new MutationController(this, {
    config: {
      attributes: true,
      characterData: true,
      childList: true,
      subtree: true
    },
  });

  constructor() {
    super();
  }

  render() {
    const { value: innerHTML } = hljs.highlight(this.textContent, { language: 'iql' });

    const divElement = document.createElement('div');
    divElement.innerHTML = innerHTML;

    divElement.querySelectorAll('.hljs-built_in').forEach((el) => el.part = 'built-in')
    divElement.querySelectorAll('.hljs-keyword').forEach((el)  => el.part = 'keyword')
    divElement.querySelectorAll('.hljs-number').forEach((el)   => el.part = 'number')
    divElement.querySelectorAll('.hljs-operator').forEach((el) => el.part = 'operator')
    divElement.querySelectorAll('.hljs-string').forEach((el)   => el.part = 'string')

    return Array.from(divElement.childNodes);
  }
}

customElements.define('iql-code', IQLCode);
