#!/usr/bin/env python3
# add draw-api settings page to index.html (OpenAI-compatible relay, e.g. breadog.cn)
# v2
import sys, io

PATH = 'index.html'

NEW_PANEL = '''<!-- draw settings panel -->
<div class="view-panel" id="api-draw-config-view" style="--app-label:'SETTINGS'">
    <div class="nav-header">
        <div class="nav-back-btn" onclick="app.navigateTo('settings')"></div>
        <div class="nav-title">生图</div>
        <div class="nav-action-btn" onclick="app.saveDrawConfig()" style="font-size:14px;">保存</div>
    </div>
    <div style="padding:20px 16px;display:flex;flex-direction:column;gap:16px;">
        <div>
            <div style="font-size:12px;color:var(--text-sub);margin-bottom:8px;">API Key</div>
            <input type="password" id="draw-key" autocomplete="off" class="settings-input" placeholder="输入中转站 API Key">
        </div>
        <div>
            <div style="font-size:12px;color:var(--text-sub);margin-bottom:8px;">Base URL</div>
            <input type="text" id="draw-base-url" class="settings-input" value="https://breadog.cn/v1" placeholder="https://breadog.cn/v1">
        </div>
        <div>
            <div style="font-size:12px;color:var(--text-sub);margin-bottom:8px;">模型名称</div>
            <input type="text" id="draw-model" class="settings-input" placeholder="gpt-image-1 / doubao-seedream-4-5" value="gpt-image-1">
        </div>
        <div>
            <div style="font-size:12px;color:var(--text-sub);margin-bottom:8px;">尺寸</div>
            <select id="draw-size" class="settings-input">
                <option value="1024x1024">方形 1024×1024</option>
                <option value="1024x1792">竖版 1024×1792</option>
                <option value="1792x1024">横版 1792×1024</option>
            </select>
        </div>
        <button class="settings-test-btn" onclick="app.testDrawConfig()">测试连接</button>
        <div style="height:1px;background:var(--border-light,#eee);margin:6px 0;"></div>
        <div>
            <div style="font-size:12px;color:var(--text-sub);margin-bottom:8px;">试画一张</div>
            <textarea id="draw-prompt" class="settings-input" rows="3" placeholder="描述你想要的画面" style="resize:none;"></textarea>
        </div>
        <button class="settings-test-btn" onclick="app.generateImageTest()">生成</button>
        <div id="draw-result" style="font-size:13px;color:var(--text-sub);line-height:1.6;"></div>
    </div>
</div>

'''

NEW_JS = r'''
    // draw config (OpenAI compatible relay)
    getDrawCfg: function() {
        return JSON.parse(localStorage.getItem('pk_draw_cfg') || 'null') ||
            { key: '', url: 'https://breadog.cn/v1', model: 'gpt-image-1', size: '1024x1024' };
    },
    fillDrawForm: function() {
        var c = app.getDrawCfg();
        var k = document.getElementById('draw-key'), u = document.getElementById('draw-base-url');
        var m = document.getElementById('draw-model'), s = document.getElementById('draw-size');
        if (k) k.value = c.key || '';
        if (u) u.value = c.url || 'https://breadog.cn/v1';
        if (m) m.value = c.model || 'gpt-image-1';
        if (s) s.value = c.size || '1024x1024';
    },
    saveDrawConfig: function() {
        var key = (document.getElementById('draw-key') || {}).value || '';
        var url = (document.getElementById('draw-base-url') || {}).value || '';
        var model = (document.getElementById('draw-model') || {}).value || '';
        var size = (document.getElementById('draw-size') || {}).value || '1024x1024';
        url = url.trim().replace(/\/+$/, '');
        localStorage.setItem('pk_draw_cfg', JSON.stringify({
            key: key.trim(), url: url || 'https://breadog.cn/v1',
            model: model.trim() || 'gpt-image-1', size: size
        }));
        app.showModal('提示', '生图设置已保存', '确定');
    },
    testDrawConfig: function() {
        var c = app.getDrawCfg();
        var key = (document.getElementById('draw-key') || {}).value || c.key;
        var url = ((document.getElementById('draw-base-url') || {}).value || c.url).trim().replace(/\/+$/, '');
        key = key.trim();
        if (!key) { app.showModal('提示', '请先填写 API Key', '确定'); return; }
        app.showModal('测试中', '正在连接中转站...', '确定');
        fetch(url + '/models', { headers: { 'Authorization': 'Bearer ' + key } })
            .then(function(res) {
                if (res.status === 401 || res.status === 403) {
                    app.showModal('测试失败', 'API Key 无效或无权限（HTTP ' + res.status + '）', '确定');
                    return;
                }
                return res.text().then(function(t) {
                    if (res.ok) {
                        app.showModal('接口可达', '中转站已响应，API Key 有效。\n' + t.substring(0, 120), '确定');
                    } else {
                        app.showModal('测试结果', 'HTTP ' + res.status + '\n' + t.substring(0, 240), '确定');
                    }
                });
            })
            .catch(function(err) {
                app.showModal('测试失败', '网络或跳域错误：' + err.message, '确定');
            });
    },
    generateImageTest: function() {
        var c = app.getDrawCfg();
        var key = (document.getElementById('draw-key') || {}).value || c.key;
        var url = ((document.getElementById('draw-base-url') || {}).value || c.url).trim().replace(/\/+$/, '');
        var model = ((document.getElementById('draw-model') || {}).value || c.model).trim();
        var size = (document.getElementById('draw-size') || {}).value || c.size;
        var prompt = ((document.getElementById('draw-prompt') || {}).value || '').trim();
        var out = document.getElementById('draw-result');
        key = key.trim();
        if (!key) { app.showModal('提示', '请先填写 API Key', '确定'); return; }
        if (!prompt) { app.showModal('提示', '先写一句描述', '确定'); return; }
        if (out) out.innerHTML = '生成中，通常需要 10-40 秒...';
        fetch(url + '/images/generations', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: model, prompt: prompt, n: 1, size: size })
        }).then(function(res) {
            return res.text().then(function(t) {
                var data = null;
                try { data = JSON.parse(t); } catch (e) {}
                if (!res.ok) {
                    if (out) out.innerHTML = '失败：HTTP ' + res.status + '<br>' + t.substring(0, 300).replace(/</g, '&lt;');
                    return;
                }
                var item = data && data.data && data.data[0];
                var src = null;
                if (item) {
                    if (item.url) src = item.url;
                    else if (item.b64_json) src = 'data:image/png;base64,' + item.b64_json;
                }
                if (!src) {
                    if (out) out.innerHTML = '返回里没有图片：<br>' + t.substring(0, 300).replace(/</g, '&lt;');
                    return;
                }
                if (out) {
                    out.innerHTML = '<img src="' + src + '" style="width:100%;border-radius:12px;display:block;" alt="generated">' +
                        '<div style="margin-top:8px;font-size:12px;color:var(--text-sub);">长按图片可保存到相册</div>';
                }
            });
        }).catch(function(err) {
            if (out) out.innerHTML = '网络或跳域错误：' + err.message.replace(/</g, '&lt;');
        });
    },

'''

def main():
    h = io.open(PATH, encoding='utf-8').read()
    if 'generateImageTest' in h:
        print('already patched, skip')
        return
    if '<!-- 生图占位页 -->' not in h:
        print('anchor missing, abort')
        sys.exit(1)

    m1 = h.index('<!-- 生图占位页 -->')
    m2 = h.index('<!-- 语音识别设置页 -->')
    h = h[:m1] + NEW_PANEL + h[m2:]

    anchor = '    saveAsrConfig: function() {'
    if anchor not in h:
        print('js anchor missing, abort')
        sys.exit(1)
    h = h.replace(anchor, NEW_JS + anchor, 1)

    boot = '''<script>
(document.addEventListener('click', function(e){
  var t = e.target && e.target.closest ? e.target.closest('[onclick*="api-draw-config-view"]') : null;
  if (t) setTimeout(function(){ try { app.fillDrawForm(); } catch(err) {} }, 120);
}, true));
</script>
'''
    if '</body>' in h:
        h = h.replace('</body>', boot + '</body>', 1)
    else:
        h = h + boot

    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('patched, new length', len(h))

if __name__ == '__main__':
    main()
