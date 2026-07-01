import httpx
import netCDF4
import tempfile
import os

async def test_read_nc():
    url = "https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/xrsf-l2-avg1m_science/2020/01/sci_xrsf-l2-avg1m_g16_d20200101_v2-2-1.nc"
    print("Downloading sample NC from:", url)
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
                    print("Variables:")
                    for var_name in ds.variables:
                        var = ds.variables[var_name]
                        print(f" - {var_name}: shape={var.shape}, dtype={var.dtype}")
                        
                    # Let's inspect some variables
                    time_var = ds.variables["time"]
                    print("time units:", getattr(time_var, "units", "None"))
                    print("time calendar:", getattr(time_var, "calendar", "None"))
                    
                    xrsa_flux = ds.variables["xrsa_flux"]
                    xrsb_flux = ds.variables["xrsb_flux"]
                    print("xrsa_flux first 5 values:", xrsa_flux[:5])
                    print("xrsb_flux first 5 values:", xrsb_flux[:5])
                    
                    # Convert times using num2date
                    import cftime
                    times = netCDF4.num2date(time_var[:], units=time_var.units, calendar=getattr(time_var, "calendar", "standard"))
                    print("Converted times (first 5):", [str(t) for t in times[:5]])
                    ds.close()
                finally:
                    os.unlink(tmp_path)
    except Exception as e:
        print("NC read failed:", e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_read_nc())
