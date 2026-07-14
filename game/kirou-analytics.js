/* KirOu analytics — tiny Aptabase client (no bundler needed).
   Posts events to Aptabase's ingest API. Region + host derived from the App Key.
   Fire-and-forget: never blocks the UI, swallows all errors. */
(function(){
  var KEY='A-EU-7532873436';
  var HOSTS={US:'https://us.aptabase.com',EU:'https://eu.aptabase.com',DEV:'https://localhost:3000'};
  var region=(KEY.split('-')[1]||'EU').toUpperCase();
  var API=(HOSTS[region]||HOSTS.EU)+'/api/v0/event';
  var APPVER='1.0';
  function sessionId(){
    var now=Date.now(),o={};
    try{o=JSON.parse(localStorage.getItem('kirou_ab_session')||'{}');}catch(e){}
    if(!o.id||!o.last||(now-o.last)>3600000){o.id=(''+now)+'-'+Math.random().toString(36).slice(2,10);}
    o.last=now;
    try{localStorage.setItem('kirou_ab_session',JSON.stringify(o));}catch(e){}
    return o.id;
  }
  window.kirouTrack=function(name,props){
    try{
      fetch(API,{method:'POST',credentials:'omit',keepalive:true,
        headers:{'Content-Type':'application/json','App-Key':KEY},
        body:JSON.stringify({
          timestamp:new Date().toISOString(),
          sessionId:sessionId(),
          eventName:name,
          systemProps:{locale:(navigator.language||'en'),isDebug:false,appVersion:APPVER,sdkVersion:'kirou-web@1'},
          props:props||{}
        })
      }).catch(function(){});
    }catch(e){}
  };
})();
