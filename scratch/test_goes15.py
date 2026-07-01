import httpx
import re

async def test_goes15():
    url = "https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/science/xrs/goes15/xrsf-l2-avg1m_science/2015/01/"
    print("Testing NCEI GOES-15 URL:", url)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            print("HTTP status:", resp.status_code)
            if resp.status_code == 200:
                links = re.findall(r'href="([^"]+\.nc)"', resp.text)
                print("Found netcdf links for GOES-15:", links[:5])
    except Exception as e:
        print("GOES-15 failed:", e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_goes15())
