//=============================================================================
// AutoWordWrap.js - Smart Auto Word Wrap & Auto-Shrink for RPG Maker MV/MZ
// Injected by Antigravity Game Translator RPG Maker Skill
//=============================================================================
/*:
 * @target MV MZ
 * @plugindesc [v1.0.0] Smart Auto Word Wrap & Auto-Shrink for Vietnamese & long text
 * @author Antigravity Localization
 * @help
 * Tự động đo độ rộng pixel thực tế của câu thoại và ảnh Face để ngắt dòng thông minh.
 * Tự động thu nhỏ nhẹ kích thước chữ nếu câu thoại vượt quá 4 dòng để tránh mất chữ.
 */

(() => {
  'use strict';

  function cleanControlCodes(text) {
    if (!text) return '';
    return text
      .replace(/[\x1b\\][a-zA-Z]+\[[^\]]*\]/g, '')
      .replace(/[\x1b\\][\$\.\|\^!><\{\}]/g, '')
      .replace(/<[^>]+>/g, '')
      .trim();
  }

  function doSmartWrap(windowInstance, text, maxWidth) {
    if (!text) return [];
    const cleanSlashes = text.replace(/\/\\n/g, '\n').replace(/\/n/g, '\n');
    const paragraphs = cleanSlashes.split('\n');
    const wrappedLines = [];

    for (let p = 0; p < paragraphs.length; p++) {
      const para = paragraphs[p];
      if (!para.trim()) {
        wrappedLines.push('');
        continue;
      }

      const words = para.split(' ');
      let curLine = '';

      for (let w = 0; w < words.length; w++) {
        const word = words[w];
        const testLine = curLine ? (curLine + ' ' + word) : word;
        const measureStr = cleanControlCodes(testLine);

        if (windowInstance.textWidth(measureStr) > maxWidth && curLine !== '') {
          wrappedLines.push(curLine);
          curLine = word;
        } else {
          curLine = testLine;
        }
      }
      if (curLine) {
        wrappedLines.push(curLine);
      }
    }
    return wrappedLines;
  }

  if (typeof Window_Message !== 'undefined') {
    const _Window_Message_startMessage = Window_Message.prototype.startMessage;
    Window_Message.prototype.startMessage = function() {
      this.resetFontSettings();

      const hasFace = !!(
        (this._faceBitmap && this._faceBitmap.width > 0) ||
        (typeof $gameMessage !== 'undefined' && $gameMessage.faceName && $gameMessage.faceName())
      );
      const faceMargin = hasFace ? 168 : 0;
      const padding = (this.textPadding ? this.textPadding() * 2 : 12) + 24;
      const maxWidth = Math.max(260, this.contentsWidth() - faceMargin - padding);

      this._textState = {};
      this._textState.index = 0;

      const rawText = this.convertEscapeCharacters($gameMessage.allText());
      const wrappedLines = doSmartWrap(this, rawText, maxWidth);

      this._autoWordWrapShrink = wrappedLines.length > 4;
      this._textState.text = wrappedLines.join('\n');

      this.newPage(this._textState);
      this.updatePlacement();
      this.updateBackground();
      this.open();
    };

    const _Window_Message_resetFontSettings = Window_Message.prototype.resetFontSettings;
    Window_Message.prototype.resetFontSettings = function() {
      _Window_Message_resetFontSettings.call(this);
      if (this._autoWordWrapShrink && this.contents) {
        this.contents.fontSize = Math.max(18, (this.contents.fontSize || this.standardFontSize()) - 3);
      }
    };

    if (typeof KNS_MessageSplit !== 'undefined') {
      Window_Message.prototype.processNormalCharacter = function(textState) {
        Window_Base.prototype.processNormalCharacter.call(this, textState);
      };
    }
  }
})();

