# golan-weather-agent

Daily email with the Golan Heights weather forecast (Katzrin, Mount Hermon,
Majdal Shams) for mohsen.office@gmail.com.

Forecast data comes from [Open-Meteo](https://open-meteo.com/) (no API key).
The email is sent over Gmail SMTP as multipart text + HTML.

## Usage

```bash
# print the report without sending
DRY_RUN=1 python3 weather_email.py

# send it
SMTP_USER=mohsen.office@gmail.com \
MAIL_TO=mohsen.office@gmail.com \
SMTP_PASSWORD="$GMAIL_APP_PASSWORD" \
python3 weather_email.py
```

Requires Python 3.9+ (standard library only).

### Environment variables

| Variable | Default | Notes |
| --- | --- | --- |
| `SMTP_USER` | required | Gmail address used to authenticate and as the From header |
| `SMTP_PASSWORD` | required | Gmail [App Password](https://myaccount.google.com/apppasswords), not the account password |
| `MAIL_TO` | `mohsen.office@gmail.com` | Recipient |
| `SMTP_HOST` | `smtp.gmail.com` | |
| `SMTP_PORT` | `587` | STARTTLS |
| `DRY_RUN` | unset | When set, prints the plain-text report instead of sending |

## Scheduling

The `Daily weather email` GitHub Actions workflow runs this script every day at
04:00 UTC (07:00 Israel time during DST, 06:00 in winter — cron is fixed to
UTC). It reads the app password from the `GMAIL_APP_PASSWORD` repository secret,
and can also be triggered manually from the Actions tab.

## Locations

Edit `LOCATIONS` in `weather_email.py` to change the reported places; each entry
is `(name, latitude, longitude)`.
