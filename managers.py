import os
import json
import glob

THEMES = {
    "Moonlight": {
        "base": "#24273a", "mantle": "#1e2030", "crust": "#181926",
        "text": "#cad3f5", "subtext": "#a5adcb",
        "surface0": "#363a4f", "surface1": "#494d64",
        "blue": "#cad3f5", "red": "#ed8796", "green": "#a6da95",
        "slider": "#cad3f5", "handle": "#cad3f5", "outline": "#494d64",
        "logo": "#cad3f5", "title": "#cad3f5", "shadow": "#000000",
        "switch_bg": "#cad3f5"
    },
    "Obsidian": {
        "base": "#000000", "mantle": "#0a0a0a", "crust": "#000000",
        "text": "#ffffff", "subtext": "#a1a1aa",
        "surface0": "#18181b", "surface1": "#27272a",
        "blue": "#ffffff", "red": "#ef4444", "green": "#22c55e",
        "slider": "#3f3f46", "handle": "#ffffff", "outline": "#27272a",
        "logo": "#ffffff", "title": "#ffffff", "shadow": "#000000",
        "switch_bg": "#ffffff"
    },
    "Crimson": {
        "base": "#0f0505", "mantle": "#1f0a0a", "crust": "#000000",
        "text": "#ffe5e5", "subtext": "#ff8080",
        "surface0": "#381212", "surface1": "#4f1919",
        "blue": "#ff3333", "red": "#ff3333", "green": "#10b981",
        "slider": "#dc2626", "handle": "#ffffff", "outline": "#4f1919",
        "logo": "#ff3333", "title": "#ffcccc", "shadow": "#1a0000",
        "switch_bg": "#ff3333"
    },
    "Dracula": {
        "base": "#282a36", "mantle": "#21222c", "crust": "#191a21",
        "text": "#f8f8f2", "subtext": "#bd93f9",
        "surface0": "#44475a", "surface1": "#6272a4",
        "blue": "#bd93f9", "red": "#ff5555", "green": "#50fa7b",
        "slider": "#bd93f9", "handle": "#f8f8f2", "outline": "#44475a",
        "logo": "#bd93f9", "title": "#f8f8f2", "shadow": "#000000",
        "switch_bg": "#bd93f9"
    },
    "Viper": {
        "base": "#051109", "mantle": "#081c10", "crust": "#000000",
        "text": "#e2e8f0", "subtext": "#4ade80",
        "surface0": "#0f2e1b", "surface1": "#14532d",
        "blue": "#22c55e", "red": "#ef4444", "green": "#22c55e",
        "slider": "#15803d", "handle": "#86efac", "outline": "#14532d",
        "logo": "#4ade80", "title": "#86efac", "shadow": "#001a05",
        "switch_bg": "#22c55e"
    },
    "Nord": {
        "base": "#2e3440", "mantle": "#242933", "crust": "#1c2128",
        "text": "#d8dee9", "subtext": "#88c0d0",
        "surface0": "#3b4252", "surface1": "#434c5e",
        "blue": "#88c0d0", "red": "#bf616a", "green": "#a3be8c",
        "slider": "#5e81ac", "handle": "#eceff4", "outline": "#434c5e",
        "logo": "#88c0d0", "title": "#eceff4", "shadow": "#000000",
        "switch_bg": "#88c0d0"
    },
    "Sakura": {
        "base": "#232136", "mantle": "#191724", "crust": "#1f1d2e",
        "text": "#e0def4", "subtext": "#eb6f92",
        "surface0": "#2a273f", "surface1": "#393552",
        "blue": "#eb6f92", "red": "#eb6f92", "green": "#9ccfd8",
        "slider": "#907aa9", "handle": "#e0def4", "outline": "#443c53",
        "logo": "#ea9a97", "title": "#e0def4", "shadow": "#1a0b10",
        "switch_bg": "#eb6f92"
    },
    "Solaris": {
        "base": "#0c0a00", "mantle": "#141100", "crust": "#000000",
        "text": "#fffce6", "subtext": "#facc15",
        "surface0": "#262203", "surface1": "#3f3908",
        "blue": "#facc15", "red": "#f43f5e", "green": "#10b981",
        "slider": "#ca8a04", "handle": "#fef08a", "outline": "#422006",
        "logo": "#facc15", "title": "#fef08a", "shadow": "#1a1600",
        "switch_bg": "#facc15"
    },
    "Catppuccin": {
        "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
        "text": "#cdd6f4", "subtext": "#bac2de",
        "surface0": "#313244", "surface1": "#45475a",
        "blue": "#89b4fa", "red": "#f38ba8", "green": "#a6e3a1",
        "slider": "#b4befe", "handle": "#cdd6f4", "outline": "#45475a",
        "logo": "#f5c2e7", "title": "#cdd6f4", "shadow": "#000000",
        "switch_bg": "#89b4fa"
    }
}

class PresetManager:
    def __init__(self, config_dir, default_config=None):
        self.preset_dir = os.path.join(config_dir, "presets")
        if not os.path.exists(self.preset_dir):
            os.makedirs(self.preset_dir, exist_ok=True)

        self.active_theme_name = "Moonlight"
        self.current_theme_data = THEMES["Moonlight"].copy()
        self.custom_overrides = {}
        self.default_config_ref = default_config

        if default_config:
            def_path = os.path.join(self.preset_dir, "Default.json")
            if not os.path.exists(def_path):
                self.reset_preset("Default")

    def get_presets(self):
        files = glob.glob(os.path.join(self.preset_dir, "*.json"))
        return sorted([os.path.basename(f).replace(".json", "") for f in files])

    def save_preset(self, name, config_data, check_exists=False):
        if not name or name.strip() == "": return "empty"

        clean_name = "".join(x for x in name if x.isalnum() or x in " -_")
        path = os.path.join(self.preset_dir, f"{clean_name}.json")

        if check_exists and os.path.exists(path):
            return "duplicate"

        save_data = config_data.copy()
        save_data['_theme_config'] = {
            'base': self.active_theme_name,
            'overrides': self.custom_overrides
        }

        try:
            with open(path, 'w') as f:
                json.dump(save_data, f, indent=4)
            return "success"
        except:
            return "error"

    def reset_preset(self, name):
        if not self.default_config_ref: return False

        cfg = self.default_config_ref.copy()
        cfg['_theme_config'] = {
            'base': "Moonlight",
            'overrides': {}
        }
        path = os.path.join(self.preset_dir, f"{name}.json")
        try:
            with open(path, 'w') as f:
                json.dump(cfg, f, indent=4)
            return True
        except:
            return False

    def check_modification(self, name, current_cfg):
        path = os.path.join(self.preset_dir, f"{name}.json")
        if not os.path.exists(path): return True

        try:
            with open(path, 'r') as f:
                saved = json.load(f)

            for key, val in current_cfg.items():
                if key in saved and saved[key] != val:
                    return True

            saved_theme = saved.get('_theme_config', {})
            saved_base = saved_theme.get('base', "Moonlight")
            saved_overrides = saved_theme.get('overrides', {})

            if self.active_theme_name != saved_base: return True
            if self.custom_overrides != saved_overrides: return True

            return False
        except:
            return True

    def is_default_modified(self, current_cfg):
        if not self.default_config_ref: return False

        for key, val in self.default_config_ref.items():
            if key in current_cfg and current_cfg[key] != val:
                return True

        if self.active_theme_name != "Moonlight": return True
        if self.custom_overrides: return True

        return False

    def load_preset(self, name):
        path = os.path.join(self.preset_dir, f"{name}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)

                if '_theme_config' in data:
                    t_cfg = data['_theme_config']
                    saved_base = t_cfg.get('base', "Moonlight")
                    if saved_base not in THEMES:
                        saved_base = "Moonlight"

                    self.set_base_theme(saved_base)
                    self.custom_overrides = t_cfg.get('overrides', {})

                return data
            except:
                pass
        return None

    def delete_preset(self, name):
        if name == "Default": return
        path = os.path.join(self.preset_dir, f"{name}.json")
        if os.path.exists(path):
            try: os.remove(path)
            except: pass

    def set_base_theme(self, name):
        if name in THEMES:
            self.active_theme_name = name
            self.current_theme_data = THEMES[name].copy()
            self.custom_overrides.clear()
            return self.get_active_theme()
        return None

    def update_custom_color(self, key, hex_val):
        self.custom_overrides[key] = hex_val
        return self.get_active_theme()

    def get_active_theme(self):
        theme = self.current_theme_data.copy()
        theme.update(self.custom_overrides)
        return theme
