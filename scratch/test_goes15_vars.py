import httpx
import netCDF4
import tempfile
import os

async def test_goes15_vars():
    # URL for GOES-15 L2 data for 2015-01-01
    url = "https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/science/xrs/goes15/xrsf-l2-avg1m_science/2015/01/sci_xrsf-l2-avg1m_g15_d20150101_v2-2-1.nc"
    print("Downloading GOES-15 NC from:", url)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            print("Download status:", resp.status_code)
            if resp.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".nc") as tmp:
                    tmp.write(resp.content)
                    tmp_path = tmp.name
                
                print("Opening NC file:", tmp_path)
                try:
                    ds = netCDF4.Dataset(tmp_path)
                    print("Variables in GOES-15 file:")
                    for var_name in ds.variables:
                        var = ds.variables[var_name]
                        print(f" - {var_name}: shape={var.shape}, dtype={var.dtype}")
                        
                    # Let's inspect some variables
                    time_var = ds.variables["time"]
                    print("time units:", getattr(time_var, "units", "None"))
                    
                    xrsa_flux = ds.variables["xrsa_flux"]
                    xrsb_flux = ds.variables["xrsb_flux"]
                    print("xrsa_flux first 5 values:", xrsa_flux[:5])
                    print("xrsb_flux first 5 values:", xrsb_flux[:5])
                    ds.close()
                finally:
                    os.unlink(tmp_path)
    except Exception as e:
        print("GOES-15 read failed:", e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_goes15_vars())
