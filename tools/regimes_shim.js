(function(){
  var RAW=__RAW__, CALCS={}, DRAWS={}, STATE=new Map(), cache={};
  function ok(d){ var r={status:'ok',data:d,message:null,refreshing:false,truncated:false,meta:null}; if(Array.isArray(d)) r.columns=d.length?Object.keys(d[0]):[]; return r; }
  var dash={
    colors:['#3b6fd4','#e08a2e','#2e9e7a','#c84f7a','#7b5bd6','#8a6d3b','#2a9fbf','#b8565a'],
    data:function(id){ if(RAW[id]) return ok(RAW[id]); if(CALCS[id]){ if(!(id in cache)){ var c=CALCS[id]; cache[id]=c.fn.apply(null,c.inputs.map(function(i){ return dash.data(i).data; })); } return ok(cache[id]); } return {status:'missing',data:[],message:'missing'}; },
    calc:function(id,o){ CALCS[id]={inputs:o.inputs||[],fn:o.fn}; },
    loader:function(){}, onData:function(fn){ fn(); window.addEventListener('resize',fn); },
    params:function(){ return {}; }, setParams:function(){}, resetParams:function(){}, setLink:function(){}, refresh:function(){},
    draw:function(name,spec){
      if(spec!==undefined){ DRAWS[name]=spec; if(window.__dashReady) render(name); return; }
      render(name);
    }
  };
  function render(name){ var spec=DRAWS[name]; if(!spec) return;
    document.querySelectorAll('[data-draw="'+name+'"]').forEach(function(n){
      try{ if(typeof spec==='function'){ spec(n); } else { var st=STATE.get(n); if(!st){ st=spec.mount?spec.mount(n):{}; STATE.set(n,st); } if(spec.update) spec.update(n,st); } n.classList.remove('dash-skeleton'); }catch(e){ console.error('draw',name,e); }
    }); }
  window.dash=dash;
  window.__dashRenderAll=function(){ window.__dashReady=true; Object.keys(DRAWS).forEach(render); };
  var rt=0, lw=window.innerWidth; window.addEventListener('resize',function(){ if(window.innerWidth===lw) return; lw=window.innerWidth; clearTimeout(rt); rt=setTimeout(function(){ Object.keys(DRAWS).forEach(function(k){ if(typeof DRAWS[k]!=='function') render(k); }); },150); });
})();