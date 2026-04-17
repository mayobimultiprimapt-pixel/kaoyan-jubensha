/* shared boot: 全局错误边界 + 键盘无障碍委托 + Service Worker 注册
   各目录的 data/boot.js 是本文件的副本，由 _sync_boot.py 同步。
   请勿直接编辑副本——修改后重跑脚本。
   通过 <script src="data/boot.js"></script> 在 <head> 内尽早加载。
*/
(function(){
  function show(msg){try{
    var d=document.getElementById('_err_toast');
    if(!d){
      d=document.createElement('div');d.id='_err_toast';
      d.style.cssText='position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:rgba(139,0,0,.95);color:#fff5e0;padding:10px 18px;border-radius:4px;z-index:99999;font-size:13px;letter-spacing:1px;max-width:92vw;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.5);font-family:inherit';
      (document.body||document.documentElement).appendChild(d);
    }
    d.textContent='⚠ 发生错误：'+msg+'（详情见 Console）';
    clearTimeout(d._t);d._t=setTimeout(function(){try{d.remove()}catch(_){}},7000);
  }catch(_){}}
  window.addEventListener('error',function(e){
    console.error('[error]',e);
    var loc=e.filename?' @ '+String(e.filename).split('/').pop()+':'+e.lineno:'';
    show((e.message||'未知错误')+loc);
  });
  window.addEventListener('unhandledrejection',function(e){
    console.error('[promise]',e.reason);
    show(String((e.reason&&(e.reason.message||e.reason))||'Promise 被拒'));
  });

  // Enter/Space 触发 [data-kbd] 元素的 click（键盘无障碍）
  document.addEventListener('keydown',function(e){
    if((e.key==='Enter'||e.key===' ')&&e.target&&e.target.matches&&e.target.matches('[data-kbd]')){
      e.preventDefault();e.target.click();
    }
  });

  // Service Worker 注册
  if('serviceWorker' in navigator){
    window.addEventListener('load',function(){
      navigator.serviceWorker.register('sw.js').catch(function(){});
    });
  }
})();
