#!/usr/bin/env python3
# 为《屿野来信》接入「画风设置 + 聊天拍照」流程
import sys, io

PATH = 'index.html'

ART_PANEL = '''<!-- art style settings panel -->
<div class="view-panel" id="art-style-config-view" style="--app-label:'SETTINGS'">
    <div class="nav-header">
        <div class="nav-back-btn" onclick="app.navigateTo('settings')"></div>
        <div class="nav-title">画风</div>
        <div class="nav-action-btn" onclick="app.saveArtStyle()" style="font-size:14px;">保存</div>
    </div>
    <div style="padding:20px 16px;display:flex;flex-direction:column;gap:16px;">
        <div style="font-size:12px;color:var(--text-sub);line-height:1.7;">画风只管照片的味道。拍什么由 AI 根据聊天现场决定，不用你写。</div>
        <div>
            <div style="font-size:12px;color:var(--text-sub);margin-bottom:8px;">公共约束（三类共用）</div>
            <textarea id="art-common" class="settings-input" rows="4" style="resize:none;"></textarea>
        </div>
        <div>
            <div style="font-size:12px;color:var(--text-sub);margin-bottom:8px;">拍人</div>
            <textarea id="art-person" class="settings-input" rows="5" style="resize:none;"></textarea>
        </div>
        <div>
            <div style="font-size:12px;color:var(--text-sub);margin-bottom:8px;">拍物</div>
            <textarea id="art-object" class="settings-input" rows="3" style="resize:none;"></textarea>
        </div>
        <div>
            <div style="font-size:12px;color:var(--text-sub);margin-bottom:8px;">拍风景</div>
            <textarea id="art-scenery" class="settings-input" rows="3" style="resize:none;"></textarea>
        </div>
        <button class="settings-test-btn" onclick="app.resetArtStyle()">恢复默认</button>
    </div>
</div>

'''

ART_ROW = '''            <div class="settings-list-row" onclick="app.navigateTo('art-style-config-view');app.fillArtStyle()">
                <div class="settings-row-left">
                    <div class="settings-row-icon" style="background-color: #E8EEF6;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="#6B7F9E"><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><path d="M21 15l-5-5L5 21"></path></svg>
                    </div>
                    <div class="settings-row-title">画风</div>
                </div>
                <div class="settings-row-right">
                    <span class="settings-row-status settings-status-none">照片风格</span>
                    <span class="settings-chevron">›</span>
                </div>
            </div>

'''

NEW_JS = r'''
    // ===== 画风设置 =====
    _artDefaults: function() {
        return {
            common: '真实拍摄感，不是插画，不是3D渲染。轻微噪点，构图不必完美。不要过度磨皮，不要水印和文字。手机实拍，非精修，非广告片质感。',
            person: '人物必须与参考图一致，五官、发型、年龄感不得改变。日常光线，皮肤保留真实纹理。背景、动作、穿着按场景来，不预设氛围。',
            object: '静物实拍，自然光，浅景深，主体清晰，背景略虚，桌面或手持视角。',
            scenery: '真实景观，自然光，不过度饱和，手机广角视角，允许杂物入镜。'
        };
    },
    getArtStyle: function() {
        var d = app._artDefaults();
        var s = null;
        try { s = JSON.parse(localStorage.getItem('pk_art_style') || 'null'); } catch (e) {}
        s = s || {};
        return {
            common: s.common || d.common,
            person: s.person || d.person,
            object: s.object || d.object,
            scenery: s.scenery || d.scenery
        };
    },
    fillArtStyle: function() {
        var s = app.getArtStyle();
        var ids = { common: 'art-common', person: 'art-person', object: 'art-object', scenery: 'art-scenery' };
        Object.keys(ids).forEach(function(k) {
            var el = document.getElementById(ids[k]);
            if (el) el.value = s[k];
        });
    },
    saveArtStyle: function() {
        var s = {
            common: (document.getElementById('art-common') || {}).value || '',
            person: (document.getElementById('art-person') || {}).value || '',
            object: (document.getElementById('art-object') || {}).value || '',
            scenery: (document.getElementById('art-scenery') || {}).value || ''
        };
        localStorage.setItem('pk_art_style', JSON.stringify(s));
        app.showModal('提示', '画风已保存', '确定');
    },
    resetArtStyle: function() {
        localStorage.removeItem('pk_art_style');
        app.fillArtStyle();
        app.showModal('提示', '已恢复默认画风，记得点保存', '确定');
    },

    // ===== 聊天拍照 =====
    _isPhotoRequest: function(text) {
        if (!text) return false;
        return /自拍|拍张照|拍个照|拍一张|发张照片|发张图|近照|拍张自拍/.test(text);
    },
    _startPhotoFlow: function(role, text, input) {
        var roleId = role.id;
        if (!app.chats[roleId]) app.chats[roleId] = [];
        var now = app._ceNow ? app._ceNow() : Date.now();
        app.chats[roleId].push({ sender: 'user', msgType: 'text', content: { text: text }, ts: now });
        role.lastMsg = text;
        role.lastTime = app.getClockStr();
        role.lastChatTime = now;
        if (input) input.value = '';
        app.renderChatMessages();
        app.saveAll();
        app.renderPocketChatList();

        var phTs = (app._ceNow ? app._ceNow() : Date.now()) + 1;
        app.chats[roleId].push({ sender: 'ai', msgType: 'text', content: { text: '正在拍照…' }, ts: phTs });
        app.renderChatMessages();

        app._buildPhotoBrief(role, text).then(function(brief) {
            return app._requestPhoto(brief).then(function(src) {
                return { brief: brief, src: src };
            });
        }).then(function(r) {
            var imageId = 'photo_' + Date.now();
            return app.imageDB.save(imageId, r.src).then(function() {
                return { imageId: imageId, brief: r.brief, src: r.src };
            });
        }).then(function(r) {
            var msgs = app.chats[roleId] || [];
            for (var i = 0; i < msgs.length; i++) {
                if (msgs[i].ts === phTs) {
                    msgs[i].content.text = r.brief.caption || '给你。';
                    break;
                }
            }
            var desc = '想拍：' + (r.brief.scene || '');
            msgs.push({ sender: 'ai', msgType: 'image', content: { imageId: r.imageId, desc: desc, text: r.brief.caption || '' }, ts: (app._ceNow ? app._ceNow() : Date.now()) });
            role.lastMsg = '[照片]';
            role.lastTime = app.getClockStr();
            app.saveAll();
            app.renderChatMessages();
            if (app._hydrateChatImages) app._hydrateChatImages();
            app.renderPocketChatList();
            app._photoLookBack(roleId, r.imageId, r.src, desc);
        }).catch(function(err) {
            var msgs = app.chats[roleId] || [];
            for (var i = 0; i < msgs.length; i++) {
                if (msgs[i].ts === phTs) {
                    msgs[i].content.text = '今天光不好，拍糊了，回头再给你拍。';
                    break;
                }
            }
            app.saveAll();
            app.renderChatMessages();
            if (window.console) console.log('photo flow error', err);
        });
    },
    _buildPhotoBrief: function(role, userText) {
        var fallback = { type: '人', scene: userText, light: '', shot: '前置自拍，略高角度', mood: '', caption: '给你。' };
        var cfg = app.config || {};
        if (!cfg.key || !cfg.url) return Promise.resolve(fallback);
        var sys = '你是拍照指令生成器。根据对话，输出一个JSON对象，不要输出任何其他文字。字段：type（只能是"人""物""景"之一）、scene（场景，30字内，只写与主体有关的）、light（光线，20字内）、shot（镜头，15字内）、mood（情绪，10字内）、caption（角色发照片时配的一句话，20字内，口语）。';
        var user = '角色：' + (role.name || '对方') + '。用户说：' + userText + '。请生成拍照指令。';
        return fetch(cfg.url.replace(/\/+$/, '') + '/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + cfg.key },
            body: JSON.stringify({ model: cfg.model, messages: [{ role: 'system', content: sys }, { role: 'user', content: user }], temperature: 0.7 })
        }).then(function(res) { return res.json(); }).then(function(data) {
            var txt = data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
            if (!txt) return fallback;
            var m = txt.match(/\{[\s\S]*\}/);
            if (!m) return fallback;
            var o = JSON.parse(m[0]);
            return {
                type: o.type || '人',
                scene: o.scene || userText,
                light: o.light || '',
                shot: o.shot || '',
                mood: o.mood || '',
                caption: o.caption || '给你。'
            };
        }).catch(function() { return fallback; });
    },
    _requestPhoto: function(brief) {
        var cfg = app.getDrawCfg();
        var art = app.getArtStyle();
        var typeTpl = brief.type === '物' ? art.object : (brief.type === '景' ? art.scenery : art.person);
        var prompt = art.common + '\n' + typeTpl +
            '\n场景：' + brief.scene +
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
    },
    _photoLookBack: function(roleId, imageId, src, desc) {
        var v = app.getVisionCfg ? app.getVisionCfg() : null;
        if (!v || !v.key || !v.url) return;
        var body = {
            model: v.model,
            messages: [{ role: 'user', content: [
                { type: 'text', text: '用一句中文描述这张照片里实际拍到了什么，40字以内，只说画面内容。' },
                { type: 'image_url', image_url: { url: src } }
            ] }]
        };
        fetch(v.url.replace(/\/+$/, '') + '/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + v.key },
            body: JSON.stringify(body)
        }).then(function(res) { return res.json(); }).then(function(data) {
            var txt = data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
            if (!txt) return;
            var msgs = app.chats[roleId] || [];
            for (var i = msgs.length - 1; i >= 0; i--) {
                if (msgs[i].msgType === 'image' && msgs[i].content && msgs[i].content.imageId === imageId) {
                    msgs[i].content.desc = desc + '；画面：' + txt.trim();
                    break;
                }
            }
            app.saveAll();
        }).catch(function() {});
    },

'''

HOOK = """    if (app._isPhotoRequest && app._isPhotoRequest(text) && app.getDrawCfg && app.getDrawCfg().key) {
        app._startPhotoFlow(role, text, input);
        return;
    }
"""


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if '_startPhotoFlow' in h:
        print('already patched, skip')
        return

    anchor_row = "            <div class=\"settings-list-row\" onclick=\"app.navigateTo('xp-mode-config-view')\">"
    if anchor_row not in h:
        print('settings row anchor missing'); sys.exit(1)
    h = h.replace(anchor_row, ART_ROW + anchor_row, 1)

    anchor_panel = '<!-- draw settings panel -->'
    if anchor_panel not in h:
        print('panel anchor missing'); sys.exit(1)
    h = h.replace(anchor_panel, ART_PANEL + anchor_panel, 1)

    anchor_js = '    // draw config (OpenAI compatible relay)'
    if anchor_js not in h:
        print('js anchor missing'); sys.exit(1)
    h = h.replace(anchor_js, NEW_JS + anchor_js, 1)

    anchor_send = "    var explicitPhoneRequest = app._isExplicitPhoneCallRequest(text);"
    if anchor_send not in h:
        print('send anchor missing'); sys.exit(1)
    h = h.replace(anchor_send, HOOK + anchor_send, 1)

    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('patched, new length', len(h))


if __name__ == '__main__':
    main()
