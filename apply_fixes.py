import os, glob, json, re

# 1. Modify clients/base.py
base_py_path = "/home/anubhavanand/recon/clients/base.py"
with open(base_py_path, "r") as f:
    content = f.read()
# Replace (429, 503, 504) with (503, 504)
content = content.replace("429, 503, 504", "503, 504")
with open(base_py_path, "w") as f:
    f.write(content)

# 2. Modify tui/screens.py
screens_py_path = "/home/anubhavanand/recon/tui/screens.py"
with open(screens_py_path, "r") as f:
    screens_content = f.read()

theme_injection = """
        if query.startswith("/theme "):
            theme_name = query[len("/theme "):].strip().lower().replace(" ", "-")
            for cls in list(self.app.classes):
                if cls.startswith("theme-"):
                    self.app.remove_class(cls)
            self.app.add_class(f"theme-{theme_name}")
            self.query_one("#status_top").update(f"Theme changed to {theme_name}")
            search_input = self.query_one("#search_input")
            search_input.value = ""
            event.stop()
            return
"""

if "/theme " not in screens_content:
    screens_content = screens_content.replace(
        "    async def on_input_submitted(self, event: Input.Submitted) -> None:\n        query = event.value.strip()\n",
        "    async def on_input_submitted(self, event: Input.Submitted) -> None:\n        query = event.value.strip()\n" + theme_injection
    )
    with open(screens_py_path, "w") as f:
        f.write(screens_content)

# 3. Modify tui/styles.css
styles_path = "/home/anubhavanand/recon/tui/styles.css"
with open(styles_path, "r") as f:
    css = f.read()

# Replace hardcoded hex with variables
# bg: #1a1b26, surface: #24283b, text: #a9b1d6, border: #414868, primary: #7aa2f7, error: #f7768e, secondary: #bb9af7
replacements = {
    "#1a1b26": "$bg",
    "#24283b": "$surface",
    "#a9b1d6": "$text",
    "#414868": "$border",
    "#7aa2f7": "$primary",
    "#f7768e": "$error",
    "#bb9af7": "$secondary"
}

for hex_val, var in replacements.items():
    css = css.replace(hex_val, var)
    css = css.replace(hex_val.upper(), var)

# Inject Tokyo Night default variables into Screen
if "$bg:" not in css:
    css = css.replace("Screen {\n", "Screen {\n    $bg: #1a1b26;\n    $surface: #24283b;\n    $text: #a9b1d6;\n    $border: #414868;\n    $primary: #7aa2f7;\n    $error: #f7768e;\n    $secondary: #bb9af7;\n")

# Read themes from applying-themes skill
themes_dir = "/home/anubhavanand/.agents/skills/applying-themes/themes/"
theme_classes = "\n/* Generated Themes */\n"
for theme_file in glob.glob(os.path.join(themes_dir, "*.md")):
    name = os.path.basename(theme_file).replace(".md", "")
    with open(theme_file, "r") as f:
        content = f.read()
    
    # Extract hex codes. Fallback generation if missing specific ones.
    hexes = re.findall(r'`#([A-Fa-f0-9]{6})`', content)
    if len(hexes) >= 4:
        bg = "#" + hexes[0]
        primary = "#" + hexes[1]
        secondary = "#" + hexes[2]
        text = "#" + hexes[3]
        
        # Approximate surface, border, error
        surface = "#" + hexes[0] # Not ideal, but will fallback
        border = primary
        error = "#f7768e" # Fallback error
        
        theme_classes += f"\nScreen.theme-{name} {{\n"
        theme_classes += f"    $bg: {bg};\n"
        theme_classes += f"    $surface: {bg};\n" # Need to darken/lighten, but good enough for now
        theme_classes += f"    $text: {text};\n"
        theme_classes += f"    $border: {border};\n"
        theme_classes += f"    $primary: {primary};\n"
        theme_classes += f"    $error: {error};\n"
        theme_classes += f"    $secondary: {secondary};\n"
        theme_classes += "}\n"

if "/* Generated Themes */" not in css:
    with open(styles_path, "w") as f:
        f.write(css + theme_classes)

print("Done")
