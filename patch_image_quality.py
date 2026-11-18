#!/usr/bin/env python3
# 修复部分手机浏览器 WebP 转码异常；主图与缩略图均直接从原图生成 JPEG
import io, sys

PATH = 'index.html'
START = '  app._imgCompress = function(fileOrBlob, maxSide, quality) {'
END = '\n\n  app._imgToDataUrl = function(blob) {'

NEW = '''  app._imgCompress = function(fileOrBlob, maxSide, quality) {
    return new Promise(function(resolve, reject) {
      var url = URL.createObjectURL(fileOrBlob);
      var img = new Image();
      img.onload = function() {
        try {
          var w = img.naturalWidth, h = img.naturalHeight;
          if (!w || !h) throw new Error('invalid image size');
          var scale = Math.min(1, maxSide / Math.max(w, h));
          var cw = Math.max(1, Math.round(w * scale)), ch = Math.max(1, Math.round(h * scale));
          var cv = document.createElement('canvas');
          cv.width = cw; cv.height = ch;
          var ctx = cv.getContext('2d', { alpha: false });
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, cw, ch);
          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';
          ctx.drawImage(img, 0, 0, cw, ch);
          URL.revokeObjectURL(url);
          cv.toBlob(function(b) {
            if (b && b.size > 0) resolve(b);
            else reject(new Error('jpeg encode failed'));
          }, 'image/jpeg', Math.max(0.88, quality || 0.9));
        } catch (e) {
          URL.revokeObjectURL(url);
          reject(e);
        }
      };
      img.onerror = function() { URL.revokeObjectURL(url); reject(new Error('image load fail')); };
      img.src = url;
    });
  }; // imageQualityJpegFix'''


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if 'imageQualityJpegFix' in h:
        print('already fixed, skip')
        return
    a = h.find(START)
    b = h.find(END, a)
    if a < 0 or b < 0:
        print('compress anchors missing'); sys.exit(1)
    h = h[:a] + NEW + h[b:]
    h = h.replace("app._imgCompress(file, maxSide, 0.8)", "app._imgCompress(file, maxSide, 0.92)", 1)
    h = h.replace("if (t.kind === 'avatar') maxSide = 256;", "if (t.kind === 'avatar') maxSide = 512;", 1)
    h = h.replace("return app._imgCompress(blob, 200, 0.75).then(function(thumb)", "return app._imgCompress(file, 360, 0.88).then(function(thumb)", 1)
    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('image quality fixed, len', len(h))


if __name__ == '__main__':
    main()
