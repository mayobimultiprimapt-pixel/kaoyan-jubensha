/* shared game: 存档模块 + Sidebar 增量渲染
   各目录的 data/game.js 是本文件的副本，由 _sync_game.py 同步。
   请勿直接编辑副本 —— 修改后重跑脚本。

   依赖（运行时由 HTML 主 inline script 提供）：
     - 全局 SAVE_SUBJECT（'101' / '201' / '301' / '408'）
     - 全局 state（游戏状态对象）
     - 全局 ZONES / ROOMS（由 data/rooms.js 提供）
     - 全局 showToast / sfxDing（由 data/engine.js 提供）
     - 全局 renderStage / computeGrade（由 HTML 主 inline script 定义）
*/

// ============ 存档 ============
const SAVE_LEGACY_KEY='101_rpg_save';   // 旧版统一键名（历史遗留）
const SAVE_VERSION=2;
function _saveKey(){return 'exam_'+SAVE_SUBJECT+'_progress'}
function _patchLoadedState(){if(!state.puzzleFirstTry)state.puzzleFirstTry={};if(state.deduction===undefined)state.deduction=null}
function _writeSave(){try{localStorage.setItem(_saveKey(),JSON.stringify({v:SAVE_VERSION,subject:SAVE_SUBJECT,savedAt:new Date().toISOString(),data:state}));return true}catch(e){return false}}
function hasSave(){try{return !!(localStorage.getItem(_saveKey())||localStorage.getItem(SAVE_LEGACY_KEY))}catch(e){return false}}
function saveGame(silent){
    if(_writeSave()){
        try{localStorage.removeItem(SAVE_LEGACY_KEY)}catch(e){}
        if(!silent){showToast('💾 已存档');sfxDing()}
    }else if(!silent){showToast('⚠️ 存档失败：存储空间不足')}
}
function loadGame(){
    try{
        const s=localStorage.getItem(_saveKey());
        if(s){
            const p=JSON.parse(s);
            if(p&&p.data){state=p.data;_patchLoadedState();return true}
        }
        const legacy=localStorage.getItem(SAVE_LEGACY_KEY);
        if(legacy){
            state=JSON.parse(legacy);_patchLoadedState();
            _writeSave();try{localStorage.removeItem(SAVE_LEGACY_KEY)}catch(e){}
            return true;
        }
    }catch(e){}return false;
}
function resetGame(){
    if(confirm('确定要重新开始吗？所有进度将丢失。')){
        try{localStorage.removeItem(_saveKey())}catch(e){}
        try{localStorage.removeItem(SAVE_LEGACY_KEY)}catch(e){}
        state={stage:'title',currentZone:null,currentRoom:null,badges:[],keys:[],clues:[],visited:{},ending:null,flags:{},startDate:null,puzzleFirstTry:{},deduction:null};
        renderStage();renderSidebar();
    }
}

// ============ Sidebar 增量渲染 (首次构建骨架，后续只 diff 变化节点) ============
const _sb={built:false,badges:{},keys:{},clueCount:0};
const NB_EMPTY_HTML='<div class="nb-empty" style="color:#888;font-style:italic;text-align:center;padding:10px">尚未发现线索...</div>';
function _getTotalBadges(){return Object.keys(ZONES).reduce((s,z)=>s+ZONES[z].count,0)}
function _buildSidebarSkeleton(){
    const bs=document.getElementById('badges');
    const bf=document.createDocumentFragment();
    Object.keys(ZONES).forEach(z=>{
        for(let i=1;i<=ZONES[z].count;i++){
            const id=z+i;
            const el=document.createElement('div');
            el.className='badge';el.dataset.id=id;el.textContent='·';
            el.title=`${id} · 未获得`;
            bf.appendChild(el);_sb.badges[id]=el;
        }
    });
    bs.innerHTML='';bs.appendChild(bf);

    const ks=document.getElementById('keys');
    const kf=document.createDocumentFragment();
    Object.keys(ZONES).forEach(z=>{
        const el=document.createElement('div');
        el.className='key';el.dataset.id=z;el.textContent='·';
        el.title=ZONES[z].key;
        kf.appendChild(el);_sb.keys[z]=el;
    });
    ks.innerHTML='';ks.appendChild(kf);

    _sb.built=true;_sb.clueCount=0;
    document.getElementById('notebook').innerHTML=NB_EMPTY_HTML;
}
function renderSidebar(){
    if(!_sb.built)_buildSidebarSkeleton();
    const totalBadges=state.badges.length;
    const TOTAL=_getTotalBadges();
    document.getElementById('badge-count').textContent=`${totalBadges}/${TOTAL}`;
    const pi=document.getElementById('progress-info');
    if(state.stage==='title')pi.textContent='尚未开始';
    else if(state.stage==='prologue')pi.textContent='序幕进行中...';
    else if(state.stage==='sandbox')pi.textContent=`调查中 · 已收集 ${totalBadges}/${TOTAL} 徽章`;
    else if(state.stage==='zone'||state.stage==='room')pi.textContent=`探索 ${ZONES[state.currentZone]?.name||'...'}`;
    else if(state.stage==='deduction')pi.textContent=state.deduction?`☗ 推理厅 · ${state.deduction.correctCount}/${state.deduction.total} 命中`:'☗ 推理厅进行中...';
    else if(state.stage==='finale')pi.textContent='终章进行中...';
    else pi.textContent=`通关结局 ${state.ending} · ${computeGrade().rankLabel}`;

    const earnedSet=new Set(state.badges);
    for(const id in _sb.badges){
        const el=_sb.badges[id];
        const want=earnedSet.has(id);
        if(want!==el.classList.contains('earned')){
            const r=ROOMS[id];
            el.classList.toggle('earned',want);
            el.title=want?`${id} · ${r.badge}`:`${id} · 未获得`;
            el.textContent=want?ZONES[r.zone].icon:'·';
        }
    }

    const keySet=new Set(state.keys);
    for(const z in _sb.keys){
        const el=_sb.keys[z];
        const want=keySet.has(z);
        if(want!==el.classList.contains('earned')){
            el.classList.toggle('earned',want);
            el.textContent=want?'🗝':'·';
        }
    }

    const nb=document.getElementById('notebook');
    if(state.clues.length<_sb.clueCount){
        _sb.clueCount=0;nb.innerHTML=NB_EMPTY_HTML;
    }
    if(state.clues.length>_sb.clueCount){
        if(_sb.clueCount===0)nb.innerHTML='';
        for(let i=_sb.clueCount;i<state.clues.length;i++){
            const c=state.clues[i];const r=ROOMS[c.rid];
            const div=document.createElement('div');div.className='clue-entry';
            const head=document.createElement('div');head.className='clue-entry-room';
            head.textContent=`${c.rid} · ${r.title}`;
            const body=document.createElement('div');body.textContent=c.text;
            div.appendChild(head);div.appendChild(body);
            nb.insertBefore(div,nb.firstChild);
        }
        _sb.clueCount=state.clues.length;
    }
}
