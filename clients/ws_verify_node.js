// npm i ws
import WebSocket from 'ws';
import crypto from 'crypto';

const SECRET = Buffer.from('phoenyra_demo_secret', 'utf8');
function verify(meta, data){
  const body = Buffer.from(meta.ts + '|' + JSON.stringify(data));
  const calc = crypto.createHmac('sha256', SECRET).update(body).digest('base64');
  if(calc !== meta.sig) throw new Error('Invalid HMAC');
}

const ws = new WebSocket('ws://localhost:9000/ws/orders?api_key=demo');
ws.on('message', buf => {
  const msg = JSON.parse(buf.toString());
  verify(msg.meta, msg.data);
  console.log('OK:', msg.data.type);
});
