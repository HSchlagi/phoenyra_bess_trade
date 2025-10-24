import json, hmac, hashlib, base64, asyncio, websockets

SECRET=b"phoenyra_demo_secret"
def verify(meta, data):
    body=(meta['ts'] + '|' + json.dumps(data, separators=(',',':'))).encode()
    calc=base64.b64encode(hmac.new(SECRET, body, hashlib.sha256).digest()).decode()
    assert calc==meta['sig'], "Invalid HMAC"

async def run():
    async with websockets.connect("ws://localhost:9000/ws/orders?api_key=demo") as ws:
        async for raw in ws:
            msg=json.loads(raw)
            verify(msg['meta'], msg['data'])
            print("OK:", msg['data']['type'])

if __name__=="__main__":
    asyncio.run(run())
