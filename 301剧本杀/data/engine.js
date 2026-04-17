/* shared engine: Web Audio 音效 + 多轨 BGM + 通用工具函数
   各目录的 data/engine.js 是本文件的副本，由 _sync_engine.py 同步。
   依赖：运行时需要全局 BGM_TRACKS（各科独有，留在 HTML）、state（游戏状态）。
   不要直接编辑副本——修改后重跑脚本。
*/

// ============ Web Audio 音效引擎 ============
let ac=null, sfxOn=true, bgmOn=false;
let bgmNodes=[], bgmSchedulerId=null, currentBgm=null, bgmGainNode=null;
function initAudio(){
    if(!ac){
        try{ac=new (window.AudioContext||window.webkitAudioContext)()}catch(e){ac=null}
    }
}
function tone(freq,dur,type,vol,when){
    if(!sfxOn||!ac) return;
    type=type||'sine';vol=vol==null?.2:vol;when=when||0;
    const o=ac.createOscillator(),g=ac.createGain();
    o.type=type;o.frequency.setValueAtTime(freq,ac.currentTime+when);
    g.gain.setValueAtTime(0,ac.currentTime+when);
    g.gain.linearRampToValueAtTime(vol,ac.currentTime+when+0.01);
    g.gain.exponentialRampToValueAtTime(0.0005,ac.currentTime+when+dur);
    o.connect(g);g.connect(ac.destination);
    o.start(ac.currentTime+when);o.stop(ac.currentTime+when+dur+0.05);
}
function sfxCorrect(){initAudio();[523.25,659.25,783.99].forEach((f,i)=>tone(f,.35,'sine',.18,i*.08))}
function sfxWrong(){initAudio();tone(185,.3,'sawtooth',.2);tone(155,.5,'sawtooth',.15,.1)}
function sfxBadge(){initAudio();[392,523.25,659.25,783.99,1046.5].forEach((f,i)=>tone(f,.25,'triangle',.2,i*.07))}
function sfxDing(){initAudio();tone(1568,.25,'sine',.12);tone(2093,.35,'sine',.08,.05)}
function sfxDoor(){initAudio();tone(55,2.2,'sawtooth',.12);[220,330,440].forEach((f,i)=>tone(f,1.8,'sine',.1,.3+i*.2))}
function sfxClick(){initAudio();tone(880,.05,'square',.06)}
function sfxSelect(){initAudio();tone(660,.08,'sine',.1)}
function toggleSfx(){sfxOn=!sfxOn;document.getElementById('btn-sfx').classList.toggle('active',sfxOn);document.getElementById('btn-sfx').textContent=sfxOn?'🔊':'🔇';if(sfxOn)sfxClick()}

// ============ 多轨 BGM 引擎 ============
const NOTES={
    A1:55.00,As1:58.27,B1:61.74,
    C2:65.41,Cs2:69.30,D2:73.42,Ds2:77.78,E2:82.41,F2:87.31,Fs2:92.50,G2:98.00,Gs2:103.83,A2:110.00,As2:116.54,B2:123.47,
    C3:130.81,Cs3:138.59,D3:146.83,Ds3:155.56,E3:164.81,F3:174.61,Fs3:185.00,G3:196.00,Gs3:207.65,A3:220.00,As3:233.08,B3:246.94,
    C4:261.63,Cs4:277.18,D4:293.66,Ds4:311.13,E4:329.63,F4:349.23,Fs4:369.99,G4:392.00,Gs4:415.30,A4:440.00,As4:466.16,B4:493.88,
    C5:523.25,Cs5:554.37,D5:587.33,Ds5:622.25,E5:659.25,F5:698.46,Fs5:739.99,G5:783.99,Gs5:830.61,A5:880.00,As5:932.33,B5:987.77,
    C6:1046.50,D6:1174.66,E6:1318.51,F6:1396.91,G6:1567.98,A6:1760.00,
    REST:0
};
function initBgmGain(){
    if(!ac)return;
    if(!bgmGainNode){
        bgmGainNode=ac.createGain();
        bgmGainNode.gain.value=0.6;
        bgmGainNode.connect(ac.destination);
    }
}
function bgmTone(freq,startTime,duration,type,vol){
    if(!ac||!bgmGainNode||!freq||freq<=0)return;
    type=type||'sine';vol=vol==null?0.05:vol;
    const o=ac.createOscillator(),g=ac.createGain();
    o.type=type;o.frequency.setValueAtTime(freq,startTime);
    g.gain.setValueAtTime(0,startTime);
    g.gain.linearRampToValueAtTime(vol,startTime+0.04);
    g.gain.linearRampToValueAtTime(vol*0.65,startTime+duration*0.6);
    g.gain.exponentialRampToValueAtTime(0.0005,startTime+duration);
    o.connect(g);g.connect(bgmGainNode);
    o.start(startTime);o.stop(startTime+duration+0.08);
    bgmNodes.push({o,g});
}
function playTrack(track,t0,beatLen){
    const totalDur=track.loopBeats*beatLen;
    (track.drones||[]).forEach(dr=>{
        bgmTone(NOTES[dr.n],t0,totalDur,dr.t||'sine',dr.v||0.04);
    });
    let t=t0;
    (track.melody||[]).forEach(m=>{
        const dur=m.d*beatLen;
        if(m.n&&m.n!=='REST'&&NOTES[m.n]) bgmTone(NOTES[m.n],t,dur*0.95,m.t||'triangle',m.v||0.05);
        t+=dur;
    });
    if(track.bass){
        let bt=t0;
        track.bass.forEach(m=>{
            const dur=m.d*beatLen;
            if(m.n&&m.n!=='REST'&&NOTES[m.n]) bgmTone(NOTES[m.n],bt,dur*0.95,m.t||'sine',m.v||0.04);
            bt+=dur;
        });
    }
}
function startBgmTrack(trackId){
    if(!trackId)return;
    if(currentBgm===trackId)return;
    stopBgmAll(true);
    if(!bgmOn||!ac)return;
    currentBgm=trackId;
    const track=BGM_TRACKS[trackId];
    if(!track)return;
    initBgmGain();
    const beatLen=60/track.tempo;
    const loopLen=track.loopBeats*beatLen;
    const loop=()=>{
        if(!bgmOn||currentBgm!==trackId||!ac)return;
        const startAt=ac.currentTime+0.05;
        playTrack(track,startAt,beatLen);
        const nowTime=ac.currentTime;
        bgmNodes=bgmNodes.filter(n=>{try{return nowTime<(n.o.endTime||nowTime+30)}catch(e){return false}});
        bgmSchedulerId=setTimeout(loop,loopLen*1000-80);
    };
    loop();
}
function stopBgmAll(crossfade){
    if(bgmSchedulerId){clearTimeout(bgmSchedulerId);bgmSchedulerId=null}
    currentBgm=null;
    if(!ac)return;
    const now=ac.currentTime;const fade=crossfade?0.6:0.3;
    bgmNodes.forEach(n=>{
        try{
            n.g.gain.cancelScheduledValues(now);
            n.g.gain.setValueAtTime(n.g.gain.value||0.05,now);
            n.g.gain.linearRampToValueAtTime(0.0001,now+fade);
            n.o.stop(now+fade+0.05);
        }catch(e){}
    });
    bgmNodes=[];
}
function applyBgm(){
    if(!bgmOn||!ac)return;
    let id='title';
    if(state.stage==='title')id='title';
    else if(state.stage==='prologue')id='prologue';
    else if(state.stage==='sandbox')id='sandbox';
    else if(state.stage==='zone'||state.stage==='room'){const z=state.currentZone;if(z)id='zone_'+z}
    else if(state.stage==='deduction')id='deduction';
    else if(state.stage==='finale')id='finale';
    else if(state.stage==='ending')id='ending_'+(state.ending||'B');
    startBgmTrack(id);
}
function toggleBgm(){
    initAudio();
    bgmOn=!bgmOn;
    const btn=document.getElementById('btn-bgm');
    btn.classList.toggle('active',bgmOn);
    btn.textContent=bgmOn?'🎵':'🎶';
    if(bgmOn){applyBgm();const t=BGM_TRACKS[currentBgm];showToast('🎵 BGM 开启 · '+(t?t.name:''))}
    else{stopBgmAll();showToast('🎶 BGM 已关闭')}
}

// ============ 通用工具 ============
function showToast(msg){
    const t=document.createElement('div');
    t.style.cssText='position:fixed;top:30px;left:50%;transform:translateX(-50%);background:rgba(212,175,55,.95);color:#0a0a0a;padding:12px 30px;border-radius:3px;z-index:9999;font-size:15px;letter-spacing:2px;box-shadow:0 4px 20px rgba(0,0,0,.5)';
    t.textContent=msg;document.body.appendChild(t);setTimeout(()=>t.remove(),2000);
}
function normalize(s){return String(s||'').trim().toLowerCase().replace(/[\s，。、,\.\/\-·]+/g,'')}
function checkFill(puzzle,userInput){
    const u=normalize(userInput);
    return puzzle.a.some(a=>{const na=normalize(a);return na===u||u.indexOf(na)>=0||(na.indexOf(u)>=0&&u.length>=2)});
}
