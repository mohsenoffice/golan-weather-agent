"""Fetch the daily Golan Heights forecast and email it.

Requires env vars:
  SMTP_HOST (default smtp.gmail.com), SMTP_PORT (default 587)
  SMTP_USER, SMTP_PASSWORD, MAIL_TO (default mohsen.office@gmail.com)
"""

import os
import smtplib
import urllib.parse
import urllib.request
import json
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

LOCATIONS = [
    ("Katzrin", 32.99, 35.69),
    ("Mount Hermon", 33.30, 35.79),
    ("Majdal Shams", 33.27, 35.77),
]
TIMEZONE = "Asia/Jerusalem"

WMO = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle",
    53: "Moderate drizzle", 55: "Dense drizzle", 56: "Light freezing drizzle",
    57: "Dense freezing drizzle", 61: "Slight rain", 63: "Moderate rain",
    65: "Heavy rain", 66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
    77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
    82: "Violent rain showers", 85: "Slight snow showers",
    86: "Heavy snow showers", 95: "Thunderstorm",
    96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def fetch_forecast(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "sunrise",
            "sunset",
        ]),
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "timezone": TIMEZONE,
        "forecast_days": 3,
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def describe(code: int) -> str:
    return WMO.get(code, f"Code {code}")


def render(reports: list[tuple[str, dict]]) -> tuple[str, str]:
    today = datetime.now(ZoneInfo(TIMEZONE)).strftime("%A, %d %B %Y")
    lines = [f"Golan Heights weather - {today}", ""]
    html = [
        "<html><body style=\"font-family:Arial,Helvetica,sans-serif;color:#222\">",
        f"<h2>Golan Heights weather &mdash; {today}</h2>",
    ]

    for name, data in reports:
        cur = data["current"]
        d = data["daily"]
        lines += [
            f"{name}",
            f"  Now: {cur['temperature_2m']}degC, {describe(cur['weather_code'])}, "
            f"humidity {cur['relative_humidity_2m']}%, wind {cur['wind_speed_10m']} km/h",
        ]
        html.append(f"<h3>{name}</h3>")
        html.append(
            f"<p><b>Now:</b> {cur['temperature_2m']}&deg;C, {describe(cur['weather_code'])}, "
            f"humidity {cur['relative_humidity_2m']}%, wind {cur['wind_speed_10m']} km/h</p>"
        )
        html.append(
            "<table cellpadding=\"6\" cellspacing=\"0\" border=\"1\" "
            "style=\"border-collapse:collapse;font-size:14px\">"
            "<tr style=\"background:#f0f0f0\"><th>Date</th><th>Conditions</th>"
            "<th>Min/Max</th><th>Rain</th><th>Wind max</th></tr>"
        )
        for i, date in enumerate(d["time"]):
            row = (
                date,
                describe(d["weather_code"][i]),
                f"{d['temperature_2m_min'][i]}/{d['temperature_2m_max'][i]}degC",
                f"{d['precipitation_sum'][i]} mm ({d['precipitation_probability_max'][i]}%)",
                f"{d['wind_speed_10m_max'][i]} km/h",
            )
            lines.append(f"  {row[0]}: {row[1]}, {row[2]}, rain {row[3]}, wind {row[4]}")
            html.append(
                "<tr>" + "".join(f"<td>{c.replace('degC', '&deg;C')}</td>" for c in row) + "</tr>"
            )
        html.append("</table>")
        sunrise = d["sunrise"][0].split("T")[1]
        sunset = d["sunset"][0].split("T")[1]
        lines += [f"  Sunrise {sunrise}, sunset {sunset}", ""]
        html.append(f"<p>Sunrise {sunrise} &middot; Sunset {sunset}</p>")

    lines.append("Source: Open-Meteo")
    html.append("<p style=\"color:#888;font-size:12px\">Source: Open-Meteo</p></body></html>")
    return "\n".join(lines), "".join(html)


def send(subject: str, text: str, html: str) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    to_addr = os.environ.get("MAIL_TO", "mohsen.office@gmail.com")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(host, port, timeout=60) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)


def main() -> None:
    reports = [(name, fetch_forecast(lat, lon)) for name, lat, lon in LOCATIONS]
    text, html = render(reports)
    today = datetime.now(ZoneInfo(TIMEZONE)).strftime("%d %b %Y")
    if os.environ.get("DRY_RUN"):
        print(text)
        return
    send(f"Golan Heights weather - {today}", text, html)
    print("sent")


if __name__ == "__main__":
    main()
