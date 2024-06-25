import { LitElement, css, html } from 'lit';
import { live } from 'lit/directives/live.js';
import { createRef, ref } from 'lit/directives/ref.js'

class IQLTextarea extends LitElement {
  static styles = css`
    :host {
      display: grid;
      font-size: inherit;
      font-family: monospace;
      margin: 0px;
      padding: 0px;
      tab-size: 2;
    }

    textarea, iql-code {
      grid-area: 1 / 1 / 2 / 2;
      overflow-x: auto;
      overflow-y: hidden;
      white-space: pre;

      border-style: solid;
      border-width: 1px;
      margin: 2px;
      padding: 2px;
      tab-size: 2;

      line-height: 1rem;

      font-size: inherit;
      font-family: inherit;
    }

    iql-code {
      z-index: 0;
      border-color: transparent;
    }


    textarea {
      z-index: 1;

      resize: none;

      color: transparent;
      background: transparent;
      caret-color: black;
      @media (prefers-color-scheme: dark) {
        caret-color: white;
      }
    }
  `;

  static properties = {
    _content: { type: String },
  };

  textareaRef = createRef();
  codeRef = createRef();

  _handleInput(event) {
    this._content = event.target.value;
  }

  _handleScroll(event) {
    this.codeRef.value.scrollTop = this.textareaRef.value.scrollTop;
    this.codeRef.value.scrollLeft = this.textareaRef.value.scrollLeft;
  }

  constructor() {
    super();
    this._content = this.textContent || '';
  }

  render() {
    const text = this._content[this._content.length-1] == "\n" ? this._content + ' ' : this._content;
    return html`
      <textarea
        ref=${ref(this.textareaRef)}
        spellcheck="false"
        @input=${this._handleInput}
        @scroll=${this._handleScroll}
        wrap="off"
        placeholder="You can edit queries here"
      >${text}</textarea>
      <iql-code
        ref=${ref(this.codeRef)}
      >${text}</iql-code>
    `;
  }
}

customElements.define('iql-textarea', IQLTextarea);
