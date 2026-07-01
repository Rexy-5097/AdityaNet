import ftplib

def test_ftp_search():
    try:
        ftp = ftplib.FTP("ftp.swpc.noaa.gov")
        ftp.login()
        print("FTP login successful!")
        
        # Let's list directories under pub/warehouse
        ftp.cwd("pub/warehouse")
        print("Contents of pub/warehouse:")
        dirs = []
        ftp.retrlines("LIST", lambda line: dirs.append(line))
        for d in dirs[:20]:
            print(d)
            
        ftp.quit()
    except Exception as e:
        print("FTP failed:", e)

if __name__ == "__main__":
    test_ftp_search()
