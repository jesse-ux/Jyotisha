#!/usr/bin/env python3
"""生成标准验证星盘数据集 - 60张名人星盘 + PyJhora D1/Rasi Yoga验证结果"""
import json, os, subprocess, sys

PYJHORA = "/Users/wuyongnaren/.workbuddy/binaries/python/envs/pyjhora-benchmark/bin/python"
HELPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_compute_one_chart.py")

CELEBRITY_CHARTS = [
    # 科学 (10)
    {"name": "Albert Einstein", "date": "1879-03-14", "time": "11:30", "tz": "+01:00", "lat": 48.4011, "lon": 9.9876, "city": "Ulm, Germany"},
    {"name": "Marie Curie", "date": "1867-11-07", "time": "12:00", "tz": "+01:00", "lat": 52.2297, "lon": 21.0122, "city": "Warsaw, Poland"},
    {"name": "Nikola Tesla", "date": "1856-07-10", "time": "00:00", "tz": "+01:00", "lat": 44.5686, "lon": 15.3790, "city": "Smiljan, Croatia"},
    {"name": "Stephen Hawking", "date": "1942-01-08", "time": "00:00", "tz": "+00:00", "lat": 51.7520, "lon": -1.2577, "city": "Oxford, UK"},
    {"name": "Charles Darwin", "date": "1809-02-12", "time": "03:00", "tz": "+00:00", "lat": 52.7073, "lon": -2.7553, "city": "Shrewsbury, UK"},
    {"name": "Thomas Edison", "date": "1847-02-11", "time": "23:59", "tz": "-05:00", "lat": 41.2995, "lon": -82.6052, "city": "Milan, USA"},
    {"name": "Alexander Fleming", "date": "1881-08-06", "time": "03:00", "tz": "+00:00", "lat": 55.6100, "lon": -4.2886, "city": "Darvel, UK"},
    {"name": "Max Planck", "date": "1858-04-23", "time": "10:00", "tz": "+01:00", "lat": 54.3233, "lon": 10.1228, "city": "Kiel, Germany"},
    {"name": "Niels Bohr", "date": "1885-10-07", "time": "11:30", "tz": "+01:00", "lat": 55.6761, "lon": 12.5683, "city": "Copenhagen, Denmark"},
    {"name": "Richard Feynman", "date": "1918-05-11", "time": "13:47", "tz": "-05:00", "lat": 40.7282, "lon": -73.7949, "city": "Queens, USA"},
    # 政治 (10)
    {"name": "Mahatma Gandhi", "date": "1869-10-02", "time": "07:12", "tz": "+05:30", "lat": 21.6270, "lon": 72.9480, "city": "Porbandar, India"},
    {"name": "Jawaharlal Nehru", "date": "1889-11-14", "time": "23:30", "tz": "+05:30", "lat": 25.5941, "lon": 77.6232, "city": "Allahabad, India"},
    {"name": "Narendra Modi", "date": "1950-09-17", "time": "11:00", "tz": "+05:30", "lat": 23.1702, "lon": 72.8311, "city": "Vadnagar, India"},
    {"name": "Indira Gandhi", "date": "1917-11-19", "time": "23:15", "tz": "+05:30", "lat": 25.5941, "lon": 77.6232, "city": "Allahabad, India"},
    {"name": "Winston Churchill", "date": "1874-11-30", "time": "01:30", "tz": "+00:00", "lat": 51.8415, "lon": -1.3610, "city": "Blenheim Palace, UK"},
    {"name": "John F. Kennedy", "date": "1917-05-29", "time": "15:00", "tz": "-05:00", "lat": 42.3318, "lon": -71.1212, "city": "Brookline, USA"},
    {"name": "Nelson Mandela", "date": "1918-07-18", "time": "14:45", "tz": "+02:00", "lat": -31.9304, "lon": 28.9487, "city": "Mvezo, South Africa"},
    {"name": "Abraham Lincoln", "date": "1809-02-12", "time": "06:54", "tz": "-05:00", "lat": 38.0293, "lon": -78.4767, "city": "Hodgenville, USA"},
    {"name": "Margaret Thatcher", "date": "1925-10-13", "time": "09:00", "tz": "+00:00", "lat": 52.9548, "lon": -1.1581, "city": "Grantham, UK"},
    {"name": "Barack Obama", "date": "1961-08-04", "time": "19:24", "tz": "-10:00", "lat": 21.3099, "lon": -157.8581, "city": "Honolulu, USA"},
    # 艺术 (10)
    {"name": "Rabindranath Tagore", "date": "1861-05-07", "time": "02:30", "tz": "+05:30", "lat": 22.5726, "lon": 88.3639, "city": "Kolkata, India"},
    {"name": "Ludwig van Beethoven", "date": "1770-12-17", "time": "15:40", "tz": "+01:00", "lat": 50.7374, "lon": 7.0982, "city": "Bonn, Germany"},
    {"name": "Wolfgang Mozart", "date": "1756-01-27", "time": "20:55", "tz": "+01:00", "lat": 47.8095, "lon": 13.0550, "city": "Salzburg, Austria"},
    {"name": "Pablo Picasso", "date": "1881-10-25", "time": "23:15", "tz": "+00:00", "lat": 36.7213, "lon": -4.4214, "city": "Malaga, Spain"},
    {"name": "Vincent van Gogh", "date": "1853-03-30", "time": "11:00", "tz": "+00:20", "lat": 51.4865, "lon": 3.5515, "city": "Zundert, Netherlands"},
    {"name": "Charlie Chaplin", "date": "1889-04-16", "time": "20:00", "tz": "+00:00", "lat": 51.5074, "lon": -0.1278, "city": "London, UK"},
    {"name": "Elvis Presley", "date": "1935-01-08", "time": "04:35", "tz": "-06:00", "lat": 34.2576, "lon": -88.7034, "city": "Tupelo, USA"},
    {"name": "Michael Jackson", "date": "1958-08-29", "time": "19:33", "tz": "-05:00", "lat": 41.5934, "lon": -87.3369, "city": "Gary, USA"},
    {"name": "A.R. Rahman", "date": "1967-01-06", "time": "03:45", "tz": "+05:30", "lat": 13.0827, "lon": 80.2707, "city": "Chennai, India"},
    {"name": "Lata Mangeshkar", "date": "1929-09-28", "time": "22:30", "tz": "+05:30", "lat": 18.5204, "lon": 73.8567, "city": "Indore, India"},
    # 商业 (10)
    {"name": "Steve Jobs", "date": "1955-02-24", "time": "19:00", "tz": "-08:00", "lat": 37.7749, "lon": -122.4194, "city": "San Francisco, USA"},
    {"name": "Bill Gates", "date": "1955-10-28", "time": "22:00", "tz": "-08:00", "lat": 47.6062, "lon": -122.3321, "city": "Seattle, USA"},
    {"name": "Elon Musk", "date": "1971-06-28", "time": "07:30", "tz": "+02:00", "lat": -25.7479, "lon": 28.2293, "city": "Pretoria, South Africa"},
    {"name": "Jeff Bezos", "date": "1964-01-12", "time": "17:44", "tz": "-07:00", "lat": 35.0844, "lon": -106.6504, "city": "Albuquerque, USA"},
    {"name": "Warren Buffett", "date": "1930-08-30", "time": "15:00", "tz": "-06:00", "lat": 41.2565, "lon": -95.9345, "city": "Omaha, USA"},
    {"name": "Mukesh Ambani", "date": "1957-04-19", "time": "19:45", "tz": "+03:00", "lat": 12.7790, "lon": 45.0090, "city": "Aden, Yemen"},
    {"name": "Ratan Tata", "date": "1937-12-28", "time": "00:30", "tz": "+05:30", "lat": 18.9219, "lon": 72.8346, "city": "Mumbai, India"},
    {"name": "Narayana Murthy", "date": "1946-08-20", "time": "01:15", "tz": "+05:30", "lat": 13.1730, "lon": 77.7990, "city": "Shidlaghatta, India"},
    {"name": "Azim Premji", "date": "1945-07-24", "time": "07:30", "tz": "+05:30", "lat": 18.5204, "lon": 73.8567, "city": "Mumbai, India"},
    {"name": "Dhirubhai Ambani", "date": "1932-12-28", "time": "06:55", "tz": "+05:30", "lat": 20.8520, "lon": 70.4836, "city": "Chorwad, India"},
    # 体育 (10)
    {"name": "Sachin Tendulkar", "date": "1973-04-24", "time": "14:00", "tz": "+05:30", "lat": 19.0760, "lon": 72.8777, "city": "Mumbai, India"},
    {"name": "Virat Kohli", "date": "1988-11-05", "time": "10:28", "tz": "+05:30", "lat": 28.6139, "lon": 77.2090, "city": "Delhi, India"},
    {"name": "MS Dhoni", "date": "1981-07-07", "time": "17:35", "tz": "+05:30", "lat": 23.3441, "lon": 85.3096, "city": "Ranchi, India"},
    {"name": "Muhammad Ali", "date": "1942-01-17", "time": "18:35", "tz": "-06:00", "lat": 38.2527, "lon": -85.7585, "city": "Louisville, USA"},
    {"name": "Michael Jordan", "date": "1963-02-17", "time": "10:20", "tz": "-05:00", "lat": 40.6782, "lon": -73.9442, "city": "Brooklyn, USA"},
    {"name": "Lionel Messi", "date": "1987-06-24", "time": "20:30", "tz": "-03:00", "lat": -32.9442, "lon": -60.6505, "city": "Rosario, Argentina"},
    {"name": "Cristiano Ronaldo", "date": "1985-02-05", "time": "10:20", "tz": "+00:00", "lat": 32.6669, "lon": -16.9241, "city": "Funchal, Portugal"},
    {"name": "Serena Williams", "date": "1981-09-26", "time": "20:28", "tz": "-04:00", "lat": 43.4195, "lon": -83.9508, "city": "Saginaw, USA"},
    {"name": "Pele", "date": "1940-10-23", "time": "03:00", "tz": "-03:00", "lat": -21.6929, "lon": -45.2580, "city": "Tres Coracoes, Brazil"},
    {"name": "Roger Federer", "date": "1981-08-08", "time": "08:40", "tz": "+01:00", "lat": 47.3769, "lon": 8.5417, "city": "Basel, Switzerland"},
    # 其他重要人物 (10)
    {"name": "Swami Vivekananda", "date": "1863-01-12", "time": "06:33", "tz": "+05:30", "lat": 22.5726, "lon": 88.3639, "city": "Kolkata, India"},
    {"name": "Amitabh Bachchan", "date": "1942-10-11", "time": "16:00", "tz": "+05:30", "lat": 25.4484, "lon": 81.7313, "city": "Prayagraj, India"},
    {"name": "Queen Elizabeth II", "date": "1926-04-21", "time": "02:40", "tz": "+00:00", "lat": 51.5074, "lon": -0.1278, "city": "London, UK"},
    {"name": "Princess Diana", "date": "1961-07-01", "time": "19:45", "tz": "+01:00", "lat": 52.9548, "lon": -1.1581, "city": "Sandringham, UK"},
    {"name": "Dalai Lama", "date": "1935-07-06", "time": "04:38", "tz": "+05:30", "lat": 26.8500, "lon": 89.4000, "city": "Taktser, Tibet"},
    {"name": "Pope Francis", "date": "1936-12-17", "time": "21:00", "tz": "-03:00", "lat": -34.6037, "lon": -58.3816, "city": "Buenos Aires, Argentina"},
    {"name": "Osho", "date": "1931-12-11", "time": "13:15", "tz": "+05:30", "lat": 23.2500, "lon": 77.4167, "city": "Kuchwada, India"},
    {"name": "J. Krishnamurti", "date": "1895-05-12", "time": "00:30", "tz": "+05:30", "lat": 13.0827, "lon": 80.2707, "city": "Madanapalle, India"},
    {"name": "Ramana Maharshi", "date": "1879-12-30", "time": "01:00", "tz": "+05:30", "lat": 9.9252, "lon": 78.1198, "city": "Tiruchuli, India"},
    {"name": "Paramahansa Yogananda", "date": "1893-01-05", "time": "20:38", "tz": "+05:30", "lat": 27.0360, "lon": 88.2627, "city": "Gorakhpur, India"},
]

def compute_external_benchmark_yogas(chart):
    try:
        result = subprocess.run(
            [PYJHORA, HELPER],
            input=json.dumps(chart),
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": result.stderr[:300]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print(f"Standard Test Charts Builder - {len(CELEBRITY_CHARTS)} charts")
    outpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "standard_test_charts.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    output = {
        "schema_version": "2.0",
        "description": "Standard test charts for yoga validation with D1/D9/Panchanga/Upagraha context",
        "charts": [],
    }
    for chart in CELEBRITY_CHARTS:
        print(f"  Computing {chart['name']}...", flush=True)
        yogas = compute_external_benchmark_yogas(chart)
        entry = dict(chart)
        entry["expected_yogas"] = yogas.get("yogas", [])
        if "context" in yogas:
            entry["context"] = yogas["context"]
        entry["external_benchmark_raw"] = yogas
        output["charts"].append(entry)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved to {outpath}")
