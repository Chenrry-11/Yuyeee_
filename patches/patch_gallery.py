#!/usr/bin/env python3
# v0.3 角色图库 + 图片本地持久化
import sys, io

PATH = 'index.html'
MARK = '_galRender'

PANEL = '''<div class="view-panel" id="character-gallery-view" style="--app-label:'GALLERY'">
    <div class="nav-header">
        <div class="nav-back-btn" onclick="app._galBack()"></div>
        <div class="nav-title">图库</div>
        <div class="nav-action-btn" onclick="app._galAddCurrent()" style="font-size:18px;line-height:1;">＋</div>
    </div>
    <div id="gallery-tabs" style="display:flex;gap:0;padding:10px 20px 0;font-size:12px;color:var(--text-sub);"></div>
    <div class="scroll-content" id="gallery-body" style="padding:18px 20px 44px;"></div>
    <input type="file" id="gal-file-input" accept="image/*" style="display:none;">
</div>

'''

SCRIPT = r'''
<script>
(function(){
  if (!window.app) return;
  var app = window.app;
  window._imgUrlCache = new WeakMap();

  app._imgSrcOf = function(data) {
    if (!data) return '';
    if (typeof data === 'string') return data;
    try {
      if (window._imgUrlCache.has(data)) return window._imgUrlCache.get(data);
      var u = URL.createObjectURL(data);
      window._imgUrlCache.set(data, u);
      return u;
    } catch (e) { return ''; }
  };

  app._imgResolve = function(id) {
    if (!id) return Promise.resolve('');
    return app.imageDB.get(id).then(function(d) { return d ? app._imgSrcOf(d) : ''; }).catch(function() { return ''; });
  };

  app._imgDelete = function(id) {
    if (!id) return Promise.resolve();
    return app.imageDB.init().then(function() {
      return new Promise(function(resolve) {
        try {
          var tx = app.imageDB.db.transaction(['images'], 'readwrite');
          tx.objectStore('images').delete(id);
          tx.oncomplete = function() { resolve(); };
          tx.onerror = function() { resolve(); };
        } catch (e) { resolve(); }
      });
    }).catch(function() {});
  };

  app._persistPhoto = function(imageId, src) {
    if (!src) return Promise.resolve();
    if (typeof src === 'string' && src.indexOf('data:') === 0) {
      return fetch(src).then(function(r) { return r.blob(); })
        .then(function(b) { return app.imageDB.save(imageId, b); })
        .catch(function() { return app.imageDB.save(imageId, src); });
    }
    if (typeof src === 'string' && /^https?:/.test(src)) {
      return fetch(src, { mode: 'cors' }).then(function(r) {
        if (!r.ok) throw new Error('fetch fail');
        return r.blob();
      }).then(function(b) {
        if (!b || b.size < 100) throw new Error('empty');
        return app.imageDB.save(imageId, b);
      }).catch(function() { return app.imageDB.save(imageId, src); });
    }
    return app.imageDB.save(imageId, src);
  };

  app._imgCompress = function(fileOrBlob, maxSide, quality) {
    return new Promise(function(resolve, reject) {
      var url = URL.createObjectURL(fileOrBlob);
      var img = new Image();
      img.onload = function() {
        try {
          var w = img.naturalWidth, h = img.naturalHeight;
          var scale = Math.min(1, maxSide / Math.max(w, h));
          var cw = Math.max(1, Math.round(w * scale)), ch = Math.max(1, Math.round(h * scale));
          var cv = document.createElement('canvas'); cv.width = cw; cv.height = ch;
          cv.getContext('2d').drawImage(img, 0, 0, cw, ch);
          URL.revokeObjectURL(url);
          cv.toBlob(function(b) {
            if (b && b.type === 'image/webp') { resolve(b); return; }
            cv.toBlob(function(b2) { resolve(b2 || b); }, 'image/jpeg', quality);
          }, 'image/webp', quality);
        } catch (e) { reject(e); }
      };
      img.onerror = function() { URL.revokeObjectURL(url); reject(new Error('image load fail')); };
      img.src = url;
    });
  };

  app._imgToDataUrl = function(blob) {
    return new Promise(function(resolve, reject) {
      var fr = new FileReader();
      fr.onload = function() { resolve(fr.result); };
      fr.onerror = reject;
      fr.readAsDataURL(blob);
    });
  };

  // ===== 图库 =====
  var TABS = [
    { k: 'main', t: '形象' },
    { k: 'avatar', t: '头像' },
    { k: 'sheet', t: '设定' },
    { k: 'stuff', t: '素材' }
  ];
  var EXPRS = [
    ['calm', '平静'], ['smile', '微笑'], ['cold', '冷淡'],
    ['tired', '疲惫'], ['shy', '害羞'], ['angry', '生气']
  ];

  app._galRole = function() { return window._galleryRole || app.caCurrentRoleId; };

  app._galChar = function() {
    var rid = app._galRole();
    return rid ? app._ceGetCharacter(rid) : null;
  };

  app._galVisual = function(c) {
    if (!c.profile.visual) c.profile.visual = {};
    var v = c.profile.visual;
    if (!v.refs) v.refs = [];
    if (!v.expressions) v.expressions = {};
    if (!v.items) v.items = [];
    return v;
  };

  app.openGallery = function() {
    window._galleryRole = app.caCurrentRoleId;
    window._galleryTab = window._galleryTab || 'main';
    if (navigator.storage && navigator.storage.persist) {
      try { navigator.storage.persist(); } catch (e) {}
    }
    app.navigateTo('character-gallery-view');
    setTimeout(function() { app._galRender(); }, 60);
  };

  app._galBack = function() {
    var rid = app._galRole();
    app.navigateTo('character-archive-view');
    if (rid && app.caOpenProfile) setTimeout(function() { app.caOpenProfile(rid); }, 120);
  };

  app._galTab = function(k) {
    window._galleryTab = k;
    app._galRender();
  };

  app._galWrite = function(fn) {
    var rid = app._galRole();
    if (!rid) return;
    app._ceWriteCharacter(rid, fn);
    if (app.saveAll) app.saveAll();
    app._galRender();
  };

  app._galSlot = function(id, w, h, label, target) {
    var kind = '';
    try { kind = (JSON.parse(target) || {}).kind || ''; } catch (e) {}
    var ratio = '';
    if (kind === 'portrait') ratio = 'aspect-ratio:3/4;';
    else if (kind === 'ref' || kind === 'expr' || kind === 'item' || kind === 'new') ratio = 'aspect-ratio:1/1;';
    var style = 'width:' + w + ';' + (h === 'auto' ? '' : 'height:' + h + ';') + ratio + 'border-radius:6px;overflow:hidden;position:relative;flex:none;' +
      'background-size:cover;background-position:center;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:4px;';
    if (id) style += 'border:1px solid rgba(0,0,0,.08);';
    else style += 'border:1px dashed rgba(120,130,140,.45);';
    var inner = id ? '' :
      '<span style="font-size:15px;color:rgba(120,130,140,.7);line-height:1;">＋</span>' +
      '<span style="font-size:10px;color:var(--text-sub);letter-spacing:.04em;">' + label + '</span>';
    return '<div data-gal-img="' + (id || '') + '" data-gal-target=\'' + target + '\' onclick="app._galSlotClick(this)" style="' + style + '">' + inner + '</div>';
  };

  app._galRender = function() {
    var body = document.getElementById('gallery-body');
    var tabs = document.getElementById('gallery-tabs');
    if (!body || !tabs) return;
    var cur = window._galleryTab || 'main';
    var th = '';
    TABS.forEach(function(t, i) {
      var on = t.k === cur;
      th += '<span onclick="app._galTab(\'' + t.k + '\')" style="padding:4px 0;color:' + (on ? 'var(--text-main)' : 'var(--text-sub)') + ';font-weight:' + (on ? '600' : '400') + ';">' + t.t + '</span>';
      if (i < TABS.length - 1) th += '<span style="padding:0 12px;color:rgba(140,150,160,.35);">｜</span>';
    });
    tabs.innerHTML = th;

    var c = app._galChar();
    if (!c) { body.innerHTML = '<div style="font-size:12px;color:var(--text-sub);">没有找到角色</div>'; return; }
    var v = app._galVisual(c);
    var html = '';

    if (cur === 'main') {
      html += '<div style="display:flex;flex-direction:column;align-items:center;margin-bottom:26px;">' +
        app._galSlot(v.portraitId || '', '62%', 'auto', '主形象', JSON.stringify({ kind: 'portrait' })) +
        '<div style="font-size:9px;letter-spacing:.24em;color:var(--text-sub);margin-top:8px;">PORTRAIT 3:4</div></div>';
      html += '<div style="font-size:11px;color:var(--text-sub);margin-bottom:10px;">参考图 · 最多 3 张</div>';
      html += '<div style="display:flex;gap:10px;margin-bottom:26px;">';
      for (var i = 0; i < 3; i++) {
        html += app._galSlot(v.refs[i] || '', '31%', 'auto', '参考' + (i + 1), JSON.stringify({ kind: 'ref', index: i }));
      }
      html += '</div>';
      html += '<div style="display:flex;align-items:baseline;gap:10px;margin-bottom:10px;">' +
        '<span style="font-size:12px;">表情差分</span>' +
        '<span style="font-size:9px;letter-spacing:.18em;color:var(--text-sub);">EXPRESSIONS</span></div>';
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">';
      EXPRS.forEach(function(e) {
        html += app._galSlot(v.expressions[e[0]] || '', '100%', 'auto', e[1], JSON.stringify({ kind: 'expr', key: e[0] }));
      });
      html += '</div>';
    } else if (cur === 'avatar') {
      var av = c.profile.avatar || '';
      var avIsId = av && String(av).indexOf('data:') !== 0;
      var avBox = app._galSlot(avIsId ? av : '', '180px', '180px', '头像', JSON.stringify({ kind: 'avatar' }));
      if (av && !avIsId) avBox = avBox.replace('style="', 'style="background-image:url(' + av + ');');
      html += '<div style="display:flex;flex-direction:column;align-items:center;gap:10px;margin-top:14px;">' + avBox +
        '<div style="font-size:9px;letter-spacing:.18em;color:var(--text-sub);">AVATAR / POCKET CHAT</div></div>';
    } else {
      var items = v.items.filter(function(x) { return x.cat === cur; });
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">';
      items.forEach(function(x, i) {
        html += app._galSlot(x.id, '100%', 'auto', '', JSON.stringify({ kind: 'item', id: x.id }));
      });
      html += app._galSlot('', '100%', 'auto', '添加', JSON.stringify({ kind: 'new', cat: cur }));
      html += '</div>';
      if (!items.length) html += '<div style="font-size:11px;color:var(--text-sub);margin-top:14px;">还没有图片。点上面的格子添加。</div>';
    }
    body.innerHTML = html;
    app._galHydrate();
  };

  app._galHydrate = function() {
    document.querySelectorAll('#gallery-body [data-gal-img]').forEach(function(el) {
      var id = el.getAttribute('data-gal-img');
      if (!id) return;
      var thumb = id + '_t';
      app._imgResolve(thumb).then(function(src) {
        if (src) { el.style.backgroundImage = 'url(' + src + ')'; return ''; }
        return app._imgResolve(id);
      }).then(function(src2) {
        if (src2) el.style.backgroundImage = 'url(' + src2 + ')';
      });
    });
  };

  app._galSlotClick = function(el) {
    var target = JSON.parse(el.getAttribute('data-gal-target') || '{}');
    var id = el.getAttribute('data-gal-img');
    if (!id) { app._galPick(target); return; }
    app._galPreview(id, target);
  };

  app._galAddCurrent = function() {
    var cur = window._galleryTab || 'main';
    if (cur === 'main') {
      var c = app._galChar();
      var v = c ? app._galVisual(c) : { refs: [] };
      if ((v.refs || []).length < 3) app._galPick({ kind: 'ref', index: (v.refs || []).length });
      else app._galPick({ kind: 'portrait' });
    } else if (cur === 'avatar') app._galPick({ kind: 'avatar' });
    else app._galPick({ kind: 'new', cat: cur });
  };

  app._galPick = function(target) {
    window._galTarget = target;
    var fi = document.getElementById('gal-file-input');
    if (!fi) return;
    fi.value = '';
    fi.click();
  };

  app._galFileChosen = function(ev) {
    var file = ev.target.files && ev.target.files[0];
    if (!file) return;
    var t = window._galTarget || {};
    var maxSide = 1080;
    if (t.kind === 'portrait') maxSide = 1440;
    if (t.kind === 'expr') maxSide = 768;
    if (t.kind === 'avatar') maxSide = 256;
    app._imgCompress(file, maxSide, 0.8).then(function(blob) {
      if (t.kind === 'avatar') {
        return app._imgToDataUrl(blob).then(function(du) {
          app._galWrite(function(ch) { ch.profile.avatar = du; });
          if (app.caRenderProfile) app.caRenderProfile();
          return null;
        });
      }
      var id = 'gal_' + Date.now() + '_' + Math.floor(Math.random() * 9999);
      return app._imgCompress(blob, 200, 0.75).then(function(thumb) {
        return app.imageDB.save(id, blob).then(function() {
          return app.imageDB.save(id + '_t', thumb);
        }).then(function() {
          app._galWrite(function(ch) {
            var v = app._galVisual(ch);
            if (t.kind === 'portrait') { v.portraitId = id; }
            else if (t.kind === 'ref') { v.refs[t.index] = id; v.refs = v.refs.filter(function(x) { return !!x; }); }
            else if (t.kind === 'expr') { v.expressions[t.key] = id; }
            else if (t.kind === 'new') { v.items.push({ id: id, cat: t.cat }); }
          });
          if (t.kind === 'portrait' && app.caRenderProfile) app.caRenderProfile();
        });
      });
    }).catch(function(e) {
      if (window.console) console.log('gallery upload error', e);
      if (app._flash) app._flash('图片处理失败，换一张试试');
    });
  };

  app._galPreview = function(id, target) {
    app._imgResolve(id).then(function(src) {
      if (!src) { if (app._flash) app._flash('图片读取失败'); return; }
      var ov = document.createElement('div');
      ov.style.cssText = 'position:fixed;inset:0;z-index:100001;background:rgba(10,14,18,.92);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:22px;gap:18px;';
      ov.innerHTML = '<img src="' + src + '" style="max-width:100%;max-height:76%;object-fit:contain;border-radius:8px;">' +
        '<div style="display:flex;gap:22px;font-size:13px;color:#e8eaec;">' +
        '<span data-act="replace">更换</span><span style="opacity:.3;">｜</span>' +
        '<span data-act="del">删除</span><span style="opacity:.3;">｜</span>' +
        '<span data-act="close">关闭</span></div>';
      ov.onclick = function(e) {
        var act = e.target.getAttribute('data-act');
        if (!act) { ov.remove(); return; }
        if (act === 'close') { ov.remove(); return; }
        if (act === 'replace') { ov.remove(); app._galPick(target); return; }
        if (act === 'del') {
          ov.remove();
          app._galWrite(function(ch) {
            var v = app._galVisual(ch);
            if (target.kind === 'portrait') v.portraitId = '';
            else if (target.kind === 'ref') v.refs = v.refs.filter(function(x) { return x !== id; });
            else if (target.kind === 'expr') delete v.expressions[target.key];
            else if (target.kind === 'item') v.items = v.items.filter(function(x) { return x.id !== id; });
          });
          app._imgDelete(id); app._imgDelete(id + '_t');
          if (target.kind === 'portrait' && app.caRenderProfile) app.caRenderProfile();
        }
      };
      document.body.appendChild(ov);
    });
  };

  // 档案首页：主形象优先展示，点击进入图库
  if (app.caRenderProfile && !app._galWrappedProfile) {
    app._galWrappedProfile = true;
    var origRender = app.caRenderProfile;
    app.caRenderProfile = function() {
      var r = origRender.apply(this, arguments);
      try {
        var c = app._galChar();
        var v = c && c.profile ? app._galVisual(c) : null;
        var el = document.getElementById('ca-avatar');
        if (el && v && v.portraitId) {
          app._imgResolve(v.portraitId).then(function(src) {
            if (src) { el.style.backgroundImage = 'url(' + src + ')'; el.innerText = ''; }
          });
        }
      } catch (e) {}
      return r;
    };
  }

  document.addEventListener('change', function(e) {
    if (e.target && e.target.id === 'gal-file-input') app._galFileChosen(e);
  }, false);
})();
</script>
'''


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if MARK in h:
        print('already patched, skip')
        return

    anchor = '<div class="view-panel" id="art-style-config-view"'
    if anchor not in h:
        print('panel anchor missing'); sys.exit(1)
    h = h.replace(anchor, PANEL + anchor, 1)

    old = '<div class="ca-avatar" id="ca-avatar" onclick="app.caChangeAvatar()"></div>'
    new = '<div class="ca-avatar" id="ca-avatar" onclick="app.openGallery()"></div>'
    if old not in h:
        print('avatar anchor missing'); sys.exit(1)
    h = h.replace(old, new, 1)

    old2 = 'if (data && img.isConnected) img.src = data;'
    if old2 not in h:
        print('hydrate anchor missing'); sys.exit(1)
    h = h.replace(old2, 'if (data && img.isConnected) img.src = app._imgSrcOf(data);', 1)

    old3 = "overlay.innerHTML = '<img src=\"' + data + '\""
    if old3 not in h:
        print('preview anchor missing'); sys.exit(1)
    h = h.replace(old3, "overlay.innerHTML = '<img src=\"' + app._imgSrcOf(data) + '\"", 1)

    old4 = 'return app.imageDB.save(imageId, r.src).then(function() { return r; });'
    if old4 in h:
        h = h.replace(old4, 'return app._persistPhoto(imageId, r.src).then(function() { return r; });', 1)
    old5 = 'return app.imageDB.save(imageId, src).then(function() { return src; });'
    if old5 in h:
        h = h.replace(old5, 'return app._persistPhoto(imageId, src).then(function() { return src; });', 1)

    h = h.replace('</body>', SCRIPT + '</body>', 1)

    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('patched, new length', len(h))


if __name__ == '__main__':
    main()
