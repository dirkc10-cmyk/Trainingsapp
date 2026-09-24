import os
import json
import sqlite3
from datetime import date, datetime, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

APP_NAME = "TSV Holm Archery Coach PRO"
APP_VERSION = "FINAL116 MOBILE"

BOW_TYPES = ["Olympic Recurve", "Compound", "Barebow", "Traditionell"]
TRAINING_TYPES = [
    "Technik & Qualität", "Volumen & Ausdauer", "Wettkampf", "Kraft & Athletik",
    "Regeneration", "Mentales Training", "Ersatztraining – Urlaub/Zuhause"
]
LOCATIONS = ["Halle 18 m", "Outdoor", "Zuhause", "Verein", "Wettkampf", "Sonstiger Ort"]
VOLUME_UNITS = ["Pfeile", "Minuten", "Sätze", "Wiederholungen"]


def today_iso():
    return date.today().isoformat()


def german_date(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d.%m.%Y")
    except Exception:
        return str(value or "")


def safe_int(value, default=0):
    try:
        return int(float(str(value).replace(",", ".")))
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return default


class MobileDB:
    """Small SQLite store. JSON import/export stays compatible with FINAL115."""

    def __init__(self, root):
        self.root = root
        os.makedirs(root, exist_ok=True)
        self.path = os.path.join(root, "archery_coach_mobile.db")
        self._init()

    def _init(self):
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), data_json TEXT NOT NULL)")
            c.commit()

    def load(self):
        with sqlite3.connect(self.path) as c:
            row = c.execute("SELECT data_json FROM state WHERE id=1").fetchone()
        if not row:
            return {}
        try:
            return json.loads(row[0])
        except Exception:
            return {}

    def save(self, data):
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT OR REPLACE INTO state(id,data_json) VALUES(1,?)", (payload,))
            c.commit()


class FieldRow(BoxLayout):
    def __init__(self, label_text, widget, **kwargs):
        super().__init__(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(48), **kwargs)
        self.add_widget(Label(text=label_text, size_hint_x=0.42, halign="left", valign="middle"))
        self.add_widget(widget)


class MobileCoach(App):
    title_text = StringProperty(APP_NAME)

    def build(self):
        self.db = MobileDB(self.user_data_dir)
        self.data = self._default_data()
        self.data.update(self.db.load())
        self._normalise()
        self.current_screen = "dashboard"
        self.root_box = BoxLayout(orientation="vertical")
        self.header = BoxLayout(size_hint_y=None, height=dp(58), padding=dp(8), spacing=dp(8))
        self.root_box.add_widget(self.header)
        self.content = BoxLayout()
        self.root_box.add_widget(self.content)
        self.nav = BoxLayout(size_hint_y=None, height=dp(66), spacing=dp(4), padding=dp(4))
        self.root_box.add_widget(self.nav)
        self._build_header()
        self._build_nav()
        self.show("dashboard")
        return self.root_box

    def _default_data(self):
        return {
            "profile": {
                "name": "Mein Profil", "bow_type": "Olympic Recurve", "indoor_distance": "18 m",
                "outdoor_distance": "70 m", "competition_format": "", "duration": "90",
                "age": "", "gender": "", "current_level": "", "goal": "",
                "training_days": ["Dienstag", "Donnerstag", "Samstag"], "training_start_time": "18:00",
                "planning_method": "Wettkampforientierte Rückwärtsplanung",
                "equipment_setups": [], "active_equipment_setup": "",
            },
            "training_days": {}, "history": [], "competitions": [], "custom_exercises": []
        }

    def _normalise(self):
        self.data.setdefault("profile", {})
        self.data.setdefault("training_days", {})
        self.data.setdefault("history", [])
        self.data.setdefault("competitions", [])
        self.data.setdefault("custom_exercises", [])
        p = self.data["profile"]
        p.setdefault("name", "Mein Profil")
        p.setdefault("bow_type", "Olympic Recurve")
        p.setdefault("equipment_setups", [])
        p.setdefault("active_equipment_setup", "")
        for h in self.data["history"]:
            h.setdefault("duration_min", 0); h.setdefault("rpe", 0); h.setdefault("readiness", 0)
            h.setdefault("workload", safe_int(h.get("duration_min")) * safe_int(h.get("rpe")))
            h.setdefault("volume_value", h.get("arrows", 0)); h.setdefault("volume_unit", "Pfeile")
            h.setdefault("replacement", False); h.setdefault("notes", "")
        for d, plan in self.data["training_days"].items():
            if isinstance(plan, dict):
                plan.setdefault("type", "Technik & Qualität"); plan.setdefault("replacement", False)
                plan.setdefault("location_mode", "Halle 18 m"); plan.setdefault("start_time", "")
                plan.setdefault("planned_volume", plan.get("arrows", 0)); plan.setdefault("planned_volume_unit", "Pfeile")

    def save(self):
        self._normalise()
        self.db.save(self.data)

    def _build_header(self):
        self.header.clear_widgets()
        title = Label(text=f"[b]{self.title_text}[/b]", markup=True, font_size=dp(18), halign="left", valign="middle")
        self.header.add_widget(title)
        self.header.add_widget(Widget())
        athlete = self.data["profile"].get("name", "Mein Profil")
        self.header.add_widget(Label(text=athlete, size_hint_x=0.45, halign="right", valign="middle"))

    def _build_nav(self):
        self.nav.clear_widgets()
        items = [("⌂", "dashboard"), ("▣", "calendar"), ("✓", "training"), ("▰", "goal"), ("●", "profile")]
        for icon, key in items:
            b = Button(text=f"{icon}\n{ {'dashboard':'Start','calendar':'Kalender','training':'Training','goal':'Ziel','profile':'Profil'}[key] }", font_size=dp(12))
            b.bind(on_release=lambda btn, k=key: self.show(k))
            self.nav.add_widget(b)

    def show(self, screen):
        self.current_screen = screen
        self.content.clear_widgets()
        self._build_header()
        if screen == "dashboard": self._dashboard()
        elif screen == "calendar": self._calendar()
        elif screen == "training": self._training()
        elif screen == "goal": self._goal()
        elif screen == "profile": self._profile()
        elif screen == "equipment": self._equipment()
        elif screen == "data": self._data_screen()
        elif screen == "competitions": self._competitions()
        elif screen == "statistics": self._statistics()

    def scroll(self, widget):
        s = ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=dp(6))
        s.add_widget(widget)
        return s

    def title_label(self, text):
        return Label(text=f"[b]{text}[/b]", markup=True, font_size=dp(21), size_hint_y=None, height=dp(48), halign="left", valign="middle")

    def section(self, text):
        return Label(text=f"[b]{text}[/b]", markup=True, font_size=dp(16), size_hint_y=None, height=dp(42), halign="left", valign="middle")

    def card(self, text, height=90):
        b = Button(text=text, size_hint_y=None, height=dp(height), halign="left", valign="middle")
        b.bind(size=lambda inst, _: setattr(inst, "text_size", (inst.width-dp(20), None)))
        return b

    def _dashboard(self):
        box = GridLayout(cols=1, spacing=dp(10), padding=dp(12), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        p = self.data["profile"]
        hist = self.data["history"]
        plans = self.data["training_days"]
        arrows = sum(safe_int(h.get("volume_value", h.get("arrows", 0))) for h in hist if not h.get("replacement"))
        duration = sum(safe_int(h.get("duration_min")) for h in hist)
        box.add_widget(self.title_label("Heute im Blick"))
        box.add_widget(self.card(f"{p.get('goal') or 'Kein Hauptziel hinterlegt'}\n\n{len(plans)} geplante Tage · {len(hist)} protokollierte Einheiten", 105))
        box.add_widget(self.card(f"TRAININGSVOLUMEN\n{arrows} Pfeile · {duration} Minuten", 90))
        box.add_widget(self.section("Schnellzugriff"))
        b = Button(text="✓ Training protokollieren", size_hint_y=None, height=dp(58)); b.bind(on_release=lambda *_: self.show("training")); box.add_widget(b)
        b = Button(text="▰ Schützenausgabe / Zielstrecke", size_hint_y=None, height=dp(58)); b.bind(on_release=lambda *_: self.show("goal")); box.add_widget(b)
        b = Button(text="▣ Kalender", size_hint_y=None, height=dp(58)); b.bind(on_release=lambda *_: self.show("calendar")); box.add_widget(b)
        b = Button(text="⌁ Material & Bogen", size_hint_y=None, height=dp(58)); b.bind(on_release=lambda *_: self.show("equipment")); box.add_widget(b)
        b = Button(text="⇅ Datenverwaltung", size_hint_y=None, height=dp(58)); b.bind(on_release=lambda *_: self.show("data")); box.add_widget(b)
        self.content.add_widget(self.scroll(box))

    def _calendar(self):
        box = GridLayout(cols=1, spacing=dp(8), padding=dp(12), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        box.add_widget(self.title_label("Mein Kalender"))
        plans = sorted(self.data["training_days"].items())
        if not plans:
            box.add_widget(self.card("Noch keine geplanten Trainingstage.\nTraining kann direkt über „Training“ protokolliert werden.", 90))
        else:
            for d, p in plans:
                done = [h for h in self.data["history"] if h.get("date") == d]
                status = "✓ protokolliert" if done else "geplant"
                text = f"{german_date(d)} · {p.get('type','')}\n{p.get('start_time','')} · {p.get('location_mode','')} · {p.get('planned_volume', p.get('arrows',0))} {p.get('planned_volume_unit','Pfeile')}\n{status}"
                btn = self.card(text, 105)
                btn.bind(on_release=lambda _, day=d: self._open_day_training(day))
                box.add_widget(btn)
        box.add_widget(self.section("Wettkämpfe"))
        for c in sorted(self.data["competitions"], key=lambda x: x.get("date", "")):
            box.add_widget(self.card(f"🏆 {german_date(c.get('date'))} · {c.get('kind','Wettkampf')}\n{c.get('location','')} · {c.get('distance','')}", 82))
        self.content.add_widget(self.scroll(box))

    def _open_day_training(self, day):
        self.training_date = day
        self.show("training")

    def _training(self):
        day = getattr(self, "training_date", today_iso())
        plan = self.data["training_days"].get(day, {})
        existing = [h for h in self.data["history"] if h.get("date") == day]
        box = GridLayout(cols=1, spacing=dp(8), padding=dp(12), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        box.add_widget(self.title_label("Training protokollieren"))
        box.add_widget(Label(text=f"Datum: {german_date(day)}", size_hint_y=None, height=dp(30), halign="left"))
        type_spinner = Spinner(text=plan.get("type", TRAINING_TYPES[0]), values=TRAINING_TYPES, size_hint_y=None, height=dp(48))
        box.add_widget(FieldRow("Training", type_spinner))
        loc_spinner = Spinner(text=plan.get("location_mode", "Halle 18 m"), values=LOCATIONS, size_hint_y=None, height=dp(48))
        box.add_widget(FieldRow("Ort", loc_spinner))
        start = TextInput(text=plan.get("start_time", self.data["profile"].get("training_start_time", "")), multiline=False)
        box.add_widget(FieldRow("Startzeit", start))
        distance = TextInput(text=plan.get("distance", ""), multiline=False)
        box.add_widget(FieldRow("Distanz", distance))
        volume = TextInput(text=str(plan.get("planned_volume", plan.get("arrows", "")) or ""), input_filter="float", multiline=False)
        unit = Spinner(text=plan.get("planned_volume_unit", "Pfeile"), values=VOLUME_UNITS, size_hint_y=None, height=dp(48))
        volrow = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(48)); volrow.add_widget(volume); volrow.add_widget(unit)
        box.add_widget(FieldRow("Ist-Volumen", volrow))
        duration = TextInput(text=str(plan.get("duration_min", self.data["profile"].get("duration", "")) or ""), input_filter="int", multiline=False)
        box.add_widget(FieldRow("Dauer (min)", duration))
        score = TextInput(text=existing[-1].get("score", "") if existing else "", multiline=False)
        box.add_widget(FieldRow("Ergebnis", score))
        rpe = TextInput(text=str(existing[-1].get("rpe", "") or ""), input_filter="int", multiline=False)
        readiness = TextInput(text=str(existing[-1].get("readiness", "") or ""), input_filter="int", multiline=False)
        box.add_widget(FieldRow("RPE 1–10", rpe)); box.add_widget(FieldRow("Readiness 1–10", readiness))
        notes = TextInput(text=existing[-1].get("notes", "") if existing else "", multiline=True, size_hint_y=None, height=dp(110))
        box.add_widget(FieldRow("Notizen", notes))
        replace = CheckBox(active=bool(plan.get("replacement", False) or (existing and existing[-1].get("replacement"))))
        box.add_widget(FieldRow("Ersatztraining", replace))
        box.add_widget(Label(text="Mehrere Einheiten pro Tag sind möglich: speichern legt eine neue Einheit an.", size_hint_y=None, height=dp(48), halign="left", valign="middle"))
        save_btn = Button(text="✓ Einheit speichern", size_hint_y=None, height=dp(58))
        save_btn.bind(on_release=lambda *_: self._save_training(day, type_spinner, loc_spinner, start, distance, volume, unit, duration, score, rpe, readiness, notes, replace))
        box.add_widget(save_btn)
        if existing:
            box.add_widget(self.section(f"Einheiten am {german_date(day)}"))
            for i, h in enumerate(existing, 1):
                box.add_widget(self.card(f"Einheit {i} · {h.get('type','')}\n{h.get('volume_value',h.get('arrows',0))} {h.get('volume_unit','Pfeile')} · {h.get('duration_min',0)} min · RPE {h.get('rpe','—')}\n{h.get('notes','')}", 105))
        self.content.add_widget(self.scroll(box))

    def _save_training(self, day, type_w, loc_w, start, distance, volume, unit, duration, score, rpe, readiness, notes, replace):
        vol = safe_float(volume.text)
        dur = safe_int(duration.text)
        rp = safe_int(rpe.text); rd = safe_int(readiness.text)
        is_repl = replace.active or type_w.text.startswith("Ersatztraining")
        arrows = safe_int(vol) if unit.text == "Pfeile" and not is_repl else 0
        entry = {
            "date": day, "type": type_w.text, "training_type": type_w.text,
            "environment": loc_w.text, "location": loc_w.text, "location_mode": loc_w.text,
            "start_time": start.text.strip(), "distance": distance.text.strip(),
            "arrows": arrows, "volume_value": vol, "volume_unit": unit.text,
            "planned_volume": safe_float(self.data["training_days"].get(day, {}).get("planned_volume", 0)),
            "planned_volume_unit": self.data["training_days"].get(day, {}).get("planned_volume_unit", "Pfeile"),
            "duration_min": dur, "score": score.text.strip(), "rpe": rp, "readiness": rd,
            "workload": dur * rp, "performance_arrows_per_hour": (vol / dur * 60.0 if unit.text == "Pfeile" and dur else None),
            "notes": notes.text.strip(), "replacement": bool(is_repl),
            "equipment_setup": self.data["profile"].get("active_equipment_setup", ""),
        }
        self.data["history"].append(entry)
        self.data["training_days"].setdefault(day, {})
        self.data["training_days"][day].update({
            "type": type_w.text, "replacement": bool(is_repl), "location_mode": loc_w.text,
            "start_time": start.text.strip(), "distance": distance.text.strip(),
            "actual_arrows": arrows, "actual_volume": vol, "actual_duration_min": dur,
            "actual_rpe": rp, "actual_readiness": rd, "actual_workload": dur * rp, "training_logged": True,
        })
        self.save()
        self._toast("Training gespeichert.")
        self.show("training")

    def _goal(self):
        p = self.data["profile"]
        target = next((c for c in self.data["competitions"] if c.get("is_main")), None)
        if not target:
            target = sorted(self.data["competitions"], key=lambda x: x.get("date", ""))[-1] if self.data["competitions"] else None
        box = GridLayout(cols=1, spacing=dp(8), padding=dp(12), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        box.add_widget(self.title_label("Schützenausgabe"))
        box.add_widget(self.card(f"HAUPTZIEL\n{p.get('goal') or 'Noch kein Ziel hinterlegt'}\n\nWettkampf: {german_date(target.get('date')) if target else '—'} · {target.get('kind','') if target else '—'}", 115))
        hist = self.data["history"]
        arrows = sum(safe_int(h.get("volume_value", h.get("arrows",0))) for h in hist if not h.get("replacement"))
        duration = sum(safe_int(h.get("duration_min")) for h in hist)
        box.add_widget(self.card(f"TRAININGSSTATUS\n{len(hist)} protokollierte Einheiten\n{arrows} Pfeile · {duration} Minuten", 90))
        box.add_widget(self.section("Gesamte Zielstrecke / Saison"))
        days = sorted(set(list(self.data["training_days"].keys()) + [h.get("date") for h in hist if h.get("date")]))
        if not days:
            box.add_widget(self.card("Noch keine Trainingstage vorhanden.", 80))
        for d in days:
            plan = self.data["training_days"].get(d, {})
            sessions = [h for h in hist if h.get("date") == d]
            state = "✓" if sessions else ("○" if d >= today_iso() else "⚠")
            text = f"{state} {german_date(d)} · {plan.get('type','Trainingstag')}\n{plan.get('location_mode','')} · {plan.get('planned_volume',plan.get('arrows',0))} {plan.get('planned_volume_unit','Pfeile')}\n{len(sessions)} protokollierte Einheit(en)"
            btn = self.card(text, 92); btn.bind(on_release=lambda _, day=d: self._open_day_training(day)); box.add_widget(btn)
        box.add_widget(self.section("Aktives Material"))
        active = self._active_setup()
        box.add_widget(self.card(active.get("name", "Kein Setup") if active else "Kein aktives Materialsetup", 70))
        self.content.add_widget(self.scroll(box))

    def _active_setup(self):
        name = self.data["profile"].get("active_equipment_setup", "")
        return next((x for x in self.data["profile"].get("equipment_setups", []) if x.get("name") == name), {})

    def _equipment(self):
        p = self.data["profile"]
        setups = p.get("equipment_setups", [])
        box = GridLayout(cols=1, spacing=dp(8), padding=dp(12), size_hint_y=None); box.bind(minimum_height=box.setter("height"))
        box.add_widget(self.title_label("Material & Bogen"))
        box.add_widget(self.card(f"Bogenart: {p.get('bow_type','')}\nAktives Setup: {p.get('active_equipment_setup') or '—'}", 82))
        for s in setups:
            b = self.card(f"{s.get('name','Setup')}\n{s.get('bow_type',p.get('bow_type',''))} · Pfeile: {s.get('arrows','')} · Spine: {s.get('spine','')}", 82)
            b.bind(on_release=lambda _, name=s.get('name',''): self._activate_setup(name))
            box.add_widget(b)
        add = Button(text="＋ Neues Setup", size_hint_y=None, height=dp(58)); add.bind(on_release=lambda *_: self._setup_popup()); box.add_widget(add)
        self.content.add_widget(self.scroll(box))

    def _activate_setup(self, name):
        self.data["profile"]["active_equipment_setup"] = name; self.save(); self.show("equipment")

    def _setup_popup(self):
        grid = GridLayout(cols=1, spacing=dp(8), padding=dp(12), size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        fields = {}
        for key, label in [("name","Setupname"),("bow_type","Bogenart"),("riser","Mittelteil"),("limbs","Wurfarme"),("arrows","Pfeile"),("spine","Spine"),("arrow_length","Pfeillänge"),("point_weight","Spitzengewicht"),("draw_length","Auszugslänge"),("draw_weight","Zuggewicht")]:
            w = TextInput(text="", multiline=False, size_hint_y=None, height=dp(46)); fields[key] = w; grid.add_widget(FieldRow(label,w))
        saveb = Button(text="Speichern", size_hint_y=None, height=dp(54)); grid.add_widget(saveb)
        pop = Popup(title="Materialsetup", content=self.scroll(grid), size_hint=(0.95,0.9))
        def save_setup(*_):
            name = fields["name"].text.strip() or f"Setup {len(self.data['profile'].get('equipment_setups',[]))+1}"
            item = {k: v.text.strip() for k,v in fields.items()}; item["name"] = name
            self.data["profile"].setdefault("equipment_setups", []).append(item)
            self.data["profile"]["active_equipment_setup"] = name; self.save(); pop.dismiss(); self.show("equipment")
        saveb.bind(on_release=save_setup); pop.open()

    def _profile(self):
        p = self.data["profile"]
        box = GridLayout(cols=1, spacing=dp(8), padding=dp(12), size_hint_y=None); box.bind(minimum_height=box.setter("height"))
        box.add_widget(self.title_label("Mein Profil"))
        fields = {}
        for key, label in [("name","Name"),("bow_type","Bogenart"),("indoor_distance","Halle"),("outdoor_distance","Outdoor"),("competition_format","Wettkampfformat"),("duration","Trainingsdauer min"),("age","Alter"),("gender","Geschlecht"),("current_level","Aktuelles Niveau"),("goal","Hauptziel"),("training_start_time","Startzeit")]:
            if key == "bow_type":
                w = Spinner(text=p.get(key,"Olympic Recurve"), values=BOW_TYPES, size_hint_y=None, height=dp(48))
            else:
                w = TextInput(text=str(p.get(key,"")), multiline=(key=="goal"), size_hint_y=None, height=dp(82) if key=="goal" else dp(48))
            fields[key]=w; box.add_widget(FieldRow(label,w))
        saveb = Button(text="✓ Profil speichern", size_hint_y=None, height=dp(58)); box.add_widget(saveb)
        saveb.bind(on_release=lambda *_: self._save_profile(fields))
        eb = Button(text="⌁ Material & Bogen", size_hint_y=None, height=dp(58)); eb.bind(on_release=lambda *_: self.show("equipment")); box.add_widget(eb)
        db = Button(text="⇅ Datenverwaltung", size_hint_y=None, height=dp(58)); db.bind(on_release=lambda *_: self.show("data")); box.add_widget(db)
        self.content.add_widget(self.scroll(box))

    def _save_profile(self, fields):
        for k,w in fields.items(): self.data["profile"][k] = w.text if hasattr(w,"text") else w.text
        self.save(); self._toast("Profil gespeichert."); self.show("profile")

    def _competitions(self):
        box = GridLayout(cols=1, spacing=dp(8), padding=dp(12), size_hint_y=None); box.bind(minimum_height=box.setter("height"))
        box.add_widget(self.title_label("Wettkämpfe"))
        for c in sorted(self.data["competitions"], key=lambda x:x.get("date","")):
            main = " · HAUPTZIEL" if c.get("is_main") else ""
            box.add_widget(self.card(f"🏆 {german_date(c.get('date'))}{main}\n{c.get('kind','')} · {c.get('location','')}\n{c.get('distance','')}", 92))
        add = Button(text="＋ Wettkampf hinzufügen", size_hint_y=None, height=dp(58)); add.bind(on_release=lambda *_: self._competition_popup()); box.add_widget(add)
        self.content.add_widget(self.scroll(box))

    def _competition_popup(self):
        grid=GridLayout(cols=1, spacing=dp(8), padding=dp(12), size_hint_y=None); grid.bind(minimum_height=grid.setter("height")); f={}
        for k,l in [("date","Datum YYYY-MM-DD"),("kind","Wettkampf"),("location","Ort"),("distance","Distanz")]:
            w=TextInput(text=today_iso() if k=="date" else "", multiline=False, size_hint_y=None, height=dp(46)); f[k]=w; grid.add_widget(FieldRow(l,w))
        cb=CheckBox(); grid.add_widget(FieldRow("Hauptziel",cb)); sb=Button(text="Speichern",size_hint_y=None,height=dp(54)); grid.add_widget(sb)
        pop=Popup(title="Wettkampf",content=self.scroll(grid),size_hint=(0.95,0.8))
        def savec(*_):
            item={k:v.text.strip() for k,v in f.items()}; item["is_main"]=cb.active; self.data["competitions"].append(item); self.save(); pop.dismiss(); self.show("competitions")
        sb.bind(on_release=savec); pop.open()

    def _statistics(self):
        hist=self.data["history"]; arrows=sum(safe_int(h.get("volume_value",h.get("arrows",0))) for h in hist if not h.get("replacement")); mins=sum(safe_int(h.get("duration_min")) for h in hist); rpes=[safe_int(h.get("rpe")) for h in hist if safe_int(h.get("rpe"))]
        box=GridLayout(cols=1,spacing=dp(8),padding=dp(12),size_hint_y=None);box.bind(minimum_height=box.setter("height"));box.add_widget(self.title_label("Leistungsanalyse"));box.add_widget(self.card(f"Einheiten: {len(hist)}\nPfeile: {arrows}\nTrainingszeit: {mins} min\nØ RPE: {sum(rpes)/len(rpes):.1f}" if rpes else f"Einheiten: {len(hist)}\nPfeile: {arrows}\nTrainingszeit: {mins} min\nØ RPE: —",110)); self.content.add_widget(self.scroll(box))

    def _data_screen(self):
        box=GridLayout(cols=1,spacing=dp(10),padding=dp(12),size_hint_y=None);box.bind(minimum_height=box.setter("height"));box.add_widget(self.title_label("Datenverwaltung"));
        box.add_widget(self.card(f"Lokale Datenbank:\n{self.db.path}\n\nJSON ist das Austauschformat mit der Windows-Version FINAL115.",100))
        exp=Button(text="⇩ JSON exportieren",size_hint_y=None,height=dp(58));exp.bind(on_release=lambda *_: self._export_json());box.add_widget(exp)
        imp=Button(text="⇧ JSON importieren",size_hint_y=None,height=dp(58));imp.bind(on_release=lambda *_: self._import_popup());box.add_widget(imp)
        box.add_widget(self.card("Hinweis: Auf Android kann eine Datei über den System-Dateidialog ausgewählt werden. Der Export wird im App-Datenordner abgelegt.",100));self.content.add_widget(self.scroll(box))

    def _export_json(self):
        path=os.path.join(self.user_data_dir,f"archery_coach_export_{date.today().isoformat()}.json")
        with open(path,"w",encoding="utf-8") as f: json.dump(self.data,f,ensure_ascii=False,indent=2)
        self._toast(f"Export gespeichert:\n{path}")

    def _import_popup(self):
        grid=GridLayout(cols=1,spacing=dp(8),padding=dp(12),size_hint_y=None);grid.bind(minimum_height=grid.setter("height"));grid.add_widget(Label(text="Pfad zur JSON-Datei eingeben.\nUnter Android kann die Datei zuvor in den App-Datenordner kopiert werden.",size_hint_y=None,height=dp(90)))
        inp=TextInput(multiline=False,size_hint_y=None,height=dp(48));grid.add_widget(inp);sb=Button(text="Importieren",size_hint_y=None,height=dp(54));grid.add_widget(sb);pop=Popup(title="JSON importieren",content=self.scroll(grid),size_hint=(0.95,0.65))
        def do(*_):
            path=inp.text.strip()
            try:
                with open(path,"r",encoding="utf-8") as f:self.data=json.load(f)
                self._normalise();self.save();pop.dismiss();self.show("dashboard");self._toast("Daten importiert.")
            except Exception as exc:self._toast(f"Importfehler: {exc}")
        sb.bind(on_release=do);pop.open()

    def _toast(self,text):
        lbl=Label(text=text,size_hint_y=None,height=dp(70),halign="center",valign="middle")
        pop=Popup(title="TSV Holm",content=lbl,size_hint=(0.9,None),height=dp(150),auto_dismiss=True)
        pop.open();Clock.schedule_once(lambda *_: pop.dismiss(),2.2)

    def on_stop(self):
        self.save()


if __name__ == "__main__":
    MobileCoach().run()
