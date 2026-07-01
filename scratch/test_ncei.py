import httpx
import re

async def test_ncei():
    url = "https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/xrsf-l2-avg1m_science/2020/01/"
    print("Testing NCEI HTTP connection to:", url)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            print("HTTP status:", resp.status_code)
            if resp.status_code == 200:
                print("HTML content sample (first 500 chars):")
                print(resp.text[:500])
                # Find links
                links = re.findall(r'href="([^"]+\.nc)"', resp.text)
                print("Found netcdf links:", links[:5])
    except Exception as e:
        print("NCEI failed:", e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ncei())
