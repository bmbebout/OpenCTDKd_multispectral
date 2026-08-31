"""Web configuration server for OpenCTDKd.

Starts a WiFi AP (SSID: OpenCTDKd), serves a dashboard on port 80.
Runs until the user clicks 'Start Data Recording', which calls /api/shutdown
and returns False so the caller can transition to data-recording mode.

REST endpoints:
    GET /              -> HTML dashboard (auto-refreshes every 5 s)
    GET /api/status    -> JSON snapshot of all sensor values + RTC time
    GET /api/shutdown  -> stops the server and transitions to data recording
"""

import network
import socket
import time
import json

import lib.rtc          as _rtc
import lib.spectral     as _spectral
import lib.pressure     as _pressure
import lib.temperature  as _temp
import lib.conductivity as _cond
import lib.recording as _recording

_SSID     = "OpenCTDKd"
_PASSWORD = "M$cience"
_PORT     = 80

# ---------------------------------------------------------------------------
# Embedded HTML dashboard — dark-themed, mobile-friendly
# ---------------------------------------------------------------------------
_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpenCTDKd</title>
<style>
body{font-family:sans-serif;background:#0d1117;color:#c9d1d9;padding:1em;max-width:480px;margin:auto}
h1{color:#58a6ff;margin-bottom:.8em;font-size:1.4em}
h2{color:#8b949e;font-size:.75em;text-transform:uppercase;letter-spacing:.08em;margin:1em 0 .4em}
.row{display:flex;justify-content:space-between;align-items:baseline;padding:8px 12px;
     background:#161b22;border:1px solid #30363d;border-radius:4px;margin-bottom:5px}
.lbl{color:#8b949e;font-size:.9em}
.v{font-weight:600;color:#e6edf3}
.u{color:#8b949e;font-size:.8em;margin-left:2px}
.sp{display:flex;flex-wrap:wrap;gap:5px}
.ch{background:#161b22;border:1px solid #30363d;border-radius:4px;padding:6px 8px;
    text-align:center;flex:1 1 80px}
.nm{color:#58a6ff;font-size:.7em;display:block;margin-bottom:2px}
.cnt{font-weight:600;font-size:.95em}
button{background:#238636;color:#fff;border:none;padding:8px 20px;
       border-radius:4px;cursor:pointer;font-size:.9em;margin-top:.9em}
button:active{background:#2ea043}
#ts{color:#8b949e;font-size:.72em;margin-top:.4em}
#err{color:#ff7b72;font-size:.72em;margin-top:.5em;white-space:pre-wrap}
</style>
</head>
<body>
<h1>OpenCTDKd</h1>

<h2>Clock</h2>
<div class="row">
  <span class="lbl">RTC Time</span>
  <span class="v" id="t">&#8212;</span>
</div>
<div class="row">
    <span class="lbl">SQW Clock Sync</span>
    <span class="v" id="sqw">&#8212;</span>
</div>

<h2>Sensors</h2>
<div class="row">
  <span class="lbl">Temperature</span>
  <span><span class="v" id="tc">&#8212;</span><span class="u">&deg;C</span></span>
</div>
<div class="row">
  <span class="lbl">Pressure</span>
  <span><span class="v" id="p">&#8212;</span><span class="u">mbar</span></span>
</div>
<div class="row">
  <span class="lbl">Depth</span>
  <span><span class="v" id="dp">&#8212;</span><span class="u">m</span></span>
</div>
<div class="row">
  <span class="lbl">Conductivity</span>
  <span><span class="v" id="ec">&#8212;</span><span class="u">&micro;S/cm</span></span>
</div>
<div class="row">
  <span class="lbl">Salinity</span>
  <span><span class="v" id="sal">&#8212;</span><span class="u">PSU</span></span>
</div>
<div class="row">
  <span class="lbl">Specific Gravity</span>
  <span class="v" id="sg">&#8212;</span>
</div>

<h2>Spectral</h2>
<div class="sp" id="sp"></div>

<button onclick="poll()">Refresh</button>
<button onclick="startRecording()">Start Data Recording</button>
<button onclick="stopRecording()" style="background:#b91c1c;margin-left:8px">Stop Recording</button>
<h2>SD Card Files</h2>
<div id="files"></div>
<div id="ts">Dashboard loaded; waiting for sensor data...</div>
<div id="err"></div>
<script>document.getElementById('ts').textContent = 'Dashboard script loaded; requesting sensor data...';</script>

<script>
var pollTimer = setInterval(poll, 5000);
function reportError(message){
    document.getElementById('err').textContent = 'Dashboard error: ' + message;
}
window.onerror = function(message, source, line, column){
    reportError(message + ' (line ' + line + ')');
};
window.onunhandledrejection = function(event){
    reportError('Unhandled request error: ' + event.reason);
};
function poll(){
  fetch('/api/status')
        .then(function(r){
            if(!r.ok) throw new Error('status HTTP ' + r.status);
            return r.json();
        })
    .then(function(d){
      document.getElementById('t').textContent   = d.time;
    document.getElementById('sqw').textContent = d.sqw;
            document.getElementById('tc').textContent  = numberText(d.temperature_c, 2);
            document.getElementById('p').textContent   = numberText(d.pressure_mbar, 1);
            document.getElementById('dp').textContent  = numberText(d.depth_m, 3);
            document.getElementById('ec').textContent  = numberText(d.ec_us_cm, 1);
            document.getElementById('sal').textContent = numberText(d.salinity_psu, 3);
            document.getElementById('sg').textContent  = numberText(d.specific_gravity, 4);
      var g = document.getElementById('sp');
      g.innerHTML = '';
            var s = d.spectral || {};
      for(var k in s){
        var el = document.createElement('div');
        el.className = 'ch';
        el.innerHTML = '<span class="nm">'+k.replace('_',' ')+'</span>'
                     + '<span class="cnt">'+s[k]+'</span>';
        g.appendChild(el);
      }
      document.getElementById('ts').textContent = 'Last update: ' + d.time;
    })
    .catch(function(e){
            reportError('status: ' + e.message);
    });
}
function numberText(value, digits){
    var number = Number(value);
    return isFinite(number) ? number.toFixed(digits) : '--';
}
function startRecording(){
    fetch('/api/start').then(function(r){
        if(!r.ok) throw new Error('start HTTP ' + r.status);
        poll(); loadFiles();
    }).catch(function(e){reportError('start: ' + e.message);});
}
function stopRecording(){
    fetch('/api/stop').then(function(r){
        if(!r.ok) throw new Error('stop HTTP ' + r.status);
        poll(); loadFiles();
    }).catch(function(e){reportError('stop: ' + e.message);});
}
function loadFiles(){
    fetch('/api/files').then(function(r){
        if(!r.ok) throw new Error('files HTTP ' + r.status);
        return r.json();
    }).then(function(files){
        var el=document.getElementById('files'); el.innerHTML='';
        files.forEach(function(name){
            var row=document.createElement('div'); row.className='row';
            var link=document.createElement('a');
            link.href='/api/download?name='+encodeURIComponent(name);
            link.textContent=name;
            var button=document.createElement('button');
            button.textContent='Delete';
            button.onclick=function(){deleteFile(name);};
            row.appendChild(link);
            row.appendChild(button);
            el.appendChild(row);
        });
    }).catch(function(e){reportError('files: ' + e.message);});
}
function deleteFile(name){
    if(confirm('Delete '+name+'?')) fetch('/api/delete?name='+encodeURIComponent(name)).then(function(r){
        if(!r.ok) throw new Error('delete HTTP ' + r.status);
        loadFiles();
    }).catch(function(e){reportError('delete: ' + e.message);});
}
poll();
loadFiles();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _start_ap():
    """Activate the WiFi AP and block until it is ready."""
    ap = network.WLAN(network.AP_IF)
    ap.config(ssid=_SSID, password=_PASSWORD)
    ap.active(True)
    while not ap.active():
        time.sleep_ms(100)
    print("AP active - SSID:", _SSID, "IP:", ap.ifconfig()[0])
    return ap


def _get_status(rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev):
    """Read all sensors and return a JSON-serialisable dict.
    Individual sensor failures return 0.0 so the page always renders."""
    data = {}

    try:
        t = _rtc.read_time(rtc_dev)
        data["time"] = "%04d-%02d-%02d %02d:%02d:%02d" % t
    except Exception as e:
        print("webserver: RTC error:", e)
        data["time"] = "unavailable"

    temp_c = 0.0
    try:
        temp_c = _temp.read(temp_dev)
        data["temperature_c"] = temp_c
    except Exception as e:
        print("webserver: temp error:", e)
        data["temperature_c"] = 0.0

    try:
        p, _, depth = _pressure.read(pressure_dev)
        data["pressure_mbar"] = p
        data["depth_m"]       = depth
    except Exception as e:
        print("webserver: pressure error:", e)
        data["pressure_mbar"] = 0.0
        data["depth_m"]       = 0.0

    try:
        ec, tds, sal, sg = _cond.read(cond_dev, temp_c)
        data["ec_us_cm"]        = ec
        data["tds_ppm"]         = tds
        data["salinity_psu"]    = sal
        data["specific_gravity"] = sg
    except Exception as e:
        print("webserver: conductivity error:", e)
        data["ec_us_cm"]        = 0.0
        data["tds_ppm"]         = 0.0
        data["salinity_psu"]    = 0.0
        data["specific_gravity"] = 0.0

    try:
        data["spectral"] = _spectral.read_channels(spectral_dev)
    except Exception as e:
        print("webserver: spectral error:", e)
        data["spectral"] = {}

    data["sqw"] = _recording.clock_status()
    data["recording"] = _recording.active()
    data["recording_file"] = _recording.path() or ""

    return data


def _send(conn, status, content_type, body, download_name=None):
    """Send a minimal HTTP response. body may be str or bytes."""
    if isinstance(body, str):
        body = body.encode("utf-8")
    header = "HTTP/1.1 %s\r\n" % status
    header += "Content-Type: %s\r\n" % content_type
    header += "Cache-Control: no-store\r\n"
    if download_name:
        header += "Content-Disposition: attachment; filename=\"%s\"\r\n" % download_name
    header += "Content-Length: %d\r\n" % len(body)
    header += "Connection: close\r\n\r\n"
    conn.sendall(header.encode("utf-8") + body)


def _handle(conn, path, rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev):
    """Dispatch one HTTP request. Returns True if the server should stop."""
    if path.startswith("/api/start"):
        _recording.start(rtc_dev)
        _send(conn, "200 OK", "application/json", '{"status":"recording"}')
    elif path.startswith("/api/stop"):
        _recording.stop()
        _send(conn, "200 OK", "application/json", '{"status":"stopped"}')
    elif path.startswith("/api/files"):
        _send(conn, "200 OK", "application/json", json.dumps(_recording.files()))
    elif path.startswith("/api/download"):
        name = _query(path, "name")
        _send(conn, "200 OK", "text/csv", _recording.read_file(name), name)
    elif path.startswith("/api/delete"):
        name = _query(path, "name")
        _recording.delete_file(name)
        _send(conn, "200 OK", "application/json", '{"status":"deleted"}')
    elif path.startswith("/api/status"):
        data = _get_status(rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev)
        _send(conn, "200 OK", "application/json", json.dumps(data))
    else:
        _send(conn, "200 OK", "text/html; charset=utf-8", _HTML)
    return False


def _query(path, key):
    """Extract a simple URL-decoded query value without external modules."""
    query = path.split("?", 1)[1] if "?" in path else ""
    for item in query.split("&"):
        parts = item.split("=", 1)
        if len(parts) == 2 and parts[0] == key:
            return parts[1].replace("%20", " ").replace("%2F", "/")
    raise ValueError("missing query parameter")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev):
    """Start AP and serve until the user requests /api/shutdown.

    Returns False so the caller can transition to data-recording mode.
    """
    ap = _start_ap()

    srv = socket.socket()
    try:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except AttributeError:
        pass
    srv.bind(("", _PORT))
    srv.listen(2)
    srv.settimeout(1.0)  # non-blocking so the loop stays responsive

    print("Web server listening - http://192.168.4.1")

    try:
        while True:
            try:
                conn, addr = srv.accept()
            except OSError:
                _recording.sample_if_due(rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev,
                                         time.ticks_ms())
                continue

            stop = False
            try:
                raw = conn.recv(2048)
                req = raw.decode("utf-8")
                parts = req.split(" ")
                path = parts[1] if len(parts) >= 2 else "/"
                stop = _handle(conn, path, rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev)
            except Exception as e:
                print("webserver: request error:", e)
            finally:
                conn.close()

            if stop:
                break

            _recording.sample_if_due(rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev,
                                     time.ticks_ms())

    finally:
        srv.close()
        ap.active(False)
        print("Web server stopped - entering data-recording mode")

    return False
