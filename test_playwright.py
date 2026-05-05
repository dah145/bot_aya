import requests

def test_aya():
    print("Testing requests with x-gw-token and Session")
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.aya.go.cr/",
        "Accept": "application/json, text/plain, */*"
    }
    session.headers.update(headers)
    
    print("Loading main page to get cookies...")
    session.get("https://www.aya.go.cr/inicio/gestiones_interes/is/interrupciones_servicio")
    
    r = session.get("https://apigat.aya.go.cr/sitio/gw/init")
    print("Init Status:", r.status_code)
    try:
        token = r.json().get("gwToken")
        print("Token:", token[:10])
        
        session.headers.update({
            "x-gw-token": token,
            "componente": "SITIO WEB",
            "x-page-url": "inicio/gestiones_interes/is/interrupciones_servicio"
        })
        
        r2 = session.get("https://apigat.aya.go.cr/sitio/api/SitioWeb/Interrupciones?FkProvincia=1&FkCanton=8&FkDistrito=102")
        print("API Status:", r2.status_code)
        print("API Data:", str(r2.text)[:200])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_aya()
