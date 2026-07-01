import httpx

async def test_edited_events():
    url = "https://services.swpc.noaa.gov/json/edited_events.json"
    print("Testing edited events JSON from:", url)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            print("HTTP status:", resp.status_code)
            if resp.status_code == 200:
                data = resp.json()
                print("Total events:", len(data))
                xra_events = [e for e in data if e.get("type") == "XRA"]
                print("Total XRA events:", len(xra_events))
                if xra_events:
                    print("Sample XRA event:")
                    import pprint
                    pprint.pprint(xra_events[0])
                    # Print other unique keys in all events
                    keys = set()
                    for e in data:
                        keys.update(e.keys())
                    print("All keys in edited_events.json:", keys)
    except Exception as e:
        print("Edited events failed:", e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_edited_events())
