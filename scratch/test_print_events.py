import ftplib

def test_list():
    ftp = ftplib.FTP("ftp.swpc.noaa.gov")
    ftp.login()
    ftp.cwd("pub/indices/events")
    files = ftp.nlst()
    # Find any files from 2015
    files_2015 = [f for f in files if "2015" in f]
    print("Files from 2015:", files_2015[:20])
    print("Total 2015 files:", len(files_2015))
    
    # Let's see some other years:
    files_2017 = [f for f in files if "2017" in f]
    print("Total 2017 files:", len(files_2017))
    
    files_2020 = [f for f in files if "2020" in f]
    print("Total 2020 files:", len(files_2020))
    
    print("Sample filenames in directory:", files[:10])
    ftp.quit()

if __name__ == "__main__":
    test_list()
