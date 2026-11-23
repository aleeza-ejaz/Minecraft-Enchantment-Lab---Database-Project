"""
Minecraft Enchantment Lab
Tkinter + SQLite. 

The database file (enchantment_lab.db) lives in the same folder as this script.
On first launch, or if the file is missing, the app creates it automatically and
fills the enchantments table. Saved builds are written to the same file, so they
are still there the next time you open the app.

Tab 1 "Lab":     build name, tool, rarity -> enchantment dropdown -> table -> summary
Tab 2 "Archive": scrollable grid of enchantment cards (from the `enchantments` table)

Tables used:
    enchantments       -> read: dropdowns, table, Archive cards
    trial_items        -> write: one row per saved build
                          name = build name, base = tool,
                          category = rarity   (ASSUMPTION - change in save_build/load_build)
    item_enchantments  -> write: the build's enchantments + levels
"""

import sqlite3
import tkinter as tk
from collections import namedtuple
from pathlib import Path
from tkinter import messagebox, ttk
import math
import sqlite3 

DB_PATH = Path(__file__).resolve().with_name("enchantment_lab.db")

ALL_ITEMS = "all durable items"

# compat = the `compatibility` column split on ';'
Ench = namedtuple("Ench", "id name type compat weight obtainable max_level edition desc treasure curse")


# --------------------------------------------------------------------------
# Database (SQLite)
# --------------------------------------------------------------------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS enchantments (
  enchantment_id INTEGER PRIMARY KEY, name VARCHAR(50) NOT NULL, type VARCHAR(20),
  compatibility VARCHAR(100), weight INTEGER, obtainable BOOLEAN, max_lvl INTEGER,
  game_edition VARCHAR(20), description TEXT, treasure BOOLEAN, curse BOOLEAN);

CREATE TABLE IF NOT EXISTS trial_items (
  item_id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(60) NOT NULL, base VARCHAR(30),
  category VARCHAR(30), date_created DATE, date_modified DATE);

CREATE TABLE IF NOT EXISTS item_enchantments (
  item_enchantment_id INTEGER PRIMARY KEY AUTOINCREMENT, enchantment_level INTEGER,
  item_id INTEGER, enchantment_id INTEGER,
  FOREIGN KEY (item_id) REFERENCES trial_items(item_id) ON DELETE CASCADE,
  FOREIGN KEY (enchantment_id) REFERENCES enchantments(enchantment_id));
"""

# Starting data for the enchantments table (used only when the table is empty)
SEED_SQL = """
INSERT INTO enchantments VALUES (1,'Protection','Armor','helmet;chestplate;leggings;boots',10,1,4,'Both','Reduces most damage.',0,0);
INSERT INTO enchantments VALUES (2,'Fire Protection','Armor','helmet;chestplate;leggings;boots',5,1,4,'Both','Reduces fire damage and burning time.',0,0);
INSERT INTO enchantments VALUES (3,'Feather Falling','Armor','boots',5,1,4,'Both','Reduces fall damage.',0,0);
INSERT INTO enchantments VALUES (4,'Blast Protection','Armor','helmet;chestplate;leggings;boots',2,1,4,'Both','Reduces explosion damage and knockback.',0,0);
INSERT INTO enchantments VALUES (5,'Projectile Protection','Armor','helmet;chestplate;leggings;boots',5,1,4,'Both','Reduces projectile damage.',0,0);
INSERT INTO enchantments VALUES (6,'Thorns','Armor','helmet;chestplate;leggings;boots',1,1,3,'Both','Reflects damage back to attackers.',0,0);
INSERT INTO enchantments VALUES (7,'Respiration','Armor','helmet',2,1,3,'Both','Extends underwater breathing time.',0,0);
INSERT INTO enchantments VALUES (8,'Aqua Affinity','Armor','helmet',2,1,1,'Both','Removes the underwater mining penalty.',0,0);
INSERT INTO enchantments VALUES (9,'Depth Strider','Armor','boots',2,1,3,'Both','Increases movement speed underwater.',0,0);
INSERT INTO enchantments VALUES (10,'Frost Walker','Armor','boots',2,0,2,'Both','Freezes water into ice underfoot.',1,0);
INSERT INTO enchantments VALUES (11,'Soul Speed','Armor','boots',1,0,3,'Both','Faster movement on soul sand and soul soil.',1,0);
INSERT INTO enchantments VALUES (12,'Swift Sneak','Armor','leggings',1,0,3,'Both','Faster movement while sneaking.',1,0);
INSERT INTO enchantments VALUES (13,'Curse of Binding','Armor','helmet;chestplate;leggings;boots',1,0,1,'Both','Item cannot be removed once equipped.',1,1);
INSERT INTO enchantments VALUES (14,'Sharpness','Weapon','sword;axe;spear',10,1,5,'Both','Increases melee damage.',0,0);
INSERT INTO enchantments VALUES (15,'Smite','Weapon','sword;axe;spear',5,1,5,'Both','Extra damage to undead mobs.',0,0);
INSERT INTO enchantments VALUES (16,'Bane of Arthropods','Weapon','sword;axe;spear',5,1,5,'Both','Extra damage to arthropods and slows them.',0,0);
INSERT INTO enchantments VALUES (17,'Knockback','Weapon','sword;spear',5,1,2,'Both','Pushes targets back.',0,0);
INSERT INTO enchantments VALUES (18,'Fire Aspect','Weapon','sword;spear',2,1,2,'Both','Sets targets on fire.',0,0);
INSERT INTO enchantments VALUES (19,'Looting','Weapon','sword;spear',2,1,3,'Both','Increases mob loot drops.',0,0);
INSERT INTO enchantments VALUES (20,'Sweeping Edge','Weapon','sword',2,1,3,'Java','Increases sweep attack damage.',0,0);
INSERT INTO enchantments VALUES (21,'Density','Weapon','mace',5,1,5,'Both','Extra smash damage per block fallen.',0,0);
INSERT INTO enchantments VALUES (22,'Breach','Weapon','mace',2,1,4,'Both','Reduces the effectiveness of target armor.',0,0);
INSERT INTO enchantments VALUES (23,'Wind Burst','Weapon','mace',2,0,3,'Both','Launches the wielder upward after a smash attack.',1,0);
INSERT INTO enchantments VALUES (24,'Power','Bow','bow',10,1,5,'Both','Increases arrow damage.',0,0);
INSERT INTO enchantments VALUES (25,'Punch','Bow','bow',2,1,2,'Both','Increases arrow knockback.',0,0);
INSERT INTO enchantments VALUES (26,'Flame','Bow','bow',2,1,1,'Both','Arrows set targets on fire.',0,0);
INSERT INTO enchantments VALUES (27,'Infinity','Bow','bow',1,1,1,'Both','Shoots without consuming arrows.',0,0);
INSERT INTO enchantments VALUES (28,'Multishot','Crossbow','crossbow',2,1,1,'Both','Fires three arrows at once.',0,0);
INSERT INTO enchantments VALUES (29,'Piercing','Crossbow','crossbow',10,1,4,'Both','Arrows pass through multiple entities.',0,0);
INSERT INTO enchantments VALUES (30,'Quick Charge','Crossbow','crossbow',5,1,3,'Both','Reduces reload time.',0,0);
INSERT INTO enchantments VALUES (31,'Loyalty','Trident','trident',5,1,3,'Both','Trident returns after being thrown.',0,0);
INSERT INTO enchantments VALUES (32,'Impaling','Trident','trident',2,1,5,'Both','Extra damage to aquatic mobs (Bedrock: all wet mobs).',0,0);
INSERT INTO enchantments VALUES (33,'Riptide','Trident','trident',2,1,3,'Both','Launches the player through water or rain.',0,0);
INSERT INTO enchantments VALUES (34,'Channeling','Trident','trident',1,1,1,'Both','Summons lightning during thunderstorms.',0,0);
INSERT INTO enchantments VALUES (35,'Efficiency','Tool','pickaxe;shovel;axe;hoe',10,1,5,'Both','Increases mining speed.',0,0);
INSERT INTO enchantments VALUES (36,'Silk Touch','Tool','pickaxe;shovel;axe;hoe',1,1,1,'Both','Blocks drop themselves.',0,0);
INSERT INTO enchantments VALUES (37,'Fortune','Tool','pickaxe;shovel;axe;hoe',2,1,3,'Both','Increases block drops.',0,0);
INSERT INTO enchantments VALUES (38,'Luck of the Sea','Fishing','fishing rod',2,1,3,'Both','Improves fishing loot.',0,0);
INSERT INTO enchantments VALUES (39,'Lure','Fishing','fishing rod',2,1,3,'Both','Fish bite faster.',0,0);
INSERT INTO enchantments VALUES (40,'Unbreaking','Universal','all durable items',5,1,3,'Both','Chance to avoid durability loss.',0,0);
INSERT INTO enchantments VALUES (41,'Mending','Universal','all durable items',2,0,1,'Both','Repairs the item using XP.',1,0);
INSERT INTO enchantments VALUES (42,'Curse of Vanishing','Universal','all durable items',1,0,1,'Both','Item disappears on death.',1,1);
INSERT INTO enchantments VALUES (43,'Lunge','Weapon','spear',5,1,3,'Both','Spear jabs launch the wielder forward in a burst of speed, using up hunger and saturation.',0,0);
"""


def init_db(conn):
    """Create any missing tables and, if the enchantments table is empty, fill it."""
    conn.executescript(SCHEMA_SQL)
    if conn.execute("SELECT COUNT(*) FROM enchantments").fetchone()[0] == 0:
        conn.executescript(SEED_SQL)
    conn.commit()


def db_connect():
    """Open (creating if needed) the database file next to this script."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


def _query(conn, sql, params=()):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def db_load_enchants(conn):
    rows = _query(conn, "SELECT enchantment_id, name, type, compatibility, weight, obtainable, max_lvl,"
                        " game_edition, description, treasure, curse FROM enchantments ORDER BY enchantment_id")
    return [Ench(r["enchantment_id"], r["name"], r["type"] or "",
                 tuple(c.strip().lower() for c in (r["compatibility"] or "").split(";") if c.strip()),
                 r["weight"], bool(r["obtainable"]), r["max_lvl"] or 1, r["game_edition"] or "",
                 r["description"] or "", bool(r["treasure"]), bool(r["curse"])) for r in rows]


def db_list_builds(conn):
    return _query(conn, "SELECT item_id, name, base, category FROM trial_items"
                        " ORDER BY date_modified DESC, name")


def db_build_exists(conn, name):
    return bool(_query(conn, "SELECT item_id FROM trial_items WHERE name = ?", (name,)))


def db_load_build(conn, item_id):
    rows = _query(conn, "SELECT enchantment_id, enchantment_level FROM item_enchantments WHERE item_id = ?",
                  (item_id,))
    return {r["enchantment_id"]: r["enchantment_level"] for r in rows}


def db_save_build(conn, name, base, category, levels):
    """levels = {enchantment_id: level}. Overwrites an existing build with the same name."""
    try:
        row = conn.execute("SELECT item_id FROM trial_items WHERE name = ?", (name,)).fetchone()
        if row:
            item_id = row["item_id"]
            conn.execute("UPDATE trial_items SET base = ?, category = ?, date_modified = date('now', 'localtime')"
                         " WHERE item_id = ?", (base, category, item_id))
            conn.execute("DELETE FROM item_enchantments WHERE item_id = ?", (item_id,))
        else:
            item_id = conn.execute(
                "INSERT INTO trial_items (name, base, category, date_created, date_modified)"
                " VALUES (?, ?, ?, date('now', 'localtime'), date('now', 'localtime'))",
                (name, base, category)).lastrowid
        conn.executemany("INSERT INTO item_enchantments (enchantment_level, item_id, enchantment_id)"
                         " VALUES (?, ?, ?)", [(lvl, item_id, eid) for eid, lvl in levels.items()])
        conn.commit()
        return item_id
    except Exception:
        conn.rollback()
        raise

def db_check(conn):
    """Look through the database and return a list of problems.
    empty list is a fine database."""
    problems = []
    existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    EXPECTED_COLUMNS = {
         "enchantments": {"enchantment_id", "name", "type", "compatibility", "weight", "obtainable",
                     "max_lvl", "game_edition", "description", "treasure", "curse"},
         "trial_items": {"item_id", "name", "base", "category", "date_created", "date_modified"},
         "item_enchantments": {"item_enchantment_id", "enchantment_level", "item_id", "enchantment_id"},
    }
    
    for table, columns in EXPECTED_COLUMNS.items():
        if table not in existing:
            problems.append(f"Missing table: {table}")
            problems.append(f"{table} is missing columns: {', '.join(sorted(missing))}")
            continue
        found = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        missing = columns - found
        if missing:
            problems.append(f"Table {table} is missing columns: {', '.join(missing)}")
    if problems:
        return problems

    result = conn.execute("PRAGMA integrity_check").fetchone()[0]

    if result != "ok":
        problems.append(f"Integrity check failed: {result}")

    for r in conn.execute("PRAGMA foreign_key_check").fetchall():
        problems.append(f"Foreign key violation: {r}")

    if conn.execute("SELECT COUNT(*) FROM enchantments").fetchone()[0] == 0:
        problems.append("The enchantments table is empty.")
    for r in conn.execute("SELECT name FROM enchantments WHERE max_lvl IS NULL OR max_lvl < 1"):
        problems.append(f"{r[0]}: max_lvl is missing or below 1")
    for r in conn.execute("SELECT name FROM enchantments WHERE compatibility IS NULL OR TRIM(compatibility) = ''"):
        problems.append(f"{r[0]}: no compatible items listed")
    for r in conn.execute("SELECT name, COUNT(*) FROM enchantments GROUP BY name HAVING COUNT(*) > 1"):
        problems.append(f"Enchantment name used {r[1]} times: {r[0]} (the app looks enchantments up by name)")


    # save builds
    for r in conn.execute("SELECT name, COUNT(*) FROM trial_items GROUP BY name HAVING COUNT(*) > 1"):
        problems.append(f"Build name saved {r[1]} times: {r[0]}")
    for r in conn.execute("SELECT name, category FROM trial_items"):
        if r[1] not in RARITIES:
            problems.append(f'Build "{r[0]}": unknown rarity "{r[1]}"')

    #enchanments inside a saved build
    by_id = {e.id: e for e in db_load_enchants(conn)}
    rows = conn.execute(
        "SELECT ie.item_enchantment_id, ie.enchantment_id, ie.enchantment_level, t.name, t.base"
        " FROM item_enchantments ie LEFT JOIN trial_items t ON t.item_id = ie.item_id"
        )
    for row_id, ench_id, level, build_name, base in rows:
        if build_name is None:
            problems.append(f"item_enchantments row {row_id} belongs to no saved build")
            continue
    e = by_id.get(ench_id)
    if e is None:
        problems.append(f'Build "{build_name}": unknown enchantment id {ench_id}')
    if level is None or not 1 <= level <= e.max_level:
        problems.append(f'Build "{build_name}": {e.name} level {level} (allowed 1-{e.max_level})')
    if base and not applies(e, base):
        problems.append(f'Build "{build_name}": {e.name} doesnt fit a {base}')
    return problems    


# --------------------------------------------------------------------------
# Build math (fill in with formulas later for build summary section)
# --------------------------------------------------------------------------
def applies(e, tool):
    return ALL_ITEMS in e.compat or tool.lower() in e.compat


def effect_text(e, level):
    """Text for the Lab table's last column."""
    return e.desc


def summarize(tool, build):
    """Summary tile values. Fill the None entries in with your formulas.
    build is {enchantment name: level}."""
    return {
        "count": len(build),
        "levels": sum(build.values()),
        "books": None,      # bookshelves required
        "required": None,   # enchanting table level
        "attack": None,     # theorized attack strength
        "dur": None,        # durability
        "mining": None,     # mining speed bonus
        "other": None,      # other effects
    }


def show(v):
    return "\u2014" if v in (None, "") else str(v)


# ==========================================
# GLOBAL THEME CONFIGURATION
# ==========================================

COLORS = {
    "background": "#12131A",
    "surface": "#1C1E29",
    "surface_light": "#282B38",
    "primary": "#A78BFA",
    "primary_hover": "#C4B5FD",
    "secondary": "#38BDF8",
    "text": "#F4F4F5",
    "text_secondary": "#A1A1AA",
    "border": "#373A4A",
}

FONTS = {
    "title": ("Segoe UI", 24, "bold"),
    "heading": ("Segoe UI", 14, "bold"),
    "subheading": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 10),
    "small": ("Segoe UI", 8),
    "button": ("Segoe UI", 10, "bold"),
}

# Rarity colors, tuned to stay readable on the dark background
RARITIES = {"Common": COLORS["text_secondary"], "Uncommon": "#FACC15",
            "Rare": COLORS["secondary"], "Epic": COLORS["primary"]}


def apply_theme(root):
    """Configure every ttk widget style (and the few plain tk widgets) from COLORS / FONTS."""
    c, f = COLORS, FONTS
    style = ttk.Style(root)
    style.theme_use("clam")   # the only built-in theme that honors custom colors on every platform

    root.configure(bg=c["background"])

    # Dropdown list of the Combobox is a plain tk Listbox, so it is themed through the option database
    root.option_add("*TCombobox*Listbox.background", c["surface_light"])
    root.option_add("*TCombobox*Listbox.foreground", c["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", c["primary"])
    root.option_add("*TCombobox*Listbox.selectForeground", c["background"])
    root.option_add("*TCombobox*Listbox.font", f["body"])

    # ---- base defaults for everything
    style.configure(".", background=c["background"], foreground=c["text"], font=f["body"],
                    bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"],
                    troughcolor=c["surface"], focuscolor=c["primary"], insertcolor=c["text"])
    style.map(".", foreground=[("disabled", c["text_secondary"])])

    # ---- frames and labels
    style.configure("TFrame", background=c["background"])
    style.configure("TLabel", background=c["background"], foreground=c["text"], font=f["body"])
    style.configure("Muted.TLabel", foreground=c["text_secondary"], font=f["small"])
    style.configure("Header.TLabel", font=f["subheading"])
    style.configure("Value.TLabel", font=f["subheading"])

    style.configure("TLabelframe", background=c["background"], bordercolor=c["border"],
                    lightcolor=c["border"], darkcolor=c["border"], borderwidth=1, relief="solid")
    style.configure("TLabelframe.Label", background=c["background"], foreground=c["primary"],
                    font=f["subheading"])

    # ---- sidebar
    style.configure("Sidebar.TFrame", background=c["surface"], relief="solid", borderwidth=1,
                    bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"])
    style.configure("SideTitle.TLabel", background=c["surface"], foreground=c["primary"], font=f["title"])
    style.configure("SideHead.TLabel", background=c["surface"], foreground=c["secondary"], font=f["subheading"])
    style.configure("SideBody.TLabel", background=c["surface"], foreground=c["text_secondary"], font=f["body"])

    # ---- cards (Archive tab)
    style.configure("Card.TFrame", background=c["surface"], relief="solid", borderwidth=1,
                    bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"])
    style.configure("Card.TLabel", background=c["surface"], foreground=c["text"], font=f["body"])
    style.configure("CardTitle.TLabel", background=c["surface"], foreground=c["text"], font=f["subheading"])
    style.configure("CardMuted.TLabel", background=c["surface"], foreground=c["text_secondary"], font=f["small"])
    style.configure("CardTag.TLabel", background=c["surface"], foreground=c["secondary"], font=f["small"])

    # ---- buttons
    style.configure("TButton", background=c["surface_light"], foreground=c["text"], font=f["button"],
                    padding=(14, 6), borderwidth=1, relief="flat", focusthickness=0)
    style.map("TButton",
              background=[("pressed", c["border"]), ("active", c["border"])],
              bordercolor=[("active", c["primary"])])
    style.configure("Accent.TButton", background=c["primary"], foreground=c["background"],
                    bordercolor=c["primary"], lightcolor=c["primary"], darkcolor=c["primary"])
    style.map("Accent.TButton",
              background=[("pressed", c["primary_hover"]), ("active", c["primary_hover"])],
              bordercolor=[("active", c["primary_hover"])])

    # ---- inputs
    field = dict(fieldbackground=c["surface_light"], background=c["surface_light"], foreground=c["text"],
                 bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"],
                 insertcolor=c["text"], selectbackground=c["primary"], selectforeground=c["background"],
                 padding=6)
    style.configure("TEntry", **field)
    style.configure("TCombobox", arrowcolor=c["primary"], **field)
    style.configure("TSpinbox", arrowcolor=c["primary"], **field)
    for w in ("TEntry", "TCombobox", "TSpinbox"):
        style.map(w,
                  bordercolor=[("focus", c["primary"])],
                  lightcolor=[("focus", c["primary"])],
                  darkcolor=[("focus", c["primary"])])
    # readonly comboboxes/spinboxes otherwise fall back to a white field
    for w in ("TCombobox", "TSpinbox"):
        style.map(w,
                  fieldbackground=[("readonly", c["surface_light"]), ("disabled", c["surface"])],
                  foreground=[("readonly", c["text"])],
                  selectbackground=[("readonly", c["surface_light"])],
                  selectforeground=[("readonly", c["text"])],
                  arrowcolor=[("active", c["primary_hover"])])
        
    # styles tabs to match the rest of the app
    style.map("TNotebook.Tab",
              background=[("selected", c["surface_light"]), ("active", c["surface_light"])],
              foreground=[("selected", c["primary"]), ("active", c["text"])],
              expand=[("selected", (0, 0, 0, 0)), ("!selected", (0, 0, 0, 0))])

    # ---- treeview (build table)
    style.configure("Treeview", background=c["surface"], fieldbackground=c["surface"],
                    foreground=c["text"], font=f["body"], rowheight=30, borderwidth=0)
    style.map("Treeview",
              background=[("selected", c["primary"])],
              foreground=[("selected", c["background"])])
    style.configure("Treeview.Heading", background=c["surface_light"], foreground=c["secondary"],
                    font=f["subheading"], relief="flat", padding=(8, 6))
    style.map("Treeview.Heading", background=[("active", c["border"])])

    # ---- scrollbars (in case any widget gets one later)
    style.configure("Vertical.TScrollbar", background=c["surface_light"], troughcolor=c["surface"],
                    arrowcolor=c["text_secondary"], bordercolor=c["surface"])
    style.map("Vertical.TScrollbar", background=[("active", c["border"])])

    return style


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minecraft Enchantment Lab")
        self.geometry("1120x840")
        self.minsize(1000, 720)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        apply_theme(self)

        problems = db_check(self.conn)
        if problems:
            startup_error = "Database check found problems:\n\n" + "\n".join(problems[:15])

        self.build = {}          # enchantment name -> level
        self.saved_rows = []     # rows from trial_items
        self.conn, self.enchants, startup_error = None, [], None
        try:
            self.conn = db_connect()
            self.enchants = db_load_enchants(self.conn)
        except Exception as exc:  # noqa: BLE001 - show any connection problem to the user
            startup_error = str(exc)
        self.by_name = {e.name: e for e in self.enchants}
        self.by_id = {e.id: e for e in self.enchants}

        # every item type named in `compatibility`, in order of first appearance
        self.tools = []
        for e in self.enchants:
            for c in e.compat:
                if c != ALL_ITEMS and c.title() not in self.tools:
                    self.tools.append(c.title())

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.build_sidebar()

        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.lab_tab = ttk.Frame(self.tabs, padding=14)
        self.archive_tab = ttk.Frame(self.tabs, padding=14)
        self.tabs.add(self.lab_tab, text="Lab")            # initial tab
        self.tabs.add(self.archive_tab, text="Archive")
        self.equalize_tabs()

        self.build_lab_tab()
        self.build_archive_tab()
        self.on_tool_change()
        self.refresh_saved()

        if startup_error:
            self.after(300, lambda: messagebox.showerror("Database connection", startup_error))

    def on_close(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:  # noqa: BLE001
                pass
        self.destroy()

    # ---------------- Sidebar ----------------
    def build_sidebar(self):
        side = ttk.Frame(self, style="Sidebar.TFrame", padding=20)
        side.grid(row=0, column=0, sticky="ns", padx=(8, 0), pady=8)
        ttk.Label(side, text="Enchantment Lab", style="SideTitle.TLabel", wraplength=210,
                  justify="left").pack(anchor="w", pady=(0, 18))
        sections = (
            ("Lab", "Build and test enchanted gear. Pick a tool and rarity, add enchantments and "
                    "levels, review the build summary, and save builds to load later."),
            ("Archive", "Browse every enchantment as a card, with its max level, compatible items, "
                        "weight, and availability."),
        )
        for head, body in sections:
            ttk.Label(side, text=head, style="SideHead.TLabel").pack(anchor="w", pady=(0, 2))
            ttk.Label(side, text=body, style="SideBody.TLabel", wraplength=210,
                      justify="left").pack(anchor="w", pady=(0, 16))

    def equalize_tabs(self):
        """Give both tab buttons the same width by padding each according to its text width."""
        from tkinter import font as tkfont
        fnt = tkfont.Font(font=FONTS["button"])
        texts = {tab: self.tabs.tab(tab, "text") for tab in self.tabs.tabs()}
        widest = max(fnt.measure(t) for t in texts.values())
        for tab, text in texts.items():
            pad_x = 28 + (widest - fnt.measure(text)) // 2
            self.tabs.tab(tab, padding=(pad_x, 8))

    # ---------------- Lab tab ----------------
    def build_lab_tab(self):
        t = self.lab_tab

        # -- Build details
        top = ttk.LabelFrame(t, text="Build", padding=12)
        top.pack(fill="x")
        top.columnconfigure((0, 1, 2), weight=1, uniform="top")
        self.name_var = tk.StringVar()
        self.tool_var = tk.StringVar()
        self.rarity_var = tk.StringVar(value="Common")
        self.name_var.trace_add("write", lambda *a: self.refresh_summary())

        for col, text in enumerate(("Build name", "Tool", "Rarity")):
            ttk.Label(top, text=text, style="Muted.TLabel").grid(
                row=0, column=col, sticky="w", padx=(0 if col == 0 else 8, 0), pady=(0, 2))
        ttk.Entry(top, textvariable=self.name_var).grid(row=1, column=0, sticky="ew")
        tool_cb = ttk.Combobox(top, textvariable=self.tool_var, values=self.tools, state="readonly")
        tool_cb.grid(row=1, column=1, sticky="ew", padx=(8, 0))
        tool_cb.bind("<<ComboboxSelected>>", lambda e: self.on_tool_change())
        rarity_cb = ttk.Combobox(top, textvariable=self.rarity_var, values=list(RARITIES), state="readonly")
        rarity_cb.grid(row=1, column=2, sticky="ew", padx=(8, 0))
        rarity_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_summary())

        ttk.Label(top, text="Saved builds", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 2))
        self.saved_var = tk.StringVar()
        self.saved_cb = ttk.Combobox(top, textvariable=self.saved_var, state="readonly")
        self.saved_cb.grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Button(top, text="Load", command=self.load_build).grid(row=3, column=2, sticky="w", padx=(8, 0))

        # -- Enchantments
        ench = ttk.LabelFrame(t, text="Enchantments", padding=12)
        ench.pack(fill="both", expand=True, pady=(12, 0))
        ench.columnconfigure(0, weight=1)
        ench.rowconfigure(1, weight=1)

        add_row = ttk.Frame(ench)
        add_row.grid(row=0, column=0, columnspan=2, sticky="ew")
        add_row.columnconfigure(0, weight=1)
        self.ench_var = tk.StringVar()
        self.ench_cb = ttk.Combobox(add_row, textvariable=self.ench_var, state="readonly")
        self.ench_cb.grid(row=0, column=0, sticky="ew")
        self.ench_cb.bind("<<ComboboxSelected>>", lambda e: self.on_ench_pick())
        ttk.Label(add_row, text="Level", style="Muted.TLabel").grid(row=0, column=1, padx=(10, 4))
        self.level_var = tk.IntVar(value=1)
        self.level_sp = ttk.Spinbox(add_row, from_=1, to=1, width=4, textvariable=self.level_var, state="readonly")
        self.level_sp.grid(row=0, column=2)
        ttk.Button(add_row, text="Add", style="Accent.TButton", command=self.add_enchant).grid(
            row=0, column=3, padx=(10, 0))

        self.table = ttk.Treeview(ench, columns=("name", "level", "effect"), show="headings", height=6, selectmode="browse")
        for key, label, width, anchor in (("name", "Enchantment", 170, "w"), ("level", "Level", 70, "center"),
                                          ("effect", "Effect", 340, "w")):
            self.table.heading(key, text=label)
            self.table.column(key, width=width, anchor=anchor, stretch=(key == "effect"))
        self.table.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        ttk.Button(ench, text="Remove selected", command=self.remove_enchant).grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Button(ench, text="Save build", style="Accent.TButton", command=self.save_build).grid(
            row=2, column=1, sticky="e", pady=(8, 0))

        # -- Summary
        summ = ttk.LabelFrame(t, text="Build summary", padding=(12, 6, 12, 4))
        summ.pack(fill="x", pady=(12, 0))
        summ.columnconfigure((0, 1, 2, 3), weight=1, uniform="tile")
        self.header_lbl = ttk.Label(summ, style="Header.TLabel")
        self.header_lbl.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 4))

        self.tiles = {}
        layout = [("count", "Enchantments"), ("levels", "Total enchantment levels"),
                  ("books", "Bookshelves required"), ("required", "Enchanting table level"),
                  ("attack", "Theorized attack strength"), ("dur", "Durability")]
        for i, (key, label) in enumerate(layout):
            if key == "other":
                tile = ttk.Frame(summ, padding=(0, 0, 0, 2))
                tile.grid(row=3, column=0, columnspan=4, sticky="ew")
            else:
                row, col = divmod(i, 4)
                tile = ttk.Frame(summ, padding=(0, 0, 0, 4))
                tile.grid(row=row + 1, column=col, sticky="ew")
            ttk.Label(tile, text=label, style="Muted.TLabel").pack(anchor="w")
            lbl = ttk.Label(tile, style="Value.TLabel", justify="left")
            lbl.pack(anchor="w")
            self.tiles[key] = lbl

        

    def on_tool_change(self):
        tool = self.tool_var.get()
        names = [e.name for e in self.enchants if tool and applies(e, tool)]
        dropped = [n for n in self.build if n not in names]
        for n in dropped:
            del self.build[n]
        if dropped:
            messagebox.showinfo("Build updated", f"Removed (not compatible with {tool}): {', '.join(dropped)}")
        self.ench_cb["values"] = names
        self.ench_var.set("")
        self.level_sp.config(to=1)
        self.level_var.set(1)
        self.refresh_table()

    def on_ench_pick(self):
        mx = self.by_name[self.ench_var.get()].max_level
        self.level_sp.config(to=mx)
        self.level_var.set(mx)

    def add_enchant(self):
        name = self.ench_var.get()
        if not name:
            return messagebox.showinfo("Pick an enchantment", "Choose a tool, then an enchantment from the dropdown.")
        self.build[name] = max(1, min(int(self.level_var.get()), self.by_name[name].max_level))
        self.refresh_table()

    def remove_enchant(self):
        sel = self.table.selection()
        if sel:
            self.build.pop(sel[0], None)
            self.refresh_table()

    def refresh_table(self):
        self.table.delete(*self.table.get_children())
        for name, lvl in self.build.items():
            self.table.insert("", "end", iid=name, values=(name, lvl, effect_text(self.by_name[name], lvl)))
        self.refresh_summary()

    def refresh_summary(self):
        tool, rarity = self.tool_var.get(), self.rarity_var.get()
        s = summarize(tool, self.build)
        name = self.name_var.get().strip() or "Unnamed build"
        self.header_lbl.config(text=f"{name}  \u2022  {rarity} {tool}".rstrip(), foreground=RARITIES[rarity])
        for key, lbl in self.tiles.items():
            lbl.config(text=show(s.get(key)))


    # ---------------- Save / load (trial_items + item_enchantments) ----------------
    def refresh_saved(self):
        self.saved_rows = []
        if self.conn is not None:
            try:
                self.saved_rows = db_list_builds(self.conn)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Database error", f"Couldn't read saved builds:\n{exc}")
        self.saved_cb["values"] = [f"{r['name']}  \u2014  {r['base'] or ''}" for r in self.saved_rows]
        self.saved_var.set("")

    def save_build(self):
        if self.conn is None:
            return messagebox.showwarning("No database", "Not connected to the database.")
        name, tool = self.name_var.get().strip(), self.tool_var.get()
        if not name:
            return messagebox.showwarning("Name needed", "Give your build a name.")
        if not tool:
            return messagebox.showwarning("Tool needed", "Choose a tool first.")
        if not self.build:
            return messagebox.showwarning("Empty build", "Add at least one enchantment first.")
        try:
            if db_build_exists(self.conn, name) and not messagebox.askyesno(
                    "Overwrite?", f'A build named "{name}" already exists. Overwrite it?'):
                return
            levels = {self.by_name[n].id: lvl for n, lvl in self.build.items()}
            db_save_build(self.conn, name, tool, self.rarity_var.get(), levels)
        except Exception as exc:  # noqa: BLE001
            return messagebox.showerror("Save failed", str(exc))
        self.refresh_saved()
        messagebox.showinfo("Saved", f'Saved "{name}".')

    def load_build(self):
        idx = self.saved_cb.current()
        if idx < 0:
            return messagebox.showinfo("Pick a build", "Choose a saved build from the dropdown first.")
        row = self.saved_rows[idx]
        if row["base"] not in self.tools:
            return messagebox.showwarning("Can't load", f'Unknown tool "{row["base"]}" for this build.')
        try:
            levels = db_load_build(self.conn, row["item_id"])
        except Exception as exc:  # noqa: BLE001
            return messagebox.showerror("Load failed", str(exc))
        self.build.clear()
        self.tool_var.set(row["base"])
        self.on_tool_change()
        if row["category"] in RARITIES:
            self.rarity_var.set(row["category"])
        self.name_var.set(row["name"])
        self.build = {self.by_id[eid].name: lvl for eid, lvl in levels.items() if eid in self.by_id}
        self.refresh_table()

    # ---------------- Archive tab ----------------
    def build_archive_tab(self):
        t = self.archive_tab
        t.columnconfigure(0, weight=1)
        t.rowconfigure(0, weight=1)

        # No scrollbar: the Archive scrolls with the trackpad / mouse wheel (see on_wheel).
        # yscrollincrement=1 makes one scroll "unit" exactly 1 pixel.
        # tk.Canvas is not a ttk widget, so it needs its background set directly.
        self.canvas = tk.Canvas(t, highlightthickness=0, yscrollincrement=1, bg=COLORS["background"])
        self.canvas.grid(row=0, column=0, sticky="nsew")

        grid = ttk.Frame(self.canvas)
        win = self.canvas.create_window((0, 0), window=grid, anchor="nw")
        grid.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(win, width=e.width))
        self.bind_all("<MouseWheel>", self.on_wheel)                                  # Mac + Windows
        self.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-60, "units"))  # Linux up
        self.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(60, "units"))   # Linux down
        try:  # Newer Tk (8.7 / 9) on Mac sends trackpad swipes as <TouchpadScroll>, not <MouseWheel>
            self.bind_all("<TouchpadScroll>", self.on_touchpad)
        except tk.TclError:
            pass  # older Tk doesn't have this event; <MouseWheel> covers it

        cols = 2
        for c in range(cols):
            grid.columnconfigure(c, weight=1, uniform="card")
        for i, e in enumerate(self.enchants):
            r, c = divmod(i, cols)
            self.make_card(grid, e).grid(row=r, column=c, sticky="nsew", padx=6, pady=6)

    def make_card(self, parent, e):
        card = ttk.Frame(parent, padding=14, style="Card.TFrame")
        ttk.Label(card, text=e.name, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text=f"{e.type}  \u2022  Max level {e.max_level}",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 0))
        items = "All durable items" if ALL_ITEMS in e.compat else ", ".join(c.title() for c in e.compat)
        ttk.Label(card, text=items, style="CardMuted.TLabel", wraplength=320,
                  justify="left").pack(anchor="w", pady=(0, 8))
        ttk.Label(card, text=e.desc, style="Card.TLabel", wraplength=320, justify="left").pack(anchor="w")

        tags = []
        if e.treasure:
            tags.append("Treasure")
        if e.curse:
            tags.append("Curse")
        if not e.obtainable:
            tags.append("Not obtainable")
        if e.edition and e.edition != "Both":
            tags.append(f"{e.edition} only")
        tags.append(f"Weight {e.weight}")
        ttk.Label(card, text="  \u2022  ".join(tags), style="CardTag.TLabel", wraplength=320,
                  justify="left").pack(anchor="w", pady=(8, 0))
        return card

    def on_wheel(self, event):
        if self.tabs.select() != str(self.archive_tab):
            return  # only scroll while the Archive tab is showing
        if self.tk.call("tk", "windowingsystem") == "aqua":
            step = -event.delta * 4              # Mac: small deltas that grow with swipe speed
        else:
            step = -int(event.delta * 2 / 3)     # Windows wheel: 120 per notch (= 80 pixels)
        self.canvas.yview_scroll(step, "units")

    def on_touchpad(self, event):
        if self.tabs.select() != str(self.archive_tab):
            return
        try:
            result = self.tk.call("tk::PreciseScrollDeltas", event.delta)  # (dx, dy) pixels moved
            _, dy = self.tk.splitlist(result)  # Tk may return a string or a pair
        except (tk.TclError, ValueError):
            return
        self.canvas.yview_scroll(-int(dy), "units")


if __name__ == "__main__":
    App().mainloop()
