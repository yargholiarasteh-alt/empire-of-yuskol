# -*- coding: utf-8 -*-
"""
EMPIRE OF YUSKOL — Generation III
A fresh, offline-first Kivy grand-strategy/economy prototype.
Designed for Android / Pydroid 3. No external assets required.
"""
import json
import os
import random
import shutil
from datetime import date

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar

Window.clearcolor = (0.035, 0.055, 0.09, 1)

# ---------- Theme ----------
BG = (0.035, 0.055, 0.09, 1)
PANEL = (0.075, 0.105, 0.15, 1)
BLUE = (0.12, 0.32, 0.52, 1)
GOLD = (0.68, 0.48, 0.16, 1)
GREEN = (0.12, 0.38, 0.27, 1)
RED = (0.48, 0.16, 0.17, 1)

# ---------- Persian text and font ----------
# Kivy's default font may not contain Persian glyphs. Prefer Android's
# Arabic-capable system fonts, then a local Vazirmatn font.
FONT_CANDIDATES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Vazirmatn-Regular.ttf"),
    "/system/fonts/NotoNaskhArabicUI-Regular.ttf",
    "/system/fonts/NotoSansArabicUI-Regular.ttf",
    "/system/fonts/NotoNaskhArabic-Regular.ttf",
    "/system/fonts/NotoSansArabic-Regular.ttf",
]
PERSIAN_FONT = next((f for f in FONT_CANDIDATES if os.path.isfile(f)), "")
if PERSIAN_FONT:
    LabelBase.register(name="YuskolPersian", fn_regular=PERSIAN_FONT)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    PERSIAN_SHAPING_AVAILABLE = True
    def fa(value):
        try:
            return get_display(arabic_reshaper.reshape(str(value)))
        except Exception:
            return str(value)
except Exception:
    PERSIAN_SHAPING_AVAILABLE = False
    def fa(value):
        return str(value)

FONT_KW = {"font_name": "YuskolPersian"} if PERSIAN_FONT else {}

# ---------- Game data ----------
RESOURCE_NAMES = {
    "gold": "طلا", "food": "غذا", "wood": "چوب",
    "stone": "سنگ", "iron": "آهن"
}

BUILDINGS = {
    "farm": {
        "name": "مزرعه", "cost": {"gold": 120, "wood": 35},
        "upkeep": {"gold": 4}, "production": {"food": 32},
        "description": "تولید غذا برای جمعیت"
    },
    "lumber": {
        "name": "کارگاه چوب‌بری", "cost": {"gold": 150, "wood": 20},
        "upkeep": {"gold": 5}, "production": {"wood": 16},
        "description": "تولید چوب برای ساخت‌وساز"
    },
    "mine": {
        "name": "معدن آهن", "cost": {"gold": 220, "wood": 30, "stone": 25},
        "upkeep": {"gold": 8}, "production": {"iron": 12},
        "description": "استخراج آهن برای توسعه و ارتش"
    },
    "quarry": {
        "name": "سنگ‌بری", "cost": {"gold": 180, "wood": 25},
        "upkeep": {"gold": 6}, "production": {"stone": 18},
        "description": "استخراج سنگ ساختمانی"
    },
    "market": {
        "name": "بازار", "cost": {"gold": 250, "wood": 45, "stone": 20},
        "upkeep": {"gold": 7}, "production": {},
        "description": "افزایش درآمد مالیاتی شهر"
    },
    "granary": {
        "name": "انبار غله", "cost": {"gold": 170, "wood": 40},
        "upkeep": {"gold": 3}, "production": {},
        "description": "افزایش ظرفیت ذخیره غذا"
    },
    "barracks": {
        "name": "پادگان", "cost": {"gold": 280, "wood": 55, "iron": 20},
        "upkeep": {"gold": 12}, "production": {},
        "description": "افزایش ظرفیت و آمادگی ارتش"
    },
    "university": {
        "name": "دانشگاه", "cost": {"gold": 420, "wood": 70, "stone": 60},
        "upkeep": {"gold": 10}, "production": {},
        "description": "افزایش سرعت پژوهش علمی"
    },
    "workshop": {
        "name": "کارخانه", "cost": {"gold": 360, "wood": 55, "iron": 35},
        "upkeep": {"gold": 9}, "production": {"wood": 5},
        "description": "تقویت تولید و صنعت"
    },
    "hospital": {
        "name": "درمانگاه", "cost": {"gold": 300, "wood": 45, "stone": 35},
        "upkeep": {"gold": 8}, "production": {},
        "description": "حفظ سلامت و ثبات جمعیت"
    },
}

DEFAULT_STATE = {
    "schema": 3,
    "day": 1,
    "year": 1,
    "gold": 1200,
    "food": 420,
    "wood": 180,
    "stone": 100,
    "iron": 65,
    "population": 420,
    "happiness": 72,
    "tax_rate": 10,
    "army": 45,
    "army_level": 1,
    "cities": {
        "یوسکول‌شهر": {
            "level": 1,
            "buildings": {"farm": 2, "lumber": 1, "mine": 0,
                          "quarry": 0, "market": 1, "granary": 1,
                          "barracks": 1}
        }
    },
    "log": ["امپراتوری یوسکول تأسیس شد."],
    "last_daily_reward": "",
    "legacy_imported": False,
    "research": {"agriculture": 0, "commerce": 0, "industry": 0, "military": 0},
    "trade_index": 0,
    "stability": 75,
    "treasury_reserve": 0,
    "policy": "متعادل",
}

class YuskolEmpire(App):
    def build(self):
        self.title = "امپراتوری یوسکول — نسل سوم"
        self.state = self.new_state()
        self.load_game(silent=True)
        if not PERSIAN_FONT:
            self.add_log("فونت فارسی پیدا نشد؛ فایل Vazirmatn-Regular.ttf را کنار فایل بازی قرار دهید.")
        if not PERSIAN_SHAPING_AVAILABLE:
            self.add_log("برای اتصال حروف فارسی، arabic-reshaper و python-bidi را نصب کنید.")

        self.root_box = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(7))
        self.header = Label(text="", size_hint_y=None, height=dp(112),
                            font_size=sp(13), color=(0.94, 0.91, 0.82, 1),
                            halign="center", valign="middle", **FONT_KW)
        self.header.bind(size=lambda *_: setattr(self.header, "text_size", self.header.size))
        self.root_box.add_widget(self.header)

        self.body = BoxLayout(orientation="vertical", spacing=dp(6))
        self.root_box.add_widget(self.body)
        self.show_dashboard()
        return self.root_box

    def new_state(self):
        return json.loads(json.dumps(DEFAULT_STATE, ensure_ascii=False))

    @property
    def save_path(self):
        return os.path.join(self.user_data_dir, "yuskol_gen2_save.json")

    def add_log(self, message):
        self.state.setdefault("log", []).insert(0, str(message))
        self.state["log"] = self.state["log"][:35]

    def refresh_header(self):
        s = self.state
        self.header.text = fa(
            f"امپراتوری یوسکول  |  سال {s['year']} - روز {s['day']}\n"
            f"خزانه: {s['gold']} طلا   غذا: {s['food']}   چوب: {s['wood']}\n"
            f"سنگ: {s['stone']}   آهن: {s['iron']}   جمعیت: {s['population']}\n"
            f"رضایت: {s['happiness']}٪   مالیات: {s['tax_rate']}٪   ارتش: {s['army']}"
        )

    def clear_body(self):
        self.body.clear_widgets()
        self.refresh_header()

    def make_button(self, caption, callback, color=BLUE, height=dp(45)):
        b = Button(text=fa(caption), font_size=sp(14), size_hint_y=None,
                   height=height, background_normal="", background_color=color,
                   color=(1, 1, 1, 1), **FONT_KW)
        b.bind(on_release=lambda *_: callback())
        return b

    def make_label(self, caption, height=dp(34), size=14):
        lab = Label(text=fa(caption), font_size=sp(size), size_hint_y=None,
                    height=height, halign="center", valign="middle",
                    color=(0.92, 0.93, 0.96, 1), **FONT_KW)
        lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
        return lab

    def make_scroll(self):
        sc = ScrollView()
        grid = GridLayout(cols=1, spacing=dp(6), padding=dp(3), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        sc.add_widget(grid)
        return sc, grid

    def popup(self, title, message):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        box.add_widget(self.make_label(message, dp(100), 14))
        pop = Popup(title=fa(title), content=box, size_hint=(0.88, 0.42),
                    title_font="YuskolPersian" if PERSIAN_FONT else "Roboto")
        box.add_widget(self.make_button("باشه", pop.dismiss, GREEN))
        pop.open()

    def show_dashboard(self):
        self.clear_body()
        self.body.add_widget(self.make_label("پایتخت امپراتوری؛ مرکز اداره کشور", dp(42), 17))
        self.body.add_widget(self.make_label(
            f"شهرها: {len(self.state['cities'])}  |  درآمد خالص تقریبی: {self.estimate_net_income()} طلا در روز",
            dp(36), 13))
        actions = [
            ("گزارش اقتصادی", self.show_economy),
            ("شهرها و ساختمان‌ها", self.show_cities),
            ("بازار منابع", self.show_market),
            ("حکومت و مالیات", self.show_government),
            ("پژوهش و فناوری", self.show_research),
            ("سیاست‌های اقتصادی", self.show_policies),
            ("ارتش و پادگان", self.show_army),
            ("پایان روز و محاسبه اقتصاد", self.next_day, GREEN),
            ("گزارش رویدادها", self.show_log),
            ("ذخیره بازی", self.save_game),
        ]
        sc, grid = self.make_scroll()
        for item in actions:
            label, fn = item[0], item[1]
            color = item[2] if len(item) > 2 else BLUE
            grid.add_widget(self.make_button(label, fn, color))
        self.body.add_widget(sc)

    def total_building_count(self, key):
        return sum(city["buildings"].get(key, 0) for city in self.state["cities"].values())

    def estimate_net_income(self):
        s = self.state
        base_tax = int(s["population"] * s["tax_rate"] / 100 * 0.035)
        market_bonus = self.total_building_count("market") * 8 + self.total_building_count("workshop") * 2
        upkeep = sum(
            count * BUILDINGS[key]["upkeep"].get("gold", 0)
            for city in s["cities"].values()
            for key, count in city["buildings"].items()
        )
        army_upkeep = s["army"] // 8
        return base_tax + market_bonus - upkeep - army_upkeep

    def show_economy(self):
        self.clear_body()
        s = self.state
        self.body.add_widget(self.make_label("گزارش اقتصادی امپراتوری", dp(42), 18))
        lines = [
            f"درآمد مالیاتی روزانه: {int(s['population'] * s['tax_rate'] / 100 * 0.035)} طلا",
            f"درآمد بازارها: {self.total_building_count('market') * 8} طلا",
            f"هزینه نگهداری ساختمان‌ها: {self.building_upkeep()} طلا",
            f"هزینه نگهداری ارتش: {s['army'] // 8} طلا",
            f"تراز روزانه: {self.estimate_net_income()} طلا",
            f"تولید غذا در روز: {self.total_production('food')}",
            f"مصرف غذا در روز: {max(1, s['population'] // 80)}",
            f"ظرفیت انبار غذا: {600 + self.total_building_count('granary') * 500}",
            f"سطح فناوری: کشاورزی {s.get('research', {}).get('agriculture', 0)} | تجارت {s.get('research', {}).get('commerce', 0)} | صنعت {s.get('research', {}).get('industry', 0)} | نظامی {s.get('research', {}).get('military', 0)}",
            f"ثبات کشور: {s.get('stability', 75)}٪ | سیاست: {s.get('policy', 'متعادل')}",
        ]
        sc, grid = self.make_scroll()
        for line in lines:
            grid.add_widget(self.make_label(line, dp(36), 14))
        grid.add_widget(self.make_button("بازگشت", self.show_dashboard))
        self.body.add_widget(sc)

    def building_upkeep(self):
        return sum(
            count * BUILDINGS[key]["upkeep"].get("gold", 0)
            for city in self.state["cities"].values()
            for key, count in city["buildings"].items()
        )

    def total_production(self, resource):
        return sum(
            count * BUILDINGS[key]["production"].get(resource, 0)
            for city in self.state["cities"].values()
            for key, count in city["buildings"].items()
        )

    def show_cities(self):
        self.clear_body()
        self.body.add_widget(self.make_label("شهرهای امپراتوری", dp(40), 18))
        sc, grid = self.make_scroll()
        for city_name, city in self.state["cities"].items():
            grid.add_widget(self.make_button(
                f"{city_name} | سطح {city['level']} | ساختمان‌ها: {sum(city['buildings'].values())}",
                lambda n=city_name: self.show_city(n), GOLD))
        grid.add_widget(self.make_button("تأسیس شهر جدید (۶۰۰ طلا، ۱۰۰ چوب، ۵۰ سنگ)",
                                         self.found_city, GREEN))
        grid.add_widget(self.make_button("بازگشت", self.show_dashboard))
        self.body.add_widget(sc)

    def show_city(self, city_name):
        self.clear_body()
        city = self.state["cities"][city_name]
        self.body.add_widget(self.make_label(city_name, dp(42), 18))
        sc, grid = self.make_scroll()
        for key, data in BUILDINGS.items():
            count = city["buildings"].get(key, 0)
            grid.add_widget(self.make_label(
                f"{data['name']} | تعداد: {count}\n{data['description']}", dp(55), 13))
            cost = "، ".join(f"{RESOURCE_NAMES[k]} {v}" for k, v in data["cost"].items())
            grid.add_widget(self.make_button(
                f"ساخت {data['name']} ({cost})",
                lambda n=city_name, k=key: self.build_structure(n, k)))
        grid.add_widget(self.make_button("ارتقای شهر (۳۵۰ طلا، ۶۰ چوب، ۴۰ سنگ)",
                                         lambda: self.upgrade_city(city_name), GOLD))
        grid.add_widget(self.make_button("بازگشت", self.show_cities))
        self.body.add_widget(sc)

    def can_pay(self, costs):
        return all(self.state.get(resource, 0) >= amount for resource, amount in costs.items())

    def pay(self, costs):
        for resource, amount in costs.items():
            self.state[resource] -= amount

    def build_structure(self, city_name, key):
        data = BUILDINGS[key]
        if not self.can_pay(data["cost"]):
            self.popup("منابع ناکافی", "منابع لازم برای ساخت این ساختمان کافی نیست.")
            return
        self.pay(data["cost"])
        self.state["cities"][city_name]["buildings"][key] = (
            self.state["cities"][city_name]["buildings"].get(key, 0) + 1)
        self.add_log(f"در {city_name} ساختمان {data['name']} ساخته شد.")
        self.save_game(silent=True)
        self.show_city(city_name)

    def upgrade_city(self, city_name):
        costs = {"gold": 350, "wood": 60, "stone": 40}
        if not self.can_pay(costs):
            self.popup("منابع ناکافی", "برای ارتقای شهر طلا، چوب و سنگ کافی نیست.")
            return
        self.pay(costs)
        self.state["cities"][city_name]["level"] += 1
        self.state["population"] += 80
        self.state["happiness"] = max(0, self.state["happiness"] - 2)
        self.add_log(f"سطح شهر {city_name} افزایش یافت.")
        self.save_game(silent=True)
        self.show_city(city_name)

    def found_city(self):
        costs = {"gold": 600, "wood": 100, "stone": 50}
        if len(self.state["cities"]) >= 8:
            self.popup("محدودیت", "در این مرحله حداکثر ۸ شهر قابل اداره است.")
            return
        if not self.can_pay(costs):
            self.popup("منابع ناکافی", "برای تأسیس شهر جدید منابع کافی نیست.")
            return
        self.pay(costs)
        name = f"شهر نوین {len(self.state['cities'])}"
        self.state["cities"][name] = {
            "level": 1,
            "buildings": {"farm": 1, "lumber": 0, "mine": 0,
                          "quarry": 0, "market": 0, "granary": 0, "barracks": 0}
        }
        self.add_log(f"شهر تازه‌ای به نام {name} تأسیس شد.")
        self.save_game(silent=True)
        self.show_cities()

    def show_market(self):
        self.clear_body()
        self.body.add_widget(self.make_label("بازار منابع", dp(42), 18))
        sc, grid = self.make_scroll()
        base_prices = {"food": 2, "wood": 4, "stone": 5, "iron": 8}
        index = self.state.get("trade_index", 0)
        prices = {k: max(1, int(v * (100 + index) / 100)) for k, v in base_prices.items()}
        for resource, price in prices.items():
            grid.add_widget(self.make_label(
                f"{RESOURCE_NAMES[resource]}: {self.state[resource]} | قیمت پایه هر واحد: {price} طلا",
                dp(35), 13))
            grid.add_widget(self.make_button(
                f"خرید ۲۵ واحد {RESOURCE_NAMES[resource]} ({price * 25} طلا)",
                lambda r=resource, p=price: self.trade(r, 25, p, True)))
            grid.add_widget(self.make_button(
                f"فروش ۲۵ واحد {RESOURCE_NAMES[resource]} ({max(1, int(price * .7)) * 25} طلا)",
                lambda r=resource, p=price: self.trade(r, 25, max(1, int(p * .7)), False)))
        grid.add_widget(self.make_label(f"شاخص قیمت بازار: {100 + self.state.get('trade_index', 0)}٪", dp(35), 13))
        grid.add_widget(self.make_button("بازگشت", self.show_dashboard))
        self.body.add_widget(sc)

    def trade(self, resource, amount, price, buying):
        if buying:
            total = amount * price
            if self.state["gold"] < total:
                self.popup("خزانه ناکافی", "طلای کافی برای این معامله نداری.")
                return
            self.state["gold"] -= total
            self.state[resource] += amount
            message = f"{amount} واحد {RESOURCE_NAMES[resource]} خریداری شد."
        else:
            if self.state[resource] < amount:
                self.popup("موجودی ناکافی", f"{RESOURCE_NAMES[resource]} کافی برای فروش نداری.")
                return
            self.state[resource] -= amount
            total = amount * price
            self.state["gold"] += total
            message = f"{amount} واحد {RESOURCE_NAMES[resource]} فروخته شد."
        self.add_log(message)
        self.save_game(silent=True)
        self.show_market()

    def show_government(self):
        self.clear_body()
        s = self.state
        self.body.add_widget(self.make_label("حکومت و سیاست مالی", dp(42), 18))
        self.body.add_widget(self.make_label(
            f"نرخ مالیات فعلی: {s['tax_rate']}٪ | رضایت مردم: {s['happiness']}٪",
            dp(42), 14))
        sc, grid = self.make_scroll()
        for rate in (5, 8, 10, 12, 15, 18, 20):
            grid.add_widget(self.make_button(
                f"تعیین مالیات روی {rate}٪",
                lambda r=rate: self.set_tax(r),
                GREEN if rate <= 10 else RED))
        grid.add_widget(self.make_button("برگزاری جشن مردمی (۱۲۰ طلا، +۸ رضایت)",
                                         self.hold_festival, GOLD))
        grid.add_widget(self.make_button("بازگشت", self.show_dashboard))
        self.body.add_widget(sc)

    def set_tax(self, rate):
        old = self.state["tax_rate"]
        self.state["tax_rate"] = rate
        if rate > old:
            self.state["happiness"] = max(0, self.state["happiness"] - (rate - old) // 2)
        else:
            self.state["happiness"] = min(100, self.state["happiness"] + (old - rate) // 3)
        self.add_log(f"نرخ مالیات به {rate} درصد تغییر کرد.")
        self.save_game(silent=True)
        self.show_government()

    def hold_festival(self):
        if self.state["gold"] < 120:
            self.popup("خزانه ناکافی", "برای برگزاری جشن ۱۲۰ طلا لازم است.")
            return
        self.state["gold"] -= 120
        self.state["happiness"] = min(100, self.state["happiness"] + 8)
        self.add_log("جشن عمومی برگزار شد؛ رضایت مردم افزایش یافت.")
        self.save_game(silent=True)
        self.show_government()

    def show_research(self):
        self.clear_body()
        self.body.add_widget(self.make_label("دانشگاه و پژوهش‌های امپراتوری", dp(42), 18))
        research = self.state.setdefault("research", {"agriculture": 0, "commerce": 0, "industry": 0, "military": 0})
        names = {"agriculture": "کشاورزی", "commerce": "بازرگانی", "industry": "صنعت", "military": "فنون نظامی"}
        sc, grid = self.make_scroll()
        universities = self.total_building_count("university")
        grid.add_widget(self.make_label(f"دانشگاه‌های فعال: {universities} | هر پژوهش به دانشگاه نیاز دارد", dp(38), 13))
        for key, title in names.items():
            level = research.get(key, 0)
            cost = 250 + level * 180
            grid.add_widget(self.make_label(f"{title} | سطح {level} | هزینه پژوهش: {cost} طلا و {10 + level * 5} آهن", dp(36), 13))
            grid.add_widget(self.make_button(f"پژوهش {title}", lambda k=key, c=cost: self.research_upgrade(k, c), GOLD))
        grid.add_widget(self.make_button("بازگشت", self.show_dashboard))
        self.body.add_widget(sc)

    def research_upgrade(self, key, cost):
        if self.total_building_count("university") < 1:
            self.popup("دانشگاه لازم است", "ابتدا در یکی از شهرها دانشگاه بساز.")
            return
        level = self.state.setdefault("research", {}).get(key, 0)
        iron_cost = 10 + level * 5
        if self.state["gold"] < cost or self.state["iron"] < iron_cost:
            self.popup("منابع ناکافی", f"برای پژوهش به {cost} طلا و {iron_cost} آهن نیاز داری.")
            return
        self.state["gold"] -= cost
        self.state["iron"] -= iron_cost
        self.state["research"][key] = level + 1
        self.add_log(f"پژوهش {key} به سطح {level + 1} رسید.")
        self.save_game(silent=True)
        self.show_research()

    def show_policies(self):
        self.clear_body()
        self.body.add_widget(self.make_label("سیاست‌گذاری اقتصادی", dp(42), 18))
        self.body.add_widget(self.make_label(f"سیاست فعلی: {self.state.get('policy', 'متعادل')} | ثبات: {self.state.get('stability', 75)}٪", dp(38), 13))
        sc, grid = self.make_scroll()
        options = [
            ("متعادل", "درآمد و رضایت در وضعیت معمول"),
            ("توسعه‌گرا", "درآمد بازار بیشتر؛ رضایت اندکی کمتر"),
            ("رفاه‌محور", "مالیات کمتر؛ رضایت مردم بیشتر"),
        ]
        for policy, desc in options:
            grid.add_widget(self.make_label(desc, dp(32), 12))
            grid.add_widget(self.make_button(f"اجرای سیاست {policy}", lambda p=policy: self.set_policy(p), GREEN if policy == "رفاه‌محور" else BLUE))
        grid.add_widget(self.make_button("بازگشت", self.show_dashboard))
        self.body.add_widget(sc)

    def set_policy(self, policy):
        self.state["policy"] = policy
        self.add_log(f"سیاست اقتصادی کشور به {policy} تغییر کرد.")
        self.save_game(silent=True)
        self.show_policies()

    def show_army(self):
        self.clear_body()
        s = self.state
        self.body.add_widget(self.make_label("ارتش و دفاع امپراتوری", dp(42), 18))
        self.body.add_widget(self.make_label(
            f"تعداد سربازان: {s['army']} | سطح ارتش: {s['army_level']} | هزینه روزانه: {s['army'] // 8} طلا",
            dp(44), 13))
        sc, grid = self.make_scroll()
        grid.add_widget(self.make_button("استخدام ۱۰ سرباز (۱۲۰ طلا و ۱۵ آهن)",
                                         self.recruit, GREEN))
        grid.add_widget(self.make_button("آموزش ارتش (۱۸۰ طلا، ۲۵ آهن)",
                                         self.train_army, GOLD))
        grid.add_widget(self.make_button("بازگشت", self.show_dashboard))
        self.body.add_widget(sc)

    def recruit(self):
        costs = {"gold": 120, "iron": 15}
        if not self.can_pay(costs):
            self.popup("منابع ناکافی", "برای استخدام سربازان ۱۲۰ طلا و ۱۵ آهن لازم است.")
            return
        self.pay(costs)
        self.state["army"] += 10
        self.add_log("۱۰ سرباز تازه استخدام شدند.")
        self.save_game(silent=True)
        self.show_army()

    def train_army(self):
        costs = {"gold": 180, "iron": 25}
        if not self.can_pay(costs):
            self.popup("منابع ناکافی", "برای آموزش ارتش منابع کافی نیست.")
            return
        self.pay(costs)
        self.state["army_level"] += 1
        self.add_log("سطح آموزش ارتش افزایش یافت.")
        self.save_game(silent=True)
        self.show_army()

    def next_day(self):
        s = self.state
        produced = {r: self.total_production(r) for r in ("food", "wood", "stone", "iron")}
        tax = int(s["population"] * s["tax_rate"] / 100 * 0.035)
        market_income = self.total_building_count("market") * 8
        building_cost = self.building_upkeep()
        army_cost = s["army"] // 8
        food_use = max(1, s["population"] // 80)

        research = s.setdefault("research", {"agriculture": 0, "commerce": 0, "industry": 0, "military": 0})
        farm_bonus = 1 + research.get("agriculture", 0) * 0.10
        industry_bonus = 1 + research.get("industry", 0) * 0.10
        produced["food"] = int(produced["food"] * farm_bonus)
        produced["wood"] = int(produced["wood"] * industry_bonus)
        produced["iron"] = int(produced["iron"] * industry_bonus)
        market_income += research.get("commerce", 0) * 3
        if s.get("policy") == "توسعه‌گرا":
            market_income += 5
            s["happiness"] = max(0, s["happiness"] - 1)
        elif s.get("policy") == "رفاه‌محور":
            tax = int(tax * 0.8)
            s["happiness"] = min(100, s["happiness"] + 1)
        s["gold"] += tax + market_income - building_cost - army_cost
        for resource, amount in produced.items():
            s[resource] += amount
        s["food"] -= food_use
        cap = 600 + self.total_building_count("granary") * 500
        s["food"] = min(s["food"], cap)

        if s["food"] < 0:
            s["food"] = 0
            s["happiness"] = max(0, s["happiness"] - 7)
            s["population"] = max(100, s["population"] - random.randint(4, 12))
            self.add_log("کمبود غذا باعث نارضایتی و کاهش جمعیت شد.")
        else:
            if s["happiness"] >= 65 and s["food"] > food_use * 3:
                growth = max(1, s["population"] // 250)
                s["population"] += growth
            if s["happiness"] >= 80:
                s["happiness"] = min(100, s["happiness"] + 1)

        if s["gold"] < 0:
            s["happiness"] = max(0, s["happiness"] - 3)
            s["stability"] = max(0, s.get("stability", 75) - 3)
        else:
            s["stability"] = min(100, s.get("stability", 75) + (1 if s["happiness"] >= 65 else 0))
        s["trade_index"] = max(-20, min(35, s.get("trade_index", 0) + random.randint(-2, 2)))
        if self.total_building_count("hospital"):
            s["stability"] = min(100, s["stability"] + 1)
            self.add_log("کسری بودجه ثبت شد؛ رضایت مردم کاهش یافت.")
        if s["tax_rate"] >= 18:
            s["happiness"] = max(0, s["happiness"] - 2)
        elif s["tax_rate"] <= 8:
            s["happiness"] = min(100, s["happiness"] + 1)

        s["day"] += 1
        if s["day"] > 30:
            s["day"] = 1
            s["year"] += 1
            self.add_log(f"سال {s['year']} آغاز شد.")
        self.add_log(
            f"روز جدید: مالیات +{tax}، بازار +{market_income}، هزینه‌ها -{building_cost + army_cost} طلا."
        )
        self.save_game(silent=True)
        self.show_dashboard()
        self.popup("گزارش پایان روز",
                   f"مالیات: +{tax} طلا\nدرآمد بازار: +{market_income} طلا\n"
                   f"هزینه‌ها: -{building_cost + army_cost} طلا\n"
                   f"تولید غذا: +{produced['food']} | مصرف غذا: -{food_use}")

    def show_log(self):
        self.clear_body()
        self.body.add_widget(self.make_label("دفتر وقایع امپراتوری", dp(42), 18))
        sc, grid = self.make_scroll()
        for item in self.state.get("log", []):
            grid.add_widget(self.make_label("• " + item, dp(42), 12))
        grid.add_widget(self.make_button("بازگشت", self.show_dashboard))
        self.body.add_widget(sc)

    def save_game(self, silent=False):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            path = self.save_path
            temp = path + ".tmp"
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            if os.path.exists(path):
                try:
                    shutil.copy2(path, path + ".bak")
                except OSError:
                    pass
            os.replace(temp, path)
            if not silent:
                self.popup("ذخیره موفق", "پیشرفت امپراتوری ذخیره شد.")
        except Exception as exc:
            if not silent:
                self.popup("خطای ذخیره", str(exc))

    def load_game(self, silent=False):
        candidates = [self.save_path, self.save_path + ".bak"]
        for path in candidates:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("schema") not in (2, 3):
                    continue
                merged = self.new_state()
                merged.update(data)
                merged["schema"] = 3
                merged.setdefault("research", {"agriculture": 0, "commerce": 0, "industry": 0, "military": 0})
                merged.setdefault("stability", 75)
                merged.setdefault("trade_index", 0)
                merged.setdefault("policy", "متعادل")
                self.state = merged
                return True
            except Exception:
                continue
        return False

if __name__ == "__main__":
    YuskolEmpire().run()
