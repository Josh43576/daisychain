# Raspberry Pi Power Monitor

This project reads three PZEM power meters, uploads measurements to a Flask dashboard, and lets an authenticated administrator request relay states. **The Pi is the only process that drives relay GPIO.** Sensor faults, invalid settings, API loss, and startup failures leave affected relays OFF.

## Setup

1. Install the packages from `requirements.txt` in the Python environment used by both the Flask app and Pi agent.
2. Copy `.env.example` values into the Flask and Pi service environments. Generate a stable random `FLASK_SECRET_KEY` and a separate random `DEVICE_API_TOKEN`; use the same device token on both services. Set `API_BASE_URL` on the Pi to the Flask host address.
3. Initialize/migrate the database with `flask --app app init-db` from this directory. The Flask SQLite database is stored under Flask's `instance` directory by default.
4. Start Flask with `python app.py` (debug mode is off unless explicitly enabled).
5. On the Pi, confirm relay polarity and wiring with disconnected loads, then run `python main.py`. Set `BASELINE_MODE=1` for telemetry-only operation; this mode holds all relay outputs OFF.
6. Register the first account and verify its email. The first account on a fresh database is the administrator. Existing users are migrated as administrators to preserve access; review accounts after upgrading.

For website testing without an SMTP account, initialize the database and run `flask --app app create-test-admin`. The command prompts for an email and password, then creates or resets a verified administrator account. Use the prompted credentials on `/login`. Browser registration also displays a demo verification code when mail is unconfigured and the request comes directly from loopback (`127.0.0.1` or `::1`). You can enable demo codes explicitly with `ALLOW_DEMO_CODES=1`; set it to `0` in deployment.

For a software-only simulation, set `SIMULATE_HARDWARE=1` **before starting the Python process**. The PZEM reader and relay GPIO use explicit mocks in this mode; simulated telemetry does not validate electrical behavior.

## Environment variables

See `.env.example`. `.env.example` is a template; this project does not automatically load it. Configure variables in the shell, service manager, or deployment environment.

- `FLASK_SECRET_KEY`: stable, randomly generated Flask session signing key.
- `DEVICE_API_TOKEN`: shared bearer token used by the Pi agent and Flask device routes.
- `API_BASE_URL`: base URL for the Flask service, for example `http://192.168.1.20:5000` on a trusted test LAN.
- `DATABASE_URL`: SQLAlchemy URI; defaults to Flask's `instance/users.db` SQLite database.
- `BASELINE_MODE`: `1` holds relays OFF and only reads/uploads telemetry; `0` enables enforcement.
- `SIMULATE_HARDWARE`: `1` enables explicit mock PZEM, RFID, and GPIO behavior; leave `0` on a real device.
- `ALLOW_DEMO_CODES`: `1` shows email verification/reset codes for local development only.
- `SESSION_COOKIE_SECURE`: set to `1` when Flask is served over HTTPS.

The app itself uses Flask's development server. For remote use, place it behind a production WSGI server and HTTPS reverse proxy or a private VPN. The device bearer token travels over HTTP if `API_BASE_URL` uses HTTP, so do not expose that connection to untrusted networks.

## Important operating limits

- Per-appliance limits are instantaneous kW settings. The total system cap is in watts. Either limit can request a cutoff.
- After a cutoff, the server stores the requested state as OFF. An administrator must explicitly request ON again; the Pi still rejects ON while the applicable measurement is invalid or over its limit.
- `manual_interface.py` is a read-only RFID/LCD monitor and does not cut relay power. Do not run it alongside `main.py`; both read the same serial bus.
- `daily_usage_state.json` tracks daily increments from cumulative PZEM energy counters. It resets when the Pi's local date changes. Existing pre-migration daily totals lacked counter baselines and are reset on the first run.
- Relay control assumes HIGH means ON and LOW means OFF, following the existing wiring convention. Confirm that convention with the installed SSR, a disconnected test load, and an appropriate hardware safety review before connecting appliances.
- Sensor logs are retained for 30 days. The device also keeps up to 10,000 local event-history entries.

See [CHANGELOG_IMPLEMENTATION.md](CHANGELOG_IMPLEMENTATION.md) for the implementation changes and upgrade notes.
