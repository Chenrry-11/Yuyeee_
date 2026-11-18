#!/usr/bin/env python3
# v0.2 拍照体验重做 + 身份锁 + 档案真名/占位文案
import sys, io

PATH = 'index.html'
MARK = '_startPhotoFlowV2'

A1 = "        var imageId = imageContent.imageId || '';\n"
A1_NEW = A1 + (
"        if (imageContent.pending) { html += app._photoPendingHtml(imageContent); break; }\n"
"        if (imageContent.failed) { html += app._photoFailedHtml(imageContent, m.ts); break; }\n")

A2 = "            content = '[' + imgWho + ']' + (imgDesc ? '：' + imgDesc : '（没能识别出图片内容，不要猜测图里有什么）');\n"
A2_NEW = A2 + (
"            if (m.content && m.content.pending) content = '[对方正在拍一张照片，还没拍完]';\n"
"            else if (m.content && m.content.failed) content = '[对方想拍一张照片，但没拍成]';\n")

A3 = "        app._startPhotoFlow(role, text, input);"
A3_NEW = "        app._startPhotoFlowV2(role, text, input);"

V2_SCRIPT = r'''
<script>
(function(){
  if (!window.app) { console.log('photoV2: app not found'); return; }
  var app = window.app;

  function esc2(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

  app._photoRatio = function() {
    try {
      var cfg = app.getDrawCfg ? app.getDrawCfg() : {};
      var m = String(cfg.size || '1024x1024').match(/(\d+)\s*x\s*(\d+)/);
      if (m) return parseFloat(m[1]) / parseFloat(m[2]);
    } catch (e) {}
    return 1;
  };

  app._photoPendingHtml = function(c) {
    var r = c.ratio || 1;
    var w = Math.round(Math.min(230, window.innerWidth * 0.62));
    var h = Math.round(Math.max(90, Math.min(300, w / r)));
    var prog = Math.max(2, Math.min(100, c.progress || 0));
    var label = c.overdue ? '还在拍，好了就发你' : '正在拍摄';
    return '<div class="msg-bubble chat-photo-bubble" style="padding:0;border-radius:15px;overflow:hidden;background:rgba(255,255,255,.38);border:1px solid rgba(255,255,255,.62);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);width:' + w + 'px;height:' + h + 'px;display:flex;flex-direction:column;justify-content:center;align-items:center;">' +
        '<div style="flex:1;display:flex;align-items:center;justify-content:center;width:100%;">' +
          '<span style="font-size:11px;letter-spacing:.06em;color:var(--text-sub);">' + label + '</span>' +
        '</div>' +
        '<div style="height:2px;width:100%;background:rgba(130,150,145,.16);">' +
          '<div data-photo-bar="' + esc2(c.imageId) + '" style="height:2px;width:' + prog + '%;background:rgba(120,145,140,.55);transition:width .45s ease;"></div>' +
        '</div>' +
      '</div>';
  };

  app._photoFailedHtml = function(c, ts) {
    return '<div style="display:flex;flex-direction:column;align-items:flex-start;">' +
      '<div class="msg-bubble chat-photo-bubble" onclick="app._photoRetry(\'' + esc2(c.roleId) + '\',\'' + esc2(c.imageId) + '\')" style="padding:0;border-radius:15px;overflow:hidden;background:rgba(255,255,255,.34);border:1px solid rgba(255,255,255,.58);backdrop-filter:blur(16px);width:132px;height:96px;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:5px;">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="width:17px;height:17px;opacity:.5;"><path d="M3 12a9 9 0 1 0 3-6.7"></path><path d="M3 4v5h5"></path></svg>' +
        '<span style="font-size:11px;color:var(--text-sub);">生成失败</span>' +
      '</div>' +
      (c.hinted ? '<div style="font-size:10px;color:var(--text-sub);padding:4px 2px 0;">再拍一张会再扣一次</div>' : '') +
      '</div>';
  };

  app._photoFindMsg = function(roleId, imageId) {
    var msgs = app.chats[roleId] || [];
    for (var i = msgs.length - 1; i >= 0; i--) {
      var c = msgs[i].content || {};
      if (msgs[i].msgType === 'image' && c.imageId === imageId) return msgs[i];
    }
    return null;
  };

  app._photoUpdateBar = function(imageId, progress, overdue) {
    var bars = document.querySelectorAll('[data-photo-bar="' + imageId + '"]');
    for (var i = 0; i < bars.length; i++) bars[i].style.width = Math.max(2, Math.min(100, progress)) + '%';
    var roleId = window._photoActiveRole || app.activeRoleId;
    var msg = roleId ? app._photoFindMsg(roleId, imageId) : null;
    if (msg && msg.content) {
      msg.content.progress = progress;
      if (overdue && !msg.content.overdue) {
        msg.content.overdue = true;
        if (app.renderChatMessages) app.renderChatMessages();
      }
    }
  };

  app._photoStartTick = function(roleId, imageId) {
    window._photoTicks = window._photoTicks || {};
    if (window._photoTicks[imageId]) clearInterval(window._photoTicks[imageId]);
    var t0 = Date.now();
    window._photoTicks[imageId] = setInterval(function() {
      var s = (Date.now() - t0) / 1000;
      var p;
      if (s < 8) p = s / 8 * 40;
      else if (s < 30) p = 40 + (s - 8) / 22 * 38;
      else p = 78 + Math.min(14, (s - 30) / 20 * 14);
      if (p > 92) p = 92;
      app._photoUpdateBar(imageId, p, s >= 45);
    }, 500);
  };

  app._photoStopTick = function(imageId) {
    if (window._photoTicks && window._photoTicks[imageId]) {
      clearInterval(window._photoTicks[imageId]);
      delete window._photoTicks[imageId];
    }
  };

  app._ceIdentity = function(role) {
    var parts = [];
    try {
      var ch = app._ceGetCharacter ? app._ceGetCharacter(role.id) : null;
      var p = (ch && ch.profile) || {};
      var bi = p.basicInfo || {};
      if (typeof bi === 'string') { try { bi = JSON.parse(bi); } catch (e) { bi = {}; } }
      if (!bi || typeof bi !== 'object') bi = {};
      var g = bi.gender || role.gender || '';
      var gmap = { 'Male': '成年男性', 'Female': '成年女性', 'Non-binary': '中性形象', 'Classified': '' };
      if (g) { var gg = (gmap[g] !== undefined) ? gmap[g] : g; if (gg) parts.push(gg); }
      if (bi.age) parts.push(String(bi.age) + '岁');
      if (bi.height) parts.push('身高' + String(bi.height));
      var raw = (ch && ch.personality && ch.personality.raw) || '';
      var m = raw.match(/【外貌】([\s\S]*?)(?=【|$)/);
      if (m && m[1].trim()) parts.push(m[1].trim().slice(0, 140));
    } catch (e) {}
    if (!parts.length) parts.push('与角色设定一致的成年人物');
    return parts.join('，');
  };

  app._startPhotoFlowV2 = function(role, text, input) {
    var roleId = role.id;
    if (!app.chats[roleId]) app.chats[roleId] = [];
    var now = app._ceNow ? app._ceNow() : Date.now();
    app.chats[roleId].push({ sender: 'user', msgType: 'text', content: { text: text }, ts: now });
    role.lastMsg = text;
    role.lastTime = app.getClockStr();
    role.lastChatTime = now;
    if (input) input.value = '';
    if (app.updateRightActionIcon) app.updateRightActionIcon();

    var imageId = 'photo_' + Date.now() + '_' + Math.floor(Math.random() * 999);
    var msg = { sender: 'ai', msgType: 'image', content: {
      imageId: imageId, pending: true, progress: 2, failed: false, roleId: roleId,
      ratio: app._photoRatio(), startedAt: Date.now(), desc: '', text: ''
    }, ts: (app._ceNow ? app._ceNow() : Date.now()) + 1 };
    app.chats[roleId].push(msg);
    app.renderChatMessages();
    if (app.saveAll) app.saveAll();
    if (app.renderPocketChatList) app.renderPocketChatList();
    app._photoStartTick(roleId, imageId);
    window._photoActiveRole = roleId;

    app._buildPhotoBrief(role, text).then(function(brief) {
      msg.content.scene = brief.scene || '';
      if (brief.caption) msg.content.text = brief.caption;
      return app._requestPhotoV2(brief, role).then(function(src) { return { brief: brief, src: src }; });
    }).then(function(r) {
      return app.imageDB.save(imageId, r.src).then(function() { return r; });
    }).then(function(r) {
      app._photoStopTick(imageId);
      msg.content.pending = false;
      msg.content.failed = false;
      msg.content.progress = 100;
      msg.content.overdue = false;
      var desc = '想拍：' + (r.brief.scene || '');
      msg.content.desc = desc;
      role.lastMsg = '[照片]';
      role.lastTime = app.getClockStr();
      if (app.saveAll) app.saveAll();
      app.renderChatMessages();
      if (app._hydrateChatImages) app._hydrateChatImages();
      if (app.renderPocketChatList) app.renderPocketChatList();
      app._photoLookBack(roleId, imageId, r.src, desc);
    }).catch(function(err) {
      app._photoStopTick(imageId);
      msg.content.pending = false;
      msg.content.failed = true;
      if (app.saveAll) app.saveAll();
      app.renderChatMessages();
      if (window.console) console.log('photoV2 error', err);
    });
  };

  app._requestPhotoV2 = function(brief, role) {
    var cfg = app.getDrawCfg();
    var art = app.getArtStyle();
    var typeTpl = brief.type === '物' ? art.object : (brief.type === '景' ? art.scenery : art.person);
    var identity = app._ceIdentity(role);
    var prompt = '拍摄对象设定：' + identity + '。性别与长相必须与上述设定一致，不要改变，不要女性化或男性化。\n' +
      art.common + '\n' + typeTpl +
      '\n场景：' + (brief.scene || '') +
      (brief.light ? '\n光线：' + brief.light : '') +
      (brief.shot ? '\n镜头：' + brief.shot : '') +
      (brief.mood ? '\n情绪：' + brief.mood : '');
    return fetch(cfg.url.replace(/\/+$/, '') + '/images/generations', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + cfg.key, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: cfg.model, prompt: prompt, n: 1, size: cfg.size || '1024x1024' })
    }).then(function(res) {
      return res.text().then(function(t) {
        if (!res.ok) throw new Error('HTTP ' + res.status + ' ' + t.substring(0, 200));
        var data = JSON.parse(t);
        var item = data && data.data && data.data[0];
        if (!item) throw new Error('no image');
        if (item.url) return item.url;
        if (item.b64_json) return 'data:image/png;base64,' + item.b64_json;
        throw new Error('empty image');
      });
    });
  };

  app._photoRetry = function(roleId, imageId) {
    var msg = app._photoFindMsg(roleId, imageId);
    if (!msg || !msg.content) return;
    var c = msg.content;
    if (!c.hinted) c.hinted = true;
    c.pending = true;
    c.failed = false;
    c.progress = 2;
    c.overdue = false;
    var role = (app.roles || []).filter(function(r) { return String(r.id) === String(roleId); })[0];
    if (!role) return;
    var brief = { type: '人', scene: (c.scene || ''), light: '', shot: '', mood: '', caption: (c.text || '给你。') };
    app._photoStartTick(roleId, imageId);
    app.renderChatMessages();
    if (app.saveAll) app.saveAll();
    app._requestPhotoV2(brief, role).then(function(src) {
      return app.imageDB.save(imageId, src).then(function() { return src; });
    }).then(function(src) {
      app._photoStopTick(imageId);
      c.pending = false;
      c.failed = false;
      c.progress = 100;
      c.desc = '想拍：' + (c.scene || '');
      if (app.saveAll) app.saveAll();
      app.renderChatMessages();
      if (app._hydrateChatImages) app._hydrateChatImages();
      app._photoLookBack(roleId, imageId, src, c.desc);
    }).catch(function() {
      app._photoStopTick(imageId);
      c.pending = false;
      c.failed = true;
      if (app.saveAll) app.saveAll();
      app.renderChatMessages();
    });
  };
})();
</script>
'''


def patch_profile(h):
    old = "$('ca-name').innerText = p.name || '未命名';"
    new = "$('ca-name').innerText = (p.realName && String(p.realName).trim()) || p.name || '未命名';"
    if old in h:
        h = h.replace(old, new, 1)
    old2 = "$('ca-roma').innerText = (p.name || '').toUpperCase().replace(/\\s/g, '');"
    new2 = "$('ca-roma').innerText = ((p.realName && String(p.realName).trim()) || p.name || '').toUpperCase().replace(/\\s/g, '');"
    if old2 in h:
        h = h.replace(old2, new2, 1)

    old3 = "        if (field === 'name') {\n            this._ceWriteCharacter(roleId, function(ch) { ch.profile.name = val; });"
    new3 = ("        if (field === 'name') {\n            this._ceWriteCharacter(roleId, function(ch) {\n"
            "                var oldReal = ch.profile.realName || '';\n"
            "                var wasSame = !ch.profile.name || ch.profile.name === oldReal;\n"
            "                ch.profile.realName = val;\n"
            "                if (wasSame) ch.profile.name = val;\n"
            "            });")
    if old3 in h:
        h = h.replace(old3, new3, 1)

    old4 = "if (field === 'name') { val = c.profile ? (c.profile.name || '') : ''; if (_ph) _ph.placeholder = '角色的名字（必填）'; }"
    new4 = "if (field === 'name') { val = c.profile ? (c.profile.realName || c.profile.name || '') : ''; if (_ph) _ph.placeholder = '角色的真名（必填）。加好友时填的昵称不会改到这里。'; }"
    if old4 in h:
        h = h.replace(old4, new4, 1)

    start = h.find("if (_ph) _ph.placeholder = '这里只写「他是谁」")
    if start > 0:
        end = h.find("';")
        end = h.find("';", start)
        if end > start:
            new_ph = ("if (_ph) _ph.placeholder = '按下面的格式写，没写的小节留空即可。标签原样使用，写错就读不到。\\n\\n"
                      "【外貌】\\n只写看得见的：性别、年龄、身高、发型、脸型五官、体型、常穿的衣服、气质。60-80字，不写性格。\\n\\n"
                      "【核心】\\n性格底色 + 职业或身份，以及他为什么会变成现在这样。300字内。只写结论，具体事件放「角色经历」。\\n\\n"
                      "【日常】\\n他日常的相处方式：怎么开口、多久回复、怎么表现关心、习惯性的小动作、平时爱聊什么、什么时候主动找你。不写城市和地理。\\n\\n"
                      "【XP】\\n亲密相关的偏好、边界与不喜欢的事。没写就不启用。'")
            h = h[:start] + new_ph + h[end + 2:]
    return h


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if MARK in h:
        print('already patched, skip')
        return

    h = patch_profile(h)

    if A1 not in h:
        print('anchor1 missing'); sys.exit(1)
    h = h.replace(A1, A1_NEW, 1)

    if A2 not in h:
        print('anchor2 missing'); sys.exit(1)
    h = h.replace(A2, A2_NEW, 1)

    if A3 not in h:
        print('anchor3 missing'); sys.exit(1)
    h = h.replace(A3, A3_NEW, 1)

    if '</body>' not in h:
        print('body missing'); sys.exit(1)
    h = h.replace('</body>', V2_SCRIPT + '</body>', 1)

    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('patched, new length', len(h))


if __name__ == '__main__':
    main()
