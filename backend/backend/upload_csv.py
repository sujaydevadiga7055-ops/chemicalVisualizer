import requests

API_URL = "http://127.0.0.1:8000/api/upload/"
TOKEN = "dc7115f7e1ded18dbebf810fb9788043f38a39b5"

FILE_PATH = r"C:\Users\vignesh\Downloads\Telegram Desktop\sample_equipment_data.csv"

def main():
    headers = {
        "Authorization": f"Token {TOKEN}"
    }

    with open(FILE_PATH, "rb") as f:
        files = {"file": (FILE_PATH, f, "text/csv")}

        try:
            resp = requests.post(API_URL, headers=headers, files=files)
        except Exception as e:
            print("Request failed:", e)
            return

    print("STATUS:", resp.status_code)

    try:
        print("RESPONSE JSON:")
        print(resp.json())
    except:
        print("RESPONSE TEXT:")
        print(resp.text)

if __name__ == "__main__":
    main()

