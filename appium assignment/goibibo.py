import datetime
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET


ADB_PATH = r"C:\Users\mohds\AppData\Local\Android\Sdk\platform-tools\adb.exe"
GOIBIBO_PACKAGE = "com.goibibo"
GOIBIBO_ACTIVITY = "com.goibibo.common.HomeActivity"
BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


# -------- ADB Core --------
def ensure_adb_path():
    if os.path.isfile(ADB_PATH):
        return True
    print(f"[ERROR] adb.exe not found at: {ADB_PATH}")
    return False


def adb_call(args, timeout=30):
    cmd = [ADB_PATH] + args
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", f"Timeout running: {' '.join(cmd)}", 1


def adb_tap(x, y, label="", wait=1.8):
    print(f"[TAP] {label} at ({x}, {y})")
    adb_call(["shell", "input", "tap", str(x), str(y)])
    time.sleep(wait)


def adb_keyevent(code, wait=0.25):
    adb_call(["shell", "input", "keyevent", str(code)])
    time.sleep(wait)


def adb_type(text, label=""):
    print(f"[TYPE] {label}: {text}")
    safe_text = text.replace(" ", "%s")
    adb_call(["shell", "input", "text", safe_text])
    time.sleep(2.0)


# -------- UI Dump Parsing --------
def parse_bounds(bounds):
    m = BOUNDS_RE.match(bounds or "")
    if not m:
        return None
    return tuple(int(v) for v in m.groups())


def dump_ui_nodes():
    adb_call(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], timeout=20)
    stdout, _stderr, _code = adb_call(["shell", "cat", "/sdcard/window_dump.xml"], timeout=30)
    start = stdout.find("<?xml")
    if start < 0:
        return []
    xml_text = stdout[start:]

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    nodes = []
    for node in root.iter("node"):
        parsed = parse_bounds(node.attrib.get("bounds", ""))
        if not parsed:
            continue
        x1, y1, x2, y2 = parsed
        nodes.append(
            {
                "text": (node.attrib.get("text") or "").strip(),
                "resource_id": (node.attrib.get("resource-id") or "").strip(),
                "content_desc": (node.attrib.get("content-desc") or "").strip(),
                "class": (node.attrib.get("class") or "").strip(),
                "package": (node.attrib.get("package") or "").strip(),
                "clickable": node.attrib.get("clickable") == "true",
                "enabled": node.attrib.get("enabled") == "true",
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "cx": (x1 + x2) // 2,
                "cy": (y1 + y2) // 2,
            }
        )
    return nodes


def tap_node(node, label, wait=1.8):
    adb_tap(node["cx"], node["cy"], label, wait=wait)


# -------- Screen Detection --------
def contains_text(nodes, snippet):
    key = snippet.lower()
    return any(key in n["text"].lower() for n in nodes)


def is_login_wall(nodes):
    if any(n["resource_id"].endswith("onboarding_enter_mob_no_edtTxt") for n in nodes):
        return True
    markers = ["enter your number", "mobile no.", "continue"]
    return sum(1 for m in markers if contains_text(nodes, m)) >= 2


def is_home_screen(nodes):
    return any(
        n["resource_id"] == "com.goibibo:id/itemContainer"
        and n["content_desc"].lower() == "flights"
        and 600 < n["cy"] < 1200
        for n in nodes
    )


def is_flight_search_screen(nodes):
    has_tabs = contains_text(nodes, "one way") and contains_text(nodes, "roundtrip")
    has_search_btn = any(n["resource_id"] == "com.goibibo:id/search_button_flat" for n in nodes)
    has_city_layouts = any(n["resource_id"] == "com.goibibo:id/from_selection_layout" for n in nodes)
    return has_tabs and has_search_btn and has_city_layouts


def is_city_picker_screen(nodes):
    return any(n["resource_id"] == "com.goibibo:id/departure_city_input" for n in nodes)


def is_calendar_screen(nodes):
    return any(n["resource_id"] == "com.goibibo:id/btnDone" for n in nodes)


def is_city_error_overlay(nodes):
    return contains_text(nodes, "something went wrong") and (
        contains_text(nodes, "refresh page") or contains_text(nodes, "back")
    )


def is_goibibo_foreground(nodes):
    return any(n["package"] == GOIBIBO_PACKAGE for n in nodes)


# -------- Navigation --------
def launch_goibibo():
    print("[ACTION] Launching Goibibo...")
    adb_call(["shell", "am", "force-stop", GOIBIBO_PACKAGE])
    time.sleep(1.5)
    adb_call(["shell", "am", "start", "-n", f"{GOIBIBO_PACKAGE}/{GOIBIBO_ACTIVITY}"])
    time.sleep(12)


def dismiss_login_wall_once(nodes):
    close_words = ["skip", "later", "not now", "no thanks", "close", "dismiss", "continue without"]
    candidates = [
        n
        for n in nodes
        if n["clickable"]
        and n["enabled"]
        and (
            any(w in n["text"].lower() for w in close_words)
            or any(w in n["content_desc"].lower() for w in close_words)
            or "skip" in n["resource_id"].lower()
            or "close" in n["resource_id"].lower()
        )
    ]
    if candidates:
        candidates.sort(key=lambda n: (n["y1"], n["x1"]))
        tap_node(candidates[0], "Dismiss login wall")
        return True

    # Common hidden close area fallback
    adb_tap(1000, 170, "Login close fallback", wait=0.8)
    adb_keyevent(4, wait=1.2)
    return True


def bypass_login_and_reach_home(max_attempts=6):
    for _ in range(max_attempts):
        nodes = dump_ui_nodes()

        if not is_goibibo_foreground(nodes):
            print("[INFO] Goibibo not in foreground, relaunching")
            launch_goibibo()
            continue

        if is_home_screen(nodes):
            print("[OK] Home screen is active")
            return True

        if is_login_wall(nodes):
            print("[ACTION] Login wall detected, attempting dismiss")
            dismiss_login_wall_once(nodes)
            time.sleep(1.2)
            continue

        # Generic escape for overlays
        adb_tap(540, 1900, "Overlay fallback tap", wait=0.8)
        adb_keyevent(4, wait=0.8)
        time.sleep(0.8)

    nodes = dump_ui_nodes()
    return is_home_screen(nodes)


def open_flights(max_attempts=5):
    for attempt in range(1, max_attempts + 1):
        nodes = dump_ui_nodes()
        if is_flight_search_screen(nodes):
            print("[OK] Flight search screen is active")
            return True

        flights_tiles = [
            n
            for n in nodes
            if n["resource_id"] == "com.goibibo:id/itemContainer"
            and n["content_desc"].lower() == "flights"
            and n["clickable"]
            and 600 < n["cy"] < 1200
        ]
        if flights_tiles:
            flights_tiles.sort(key=lambda n: (n["y1"], n["x1"]))
            tap_node(flights_tiles[0], f"Flights tile (attempt {attempt})", wait=3.0)
        else:
            adb_tap(414, 857, f"Flights fallback tap (attempt {attempt})", wait=3.0)

        nodes = dump_ui_nodes()
        if is_flight_search_screen(nodes):
            print("[OK] Flight search screen is active")
            return True

    return False


# -------- Flight Form Helpers --------
def tap_from_or_to(which):
    nodes = dump_ui_nodes()
    rid = "com.goibibo:id/from_selection_layout" if which == "FROM" else "com.goibibo:id/to_city_layout"
    candidates = [n for n in nodes if n["resource_id"] == rid and n["clickable"]]
    if candidates:
        tap_node(candidates[0], f"Open {which} city", wait=2.0)
        return True

    # Fallback coordinates from captured dump
    if which == "FROM":
        adb_tap(289, 546, "Fallback FROM city", wait=2.0)
    else:
        adb_tap(794, 546, "Fallback TO city", wait=2.0)
    return False


def clear_city_input():
    # move cursor to end then delete
    adb_keyevent(123, wait=0.1)
    for _ in range(40):
        adb_call(["shell", "input", "keyevent", "67"])
    time.sleep(0.3)


def handle_city_picker_error_if_any():
    nodes = dump_ui_nodes()
    if is_city_error_overlay(nodes):
        print("[WARN] City picker error detected")

        refresh_btn = [
            n for n in nodes if n["text"].strip().lower() == "refresh page" and n["clickable"]
        ]
        if refresh_btn:
            tap_node(refresh_btn[0], "Refresh city picker", wait=2.0)
            return True

        back_btn = [
            n for n in nodes if n["text"].strip().lower() == "back" and n["clickable"]
        ]
        if back_btn:
            tap_node(back_btn[0], "Back from city picker error", wait=1.5)
            return False

        adb_keyevent(4, wait=1.2)
        return False

    return True


def recover_to_flight_search(max_steps=4):
    for _ in range(max_steps):
        nodes = dump_ui_nodes()
        if is_flight_search_screen(nodes):
            return True

        if is_city_error_overlay(nodes):
            back_btn = [n for n in nodes if n["text"].strip().lower() == "back" and n["clickable"]]
            if back_btn:
                tap_node(back_btn[0], "Exit city error", wait=1.2)
            else:
                adb_keyevent(4, wait=1.0)
            continue

        if is_city_picker_screen(nodes) or is_calendar_screen(nodes):
            adb_keyevent(4, wait=1.0)
            continue

        adb_keyevent(4, wait=1.0)

    return is_flight_search_screen(dump_ui_nodes())


def choose_city(city_name, city_code):
    city = city_name.lower()
    code = city_code.lower()

    for _ in range(4):
        nodes = dump_ui_nodes()
        if not handle_city_picker_error_if_any():
            return False

        candidates = [
            n
            for n in nodes
            if 420 < n["cy"] < 2200
            and (
                city in n["text"].lower()
                or code in n["text"].lower()
                or city in n["content_desc"].lower()
                or code in n["content_desc"].lower()
            )
        ]
        if candidates:
            clickable = [n for n in candidates if n["clickable"] and n["enabled"]] or candidates
            clickable.sort(key=lambda n: (n["y1"], n["x1"]))
            tap_node(clickable[0], f"Select {city_name} ({city_code})", wait=2.2)
            return True

        time.sleep(1.0)

    # Fallback: first visible suggestion row area
    adb_tap(540, 640, f"Fallback select {city_name}", wait=2.2)
    return False


def set_city(which, city_name, city_code):
    recover_to_flight_search(max_steps=2)
    tap_from_or_to(which)

    # Ensure picker is open
    for _ in range(4):
        if is_city_picker_screen(dump_ui_nodes()):
            break
        time.sleep(1)

    if not is_city_picker_screen(dump_ui_nodes()):
        print(f"[WARN] {which} picker did not open")
        return False

    clear_city_input()
    adb_type(city_name, f"{which} city")
    choose_city(city_name, city_code)

    # Wait to return to search form
    for _ in range(8):
        nodes = dump_ui_nodes()
        if is_flight_search_screen(nodes):
            return True
        if is_city_picker_screen(nodes):
            time.sleep(1)
            continue
        time.sleep(1)

    # Recovery from picker/error states
    recover_to_flight_search(max_steps=3)

    return is_flight_search_screen(dump_ui_nodes())


# -------- Date + Search --------
def date_label_from_nodes(nodes):
    date_nodes = [n for n in nodes if n["resource_id"] == "com.goibibo:id/tv_from_date"]
    if not date_nodes:
        return ""
    return date_nodes[0]["text"].strip().lower()


def set_departure_to_tomorrow():
    recover_to_flight_search(max_steps=3)
    target = datetime.date.today() + datetime.timedelta(days=1)
    target_label = f"{target.day} {target.strftime('%b').lower()}"

    nodes = dump_ui_nodes()
    current = date_label_from_nodes(nodes)
    if target_label == current:
        print(f"[OK] Departure date already set to {target_label}")
        return True

    # Open date picker
    dep_layout = [n for n in nodes if n["resource_id"] == "com.goibibo:id/from_date_layout" and n["clickable"]]
    if dep_layout:
        tap_node(dep_layout[0], "Open departure date", wait=2.2)
    else:
        adb_tap(288, 738, "Fallback departure date tap", wait=2.2)

    # Wait for calendar
    for _ in range(6):
        if is_calendar_screen(dump_ui_nodes()):
            break
        time.sleep(1)

    nodes = dump_ui_nodes()
    if not is_calendar_screen(nodes):
        print("[WARN] Calendar did not open; keeping current date")
        return False

    # Content-desc pattern from dump: "14 APR 2026 Tap to select"
    token = f"{target.day} {target.strftime('%b').upper()} {target.year}"
    day_candidates = [
        n
        for n in nodes
        if token in n["content_desc"].upper() and "MONTHVIEW" in n["class"].upper()
    ]
    if day_candidates:
        day_candidates.sort(key=lambda n: (n["y1"], n["x1"]))
        tap_node(day_candidates[0], f"Pick date {target_label}", wait=1.5)
    else:
        print(f"[WARN] Could not locate {token} in calendar")

    done_btn = [n for n in dump_ui_nodes() if n["resource_id"] == "com.goibibo:id/btnDone" and n["clickable"]]
    if done_btn:
        tap_node(done_btn[0], "Done with date", wait=2.0)
    else:
        adb_tap(540, 2280, "Fallback DONE", wait=2.0)

    return True


def tap_search_flights():
    recover_to_flight_search(max_steps=3)
    nodes = dump_ui_nodes()
    search_btn = [n for n in nodes if n["resource_id"] == "com.goibibo:id/search_button_flat" and n["clickable"]]
    if search_btn:
        tap_node(search_btn[0], "SEARCH FLIGHTS", wait=3.0)
        return True

    fallback_text = [n for n in nodes if "search flights" in n["text"].lower() and n["clickable"]]
    if fallback_text:
        tap_node(fallback_text[0], "SEARCH FLIGHTS (text fallback)", wait=3.0)
        return True

    adb_tap(540, 1125, "SEARCH FLIGHTS fallback tap", wait=3.0)
    return False


# -------- Main Flow --------
def run_goibibo_flight_search():
    if not ensure_adb_path():
        return

    launch_goibibo()

    if not bypass_login_and_reach_home():
        print("[ERROR] Could not bypass login wall and reach home")
        return

    if not open_flights():
        print("[ERROR] Could not open Flight Search screen")
        return

    print("[ACTION] Setting route: Hyderabad -> Delhi")
    from_ok = set_city("FROM", "Hyderabad", "HYD")
    to_ok = set_city("TO", "Delhi", "DEL")

    if not from_ok or not to_ok:
        print("[WARN] City selection had issues. Check internet and retry if needed.")

    print("[ACTION] Setting departure date")
    set_departure_to_tomorrow()

    print("[ACTION] Triggering search")
    tap_search_flights()

    time.sleep(6)
    nodes = dump_ui_nodes()
    if is_flight_search_screen(nodes):
        print("[WARN] Still on search screen. One manual tap on SEARCH FLIGHTS may be needed.")
    else:
        print("[SUCCESS] Flight search triggered. Check device for results page.")


if __name__ == "__main__":
    run_goibibo_flight_search()
