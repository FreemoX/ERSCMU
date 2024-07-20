# Define version number
PROGRAM_VERSION = "1.7.0.6"
LAUNCHER_VERSION = "1.1.0.0"

# Define a persistent path for the configuration files in the AppData folder
PERSISTENT_DIR = os.path.join(os.getenv('APPDATA'), 'ERSC Mod Updater')
if not os.path.exists(PERSISTENT_DIR):
    os.makedirs(PERSISTENT_DIR)

LOGO_PATH = os.path.join(PERSISTENT_DIR, 'logo.ico')
CONFIG_FILE = os.path.join(PERSISTENT_DIR, 'mod_updater_config.json')
DEFAULT_MOD_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game\SeamlessCoop"
GITHUB_API_URL = 'https://api.github.com/repos/LukeYui/EldenRingSeamlessCoopRelease/releases/latest'
BATCH_FILE = os.path.join(PERSISTENT_DIR, 'launch_mod.bat')
INI_FILE = 'ersc_settings.ini'
DEFAULT_VALUES = {
    'GAMEPLAY': {
        'allow_invaders': '1',
        'death_debuffs': '1',
        'allow_summons': '1',
        'overhead_player_display': '0'
    },
    'SCALING': {
        'enemy_health_scaling': '35',
        'enemy_damage_scaling': '0',
        'enemy_posture_scaling': '15',
        'boss_health_scaling': '100',
        'boss_damage_scaling': '0',
        'boss_posture_scaling': '20'
    },
    'SAVE': {
        'save_file_extension': 'co2'
    },
    'LANGUAGE': {
        'mod_language_override': ''
    }
}
FIRST_RUN = 1

def check_logo():
    LOGO_URL = 'https://raw.githubusercontent.com/FreemoX/ERSCMU/main/assets/logo.ico'
    if not os.path.isfile(LOGO_PATH):
        response = requests.get(LOGO_URL, stream=True)
        if response.status_code == 200:
            # Open the local file in write-binary mode
            with open(LOGO_PATH, 'wb') as file:
                # Write the content in chunks to the local file
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"Logo downloaded successfully to {LOGO_PATH}")
        else:
            print(f"Failed to download logo.\nHTTP status code: {response.status_code}")
    else:
        print(f"Logo discovered locally at {LOGO_PATH}")

def get_changelog(num_entries=1):
    url = 'https://raw.githubusercontent.com/FreemoX/ERSCMU/main/assets/changelog.md'
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch changelog. HTTP status code: {response.status_code}")

    changelog = response.text.split('\n- ')
    latest_entries = changelog[:num_entries]
    
    formatted_entries = []
    for entry in latest_entries:
        if entry.strip():
            lines = entry.split('\n')
            version = lines[0].strip()
            changes = '\n'.join([f"- {line.strip()}" for line in lines[1:] if line.strip()])
            formatted_entries.append(f"version {version}:\n{changes}")
    
    return '\n\n'.join(formatted_entries)

def ensure_vocabulary(config):
    if "vocabulary" not in config:
        config["vocabulary"] = {
            "GAMEPLAY": {
                "allow_invaders": {"0": "Off", "1": "On"},
                "death_debuffs": {"0": "Off", "1": "On"},
                "allow_summons": {"0": "Off", "1": "On"},
                "overhead_player_display": {
                    "0": "Normal",
                    "1": "None",
                    "2": "Display player ping",
                    "3": "Display player soul level",
                    "4": "Display player death count",
                    "5": "Display player ping & level"
                }
            },
            "SCALING": {},
            "SAVE": {},
            "PASSWORD": {},
            "LANGUAGE": {}
        }
    return config

def ensure_settings(config):
    if "settings" not in config:
        config["settings"] = {
            "GAMEPLAY": {},
            "SCALING": {},
            "SAVE": {},
            "LANGUAGE": {}
        }
    return config

def camelcase(text):
    return ' '.join([word.capitalize() for word in text.split('_')])

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "installed_version": "N/A",
            "mod_path": DEFAULT_MOD_PATH,
            "launcher_name": "ersc_launcher.exe",
            "last_updated": "N/A"
        }
    config = ensure_vocabulary(config)
    config = ensure_settings(config)
    return config

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def get_latest_release_info():
    response = requests.get(GITHUB_API_URL)
    response.raise_for_status()
    return response.json()

def get_installed_version(mod_path):
    version_file = os.path.join(mod_path, 'version.txt')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            return f.read().strip()
    return ""

def download_latest_release(download_url, dest_path):
    response = requests.get(download_url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def backup_old_mod(mod_path, installed_version, config):
    backup_dir = PERSISTENT_DIR
    backup_path = os.path.join(backup_dir, f"ER-SC-{installed_version}.zip")
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(mod_path):
            for file in files:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file), mod_path))
        launcher_path = os.path.join(os.path.dirname(mod_path), config.get('launcher_name', 'ersc_launcher.exe'))
        if os.path.exists(launcher_path):
            zipf.write(launcher_path, os.path.basename(launcher_path))

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def find_launcher(mod_path):
    for root, _, files in os.walk(os.path.dirname(mod_path)):
        for file in files:
            if file.endswith('.exe') and file != 'eldenring.exe' and file != 'start_protected_game.exe':
                return file
    return None

def merge_ini_files(old_ini, new_ini):
    old_config = configparser.ConfigParser()
    old_config.read(old_ini)
    new_config = configparser.ConfigParser()
    new_config.read(new_ini)

    for section in old_config.sections():
        if not new_config.has_section(section):
            new_config.add_section(section)
        for key, value in old_config.items(section):
            new_config.set(section, key, value)

    with open(new_ini, 'w') as configfile:
        new_config.write(configfile)

    return new_config

def check_ini_files(mod_path):
    old_ini = os.path.join(mod_path, INI_FILE)
    new_ini = os.path.join(mod_path, INI_FILE)
    if os.path.exists(old_ini) and os.path.exists(new_ini):
        merged_config = merge_ini_files(old_ini, new_ini)
        with open(new_ini, 'w') as configfile:
            merged_config.write(configfile)
    elif os.path.exists(old_ini) and not os.path.exists(new_ini):
        shutil.copy(old_ini, new_ini)

def update_mod(latest_version, download_url, release_info):
    config = load_config()
    mod_path = config["mod_path"]
    installed_version = get_installed_version(mod_path)

    try:
        zip_path = os.path.join(PERSISTENT_DIR, 'SeamlessCoop.zip')
        download_latest_release(download_url, zip_path)

        if installed_version:
            backup_old_mod(mod_path, installed_version, config)
            shutil.rmtree(mod_path)
            old_launcher = config.get('launcher_name', 'ersc_launcher.exe')
            old_launcher_path = os.path.join(os.path.dirname(mod_path), old_launcher)
            if os.path.exists(old_launcher_path):
                os.remove(old_launcher_path)

        extract_zip(zip_path, os.path.dirname(mod_path))
        os.remove(zip_path)

        new_launcher = find_launcher(mod_path)
        if new_launcher:
            config['launcher_name'] = new_launcher

        with open(os.path.join(mod_path, 'version.txt'), 'w') as f:
            f.write(latest_version)

        config['installed_version'] = latest_version
        config['last_updated'] = datetime.strptime(release_info['published_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
        save_config(config)

        check_ini_files(mod_path)
        apply_saved_settings_to_ini(mod_path)
        create_batch_script()
        update_info_text()
        QMessageBox.information(None, "Update Complete", f"Updated to version {latest_version}.")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Update failed: {e}")

def check_for_updates():
    global FIRST_RUN
    config = load_config()
    mod_path = config["mod_path"]
    installed_version = get_installed_version(mod_path)
    
    try:
        release_info = get_latest_release_info()
        latest_version = release_info['tag_name']
        download_url = next(asset['browser_download_url'] for asset in release_info['assets'] if asset['name'].endswith('.zip'))
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to fetch update info: {e}")
        return

    if installed_version != latest_version:
        response = QMessageBox.question(None, "Update Available", f"A new version ({latest_version}) is available. Do you want to update?", QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            update_mod(latest_version, download_url, release_info)
    elif FIRST_RUN == 0:
        response = QMessageBox.question(None, "No Updates", "No new updates available. Do you want to force update?", QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            update_mod(latest_version, download_url, release_info)

def launch_mod():
    config = load_config()
    ini_path = os.path.join(config["mod_path"], INI_FILE)
    password = read_password_from_ini(ini_path)
    if not password:
        QMessageBox.critical(None, "Error", "Session password cannot be empty.")
        return
    os.startfile(BATCH_FILE)

def browse_folder():
    folder_selected = QFileDialog.getExistingDirectory()
    if folder_selected:
        config = load_config()
        if os.path.basename(folder_selected) == "SeamlessCoop":
            config["mod_path"] = folder_selected
            save_config(config)
            mod_path_entry.setText(folder_selected)
            create_batch_script()
            update_info_text()
        else:
            QMessageBox.critical(None, "Error", "Please select the SeamlessCoop folder.")

def update_info_text():
    config = load_config()
    installed_version = config.get('installed_version', 'Unknown')
    last_updated = config.get('last_updated', 'Unknown')
    info_text.setText(f"Current Version: {installed_version}\nLast Updated: {last_updated}")

def create_batch_script():
    config = load_config()
    launcher_path = os.path.join(os.path.dirname(config["mod_path"]), config['launcher_name'])
    with open(BATCH_FILE, 'w') as f:
        f.write(f'@echo off\ncd /d "{os.path.dirname(launcher_path)}"\nstart {config["launcher_name"]}\n')

def read_password_from_ini(ini_path):
    if os.path.exists(ini_path):
        config_parser = configparser.ConfigParser()
        config_parser.read(ini_path)
        if config_parser.has_option('PASSWORD', 'cooppassword'):
            return config_parser.get('PASSWORD', 'cooppassword')
    return ""

def save_password_to_ini(password, ini_path):
    if os.path.exists(ini_path):
        config_parser = configparser.ConfigParser()
        config_parser.read(ini_path)
        if not config_parser.has_section('PASSWORD'):
            config_parser.add_section('PASSWORD')
        config_parser.set('PASSWORD', 'cooppassword', password)
        with open(ini_path, 'w') as configfile:
            config_parser.write(configfile)

def save_password():
    new_password = password_entry.text()
    if not new_password:
        QMessageBox.critical(None, "Error", "Session password cannot be empty.")
        return
    config = load_config()
    ini_path = os.path.join(config["mod_path"], INI_FILE)
    save_password_to_ini(new_password, ini_path)

def toggle_password():
    if password_entry.echoMode() == QLineEdit.Normal:
        password_entry.setEchoMode(QLineEdit.Password)
        toggle_button.setText('Show')
    else:
        password_entry.setEchoMode(QLineEdit.Normal)
        toggle_button.setText('Hide')

def get_locale_options(mod_path):
    locale_path = os.path.join(mod_path, 'locale')
    if not os.path.exists(locale_path):
        return ["Default"]
    return ["Default"] + [os.path.splitext(f)[0].capitalize() for f in os.listdir(locale_path) if f.endswith('.json')]

def auto_discover_mod_path():
    QMessageBox.information(None, "Auto-Discovery", "Auto-discovery might take a few minutes. Please wait...")

    drives = [f"{chr(letter)}:\\" for letter in range(65, 91) if os.path.exists(f"{chr(letter)}:\\")]
    potential_paths = []

    # First, check Program Files directories
    program_files_dirs = []
    for drive in drives:
        program_files_dirs.extend([
            os.path.join(drive, 'Program Files', 'Steam'),
            os.path.join(drive, 'Program Files (x86)', 'Steam')
        ])

    for dir in program_files_dirs:
        if os.path.exists(dir):
            for root, dirs, files in os.walk(dir):
                if 'steamapps' in dirs:
                    steamapps_path = os.path.join(root, 'steamapps')
                    elden_ring_path = os.path.join(steamapps_path, 'common', 'ELDEN RING', 'Game')
                    if os.path.exists(elden_ring_path):
                        if not os.path.exists(os.path.join(elden_ring_path, 'SeamlessCoop')):
                            response = QMessageBox.question(None, "Mod Not Found", f"SeamlessCoop mod not found in {elden_ring_path}. Do you want to install the mod?", QMessageBox.Yes | QMessageBox.No)
                            if response == QMessageBox.Yes:
                                install_mod(elden_ring_path)
                        else:
                            potential_paths.append(os.path.join(elden_ring_path, 'SeamlessCoop'))
                    dirs[:] = []  # Stop further recursion

    if not potential_paths:
        # Check other directories
        for drive in drives:
            for root, dirs, files in os.walk(drive):
                if len(root.split(os.sep)) - 1 > 5:  # Limit to 5 directories deep
                    dirs[:] = []  # Don't recurse any deeper
                    continue
                if 'steamapps' in dirs:
                    steamapps_path = os.path.join(root, 'steamapps')
                    elden_ring_path = os.path.join(steamapps_path, 'common', 'ELDEN RING', 'Game')
                    if os.path.exists(elden_ring_path):
                        if not os.path.exists(os.path.join(elden_ring_path, 'SeamlessCoop')):
                            response = QMessageBox.question(None, "Mod Not Found", f"SeamlessCoop mod not found in {elden_ring_path}. Do you want to install the mod?", QMessageBox.Yes | QMessageBox.No)
                            if response == QMessageBox.Yes:
                                install_mod(elden_ring_path)
                        else:
                            potential_paths.append(os.path.join(elden_ring_path, 'SeamlessCoop'))
                    dirs[:] = []  # Stop further recursion

    if potential_paths:
        mod_path = potential_paths[0]
        config = load_config()
        config["mod_path"] = mod_path
        save_config(config)
        mod_path_entry.setText(mod_path)
        create_batch_script()
        update_info_text()
        QMessageBox.information(None, "Auto-Discovery Complete", f"Mod path set to: {mod_path}")
    else:
        QMessageBox.critical(None, "Auto-Discovery Failed", "Failed to auto-discover the mod path. Please select it manually.")
        browse_folder()

def install_mod(elden_ring_path):
    try:
        release_info = get_latest_release_info()
        latest_version = release_info['tag_name']
        download_url = next(asset['browser_download_url'] for asset in release_info['assets'] if asset['name'].endswith('.zip'))

        zip_path = os.path.join(PERSISTENT_DIR, 'SeamlessCoop.zip')
        download_latest_release(download_url, zip_path)

        extract_zip(zip_path, elden_ring_path)
        os.remove(zip_path)

        mod_path = os.path.join(elden_ring_path, 'SeamlessCoop')
        config = load_config()
        config["mod_path"] = mod_path
        save_config(config)

        new_launcher = find_launcher(mod_path)
        if new_launcher:
            config['launcher_name'] = new_launcher

        with open(os.path.join(mod_path, 'version.txt'), 'w') as f:
            f.write(latest_version)

        config['installed_version'] = latest_version
        config['last_updated'] = datetime.strptime(release_info['published_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
        save_config(config)

        check_ini_files(mod_path)
        apply_saved_settings_to_ini(mod_path)
        create_batch_script()
        update_info_text()
        QMessageBox.information(None, "Installation Complete", f"Installed version {latest_version}.")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Installation failed: {e}")

def open_settings_window():
    try:
        settings_window = QDialog()
        settings_window.setWindowTitle("Settings")
        layout = QVBoxLayout(settings_window)

        config = load_config()
        ini_path = os.path.join(config["mod_path"], INI_FILE)
        config_parser = configparser.ConfigParser()
        config_parser.read(ini_path)

        vocabulary = config["vocabulary"]
        settings = {}

        def save_settings():
            try:
                for section, entries in settings.items():
                    for key, widget in entries.items():
                        if section == 'GAMEPLAY' and key in ['allow_invaders', 'death_debuffs', 'allow_summons']:
                            value = '1' if widget.isChecked() else '0'
                        elif section == 'GAMEPLAY' and key == 'overhead_player_display':
                            value = list(vocabulary[section][key].keys())[widget.currentIndex()]
                        elif section == 'LANGUAGE' and key == 'mod_language_override':
                            value = '' if widget.currentText() == "Default" else widget.currentText().lower()
                        else:
                            value = widget.text()
                        if section == 'SCALING' and not value.isdigit():
                            QMessageBox.critical(settings_window, "Error", f"Invalid value for {key} in {section}")
                            return
                        if section == 'SAVE' and value.endswith('sl2'):
                            QMessageBox.critical(settings_window, "Error", "Value for SAVE should not be set to sl2")
                            return
                        config_parser.set(section, key, value)
                with open(ini_path, 'w') as configfile:
                    config_parser.write(configfile)
                save_settings_to_json(config, config_parser)  # Save settings to JSON
                settings_window.accept()
                verify_settings(config_parser, config)  # Verify settings
                QMessageBox.information(None, "Settings Saved", "Settings have been saved successfully.")
            except Exception as e:
                print(f"Error in save_settings: {e}")

        def clone_save_file():
            config = load_config()
            save_ext = config["settings"]["SAVE"].get("save_file_extension", "co2")
            if save_ext == "sl2":
                QMessageBox.critical(settings_window, "Error", "Save file extension cannot be set to .sl2")
                return

            appdata_dir = os.path.join(os.getenv('APPDATA'), 'EldenRing')
            if not os.path.exists(appdata_dir):
                QMessageBox.critical(settings_window, "Error", "Elden Ring AppData folder not found.")
                return

            subfolders = [f.path for f in os.scandir(appdata_dir) if f.is_dir() and f.name.isdigit()]
            if not subfolders:
                QMessageBox.critical(settings_window, "Error", "No subfolders found in Elden Ring AppData folder.")
                return

            save_folder = subfolders[0]
            sl2_file = None
            co2_file = None

            for file in os.listdir(save_folder):
                if file.endswith(".sl2"):
                    sl2_file = os.path.join(save_folder, file)
                    co2_file = os.path.join(save_folder, file.replace(".sl2", f".{save_ext}"))
                    break

            if sl2_file:
                if os.path.exists(co2_file):
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("Warning")
                    msg_box.setText(f"The coop mod save file already exists.\n({co2_file})\nDo you want to overwrite it?\n\n!!! THIS MAY LEAD TO PROGRESSION LOSS !!!")

                    yes_button = msg_box.addButton("Yes", QMessageBox.YesRole)
                    no_button = msg_box.addButton("No", QMessageBox.NoRole)

                    yes_button.setStyleSheet("background-color: red;")
                    no_button.setStyleSheet("background-color: green;")

                    msg_box.exec_()

                    if msg_box.clickedButton() == no_button:
                        return

                try:
                    shutil.copyfile(sl2_file, co2_file)
                    QMessageBox.information(settings_window, "Success", f"Save file cloned successfully to '{co2_file}'")
                except Exception as e:
                    QMessageBox.critical(settings_window, "Error", f"Failed to clone save file: {e}")
            else:
                QMessageBox.critical(settings_window, "Error", "No .sl2 save file found in the folder.")


        settings_grid = QtWidgets.QGridLayout()
        row = 0

        for section in config_parser.sections():
            if section == 'PASSWORD':
                continue
            section_label = QLabel(section)
            section_label.setFont(QFont("Arial", 12, QFont.Bold))
            settings_grid.addWidget(section_label, row, 0, 1, 4, alignment=Qt.AlignHCenter)
            row += 1
            settings[section] = {}
            for key, value in config_parser.items(section):
                display_name = camelcase(key)
                default_value = DEFAULT_VALUES.get(section, {}).get(key, "")
                if section == 'GAMEPLAY':
                    if key in ['allow_invaders', 'death_debuffs', 'allow_summons']:
                        checkbox = QCheckBox(display_name)
                        checkbox.setChecked(value == '1')
                        settings_grid.addWidget(checkbox, row, 0, 1, 1)
                        settings[section][key] = checkbox
                        reset_button = QPushButton("Reset")
                        reset_button.clicked.connect(lambda cb=checkbox, dv=default_value: cb.setChecked(dv == '1'))
                        settings_grid.addWidget(reset_button, row, 1, 1, 1)
                        if key == 'allow_invaders':
                            checkbox.setToolTip(str("Allow hostile invaders to invade your party."))
                        elif key == 'death_debuffs':
                            checkbox.setToolTip(str("Grant Death Rot debuffs upon death.\nCan be cleared by resting at a grace."))
                        elif key == 'allow_summons':
                            checkbox.setToolTip(str("Allow players to use summons."))
                    elif key == 'overhead_player_display':
                        dropdown = QComboBox()
                        dropdown.setToolTip(str("How other players should be displayed"))
                        options = vocabulary[section][key]
                        dropdown.addItems(options.values())
                        dropdown.setCurrentIndex(list(options.keys()).index(value))
                        settings_grid.addWidget(QLabel(display_name), row, 0, 1, 1)
                        settings_grid.addWidget(dropdown, row, 1, 1, 1)
                        settings[section][key] = dropdown
                        reset_button = QPushButton("Reset")
                        reset_button.clicked.connect(lambda cb=dropdown, dv=default_value: cb.setCurrentIndex(list(options.keys()).index(dv)))
                        settings_grid.addWidget(reset_button, row, 2, 1, 1)
                elif section == 'SAVE':
                    entry = QLineEdit(value)
                    entry.setToolTip(str("Select a save file extension you'd like the mod to use.\nDo not include a period.\nCannot be set to \"sl2\""))
                    settings_grid.addWidget(QLabel(display_name), row, 0, 1, 1)
                    settings_grid.addWidget(entry, row, 1, 1, 1)
                    settings[section][key] = entry
                    disclaimer = QLabel("(Do not use \"sl2\")")
                    disclaimer.setFont(QFont("Arial", 8, QFont.StyleItalic))
                    settings_grid.addWidget(disclaimer, row+1, 1, 1, 1, alignment=Qt.AlignHCenter)
                    reset_button = QPushButton("Reset")
                    reset_button.clicked.connect(lambda e=entry, dv=default_value: e.setText(dv))
                    settings_grid.addWidget(reset_button, row, 2, 1, 1)
                    row += 1
                    # Add the clone save button below the save file extension entry
                    clone_button = QPushButton("Generate Mod Save File")
                    clone_button.setToolTip(str("Clone your vanilla save file into a coop save file"))
                    clone_button.clicked.connect(clone_save_file)
                    settings_grid.addWidget(clone_button, row+1, 0, 1, 3)
                    row += 1
                elif section == 'LANGUAGE':
                    dropdown = QComboBox()
                    dropdown.setToolTip(str("Select a Language Override for the mod"))
                    options = get_locale_options(config["mod_path"])
                    dropdown.addItems(options)
                    dropdown.setCurrentText(value.capitalize() if value else "Default")
                    settings_grid.addWidget(QLabel(display_name), row, 0, 1, 1)
                    settings_grid.addWidget(dropdown, row, 1, 1, 1)
                    settings[section][key] = dropdown
                    reset_button = QPushButton("Reset")
                    reset_button.clicked.connect(lambda cb=dropdown: cb.setCurrentText("Default"))
                    settings_grid.addWidget(reset_button, row, 2, 1, 1)
                else:
                    entry = QLineEdit(value)
                    settings_grid.addWidget(QLabel(display_name), row, 0, 1, 1)
                    settings_grid.addWidget(entry, row, 1, 1, 1)
                    settings[section][key] = entry
                    reset_button = QPushButton("Reset")
                    reset_button.clicked.connect(lambda e=entry, dv=default_value: e.setText(dv))
                    settings_grid.addWidget(reset_button, row, 2, 1, 1)
                    if key == 'enemy_health_scaling':
                        tt_example_1 = 346  # Vulgar Militiamen (Liurnia) Example
                        # Calculate HP for 2, 3, and 4 players
                        tt_example_2 = tt_example_1 * (1 + int(value) / 100)
                        tt_example_3 = tt_example_1 * (1 + 2 * int(value) / 100)
                        tt_example_4 = tt_example_1 * (1 + 3 * int(value) / 100)
                        
                        # Format numbers with space as thousand separator and no decimals
                        tt_example_1_formatted = f"{int(tt_example_1):,}".replace(",", " ")
                        tt_example_2_formatted = f"{int(tt_example_2):,}".replace(",", " ")
                        tt_example_3_formatted = f"{int(tt_example_3):,}".replace(",", " ")
                        tt_example_4_formatted = f"{int(tt_example_4):,}".replace(",", " ")
                        
                        tooltip_text = (
                            f"Percentage increase of enemy non-boss HP per player.\n\n"
                            f"Vulgar Militiamen (Liurnia) example with a {int(value)}% scaling:\n"
                            f"Enemy HP with 1 player: {tt_example_1_formatted}\n"
                            f"Enemy HP with 2 players: {tt_example_2_formatted}\n"
                            f"Enemy HP with 3 players: {tt_example_3_formatted}\n"
                            f"Enemy HP with 4 players: {tt_example_4_formatted}"
                        )
                        entry.setToolTip(str(tooltip_text))
                    elif key == 'enemy_damage_scaling':
                        tt_example_1 = 130  # Vulgar Militiamen (Liurnia) Example
                        # Calculate damage for 2, 3, and 4 players
                        tt_example_2 = tt_example_1 * (1 + int(value) / 100)
                        tt_example_3 = tt_example_1 * (1 + 2 * int(value) / 100)
                        tt_example_4 = tt_example_1 * (1 + 3 * int(value) / 100)
                        
                        # Format numbers with space as thousand separator and no decimals
                        tt_example_1_formatted = f"{int(tt_example_1):,}".replace(",", " ")
                        tt_example_2_formatted = f"{int(tt_example_2):,}".replace(",", " ")
                        tt_example_3_formatted = f"{int(tt_example_3):,}".replace(",", " ")
                        tt_example_4_formatted = f"{int(tt_example_4):,}".replace(",", " ")
                        
                        tooltip_text = (
                            f"Percentage increase of enemy non-boss damage potential per player.\n\n"
                            f"Vulgar Militiamen (Liurnia) example with a {int(value)}% scaling:\n"
                            f"Enemy Damage with 1 player: {tt_example_1_formatted}\n"
                            f"Enemy Damage with 2 players: {tt_example_2_formatted}\n"
                            f"Enemy Damage with 3 players: {tt_example_3_formatted}\n"
                            f"Enemy Damage with 4 players: {tt_example_4_formatted}"
                        )
                        entry.setToolTip(str(tooltip_text))
                    elif key == 'enemy_posture_scaling':
                        tt_example_1 = 30  # Vulgar Militiamen (Liurnia) Example
                        # Calculate Poise for 2, 3, and 4 players
                        tt_example_2 = tt_example_1 * (1 + int(value) / 100)
                        tt_example_3 = tt_example_1 * (1 + 2 * int(value) / 100)
                        tt_example_4 = tt_example_1 * (1 + 3 * int(value) / 100)
                        
                        # Format numbers with space as thousand separator and no decimals
                        tt_example_1_formatted = f"{int(tt_example_1):,}".replace(",", " ")
                        tt_example_2_formatted = f"{int(tt_example_2):,}".replace(",", " ")
                        tt_example_3_formatted = f"{int(tt_example_3):,}".replace(",", " ")
                        tt_example_4_formatted = f"{int(tt_example_4):,}".replace(",", " ")
                        
                        tooltip_text = (
                            f"Percentage increase of enemy non-boss Posture/Poise (stun resistance) per player.\n\n"
                            f"Vulgar Militiamen (Liurnia) example with a {int(value)}% scaling:\n"
                            f"Enemy Poise with 1 player: {tt_example_1_formatted}\n"
                            f"Enemy Poise with 2 players: {tt_example_2_formatted}\n"
                            f"Enemy Poise with 3 players: {tt_example_3_formatted}\n"
                            f"Enemy Poise with 4 players: {tt_example_4_formatted}"
                        )
                        entry.setToolTip(str(tooltip_text))
                    elif key == 'boss_health_scaling':
                        tt_example_1 = 6080  # Godrick The Grafted HP Example
                        # Calculate HP for 2, 3, and 4 players
                        tt_example_2 = tt_example_1 * (1 + int(value) / 100)
                        tt_example_3 = tt_example_1 * (1 + 2 * int(value) / 100)
                        tt_example_4 = tt_example_1 * (1 + 3 * int(value) / 100)
                        
                        # Format numbers with space as thousand separator and no decimals
                        tt_example_1_formatted = f"{int(tt_example_1):,}".replace(",", " ")
                        tt_example_2_formatted = f"{int(tt_example_2):,}".replace(",", " ")
                        tt_example_3_formatted = f"{int(tt_example_3):,}".replace(",", " ")
                        tt_example_4_formatted = f"{int(tt_example_4):,}".replace(",", " ")
                        
                        tooltip_text = (
                            f"Percentage increase of enemy boss HP per player.\n\n"
                            f"Godrick The Grafted example with a {int(value)}% scaling:\n"
                            f"Boss HP with 1 player: {tt_example_1_formatted}\n"
                            f"Boss HP with 2 players: {tt_example_2_formatted}\n"
                            f"Boss HP with 3 players: {tt_example_3_formatted}\n"
                            f"Boss HP with 4 players: {tt_example_4_formatted}"
                        )
                        entry.setToolTip(str(tooltip_text))
                    elif key == 'boss_damage_scaling':
                        tt_example_1 = 200  # Godrick The Grafted Damage Example
                        # Calculate Damage for 2, 3, and 4 players
                        tt_example_2 = tt_example_1 * (1 + int(value) / 100)
                        tt_example_3 = tt_example_1 * (1 + 2 * int(value) / 100)
                        tt_example_4 = tt_example_1 * (1 + 3 * int(value) / 100)
                        
                        # Format numbers with space as thousand separator and no decimals
                        tt_example_1_formatted = f"{int(tt_example_1):,}".replace(",", " ")
                        tt_example_2_formatted = f"{int(tt_example_2):,}".replace(",", " ")
                        tt_example_3_formatted = f"{int(tt_example_3):,}".replace(",", " ")
                        tt_example_4_formatted = f"{int(tt_example_4):,}".replace(",", " ")
                        
                        tooltip_text = (
                            f"Percentage increase of enemy boss damage potential per player.\n\n"
                            f"Godrick The Grafted example with a {int(value)}% scaling:\n"
                            f"Boss Example Damage with 1 player: {tt_example_1_formatted}\n"
                            f"Boss Example Damage with 2 players: {tt_example_2_formatted}\n"
                            f"Boss Example Damage with 3 players: {tt_example_3_formatted}\n"
                            f"Boss Example Damage with 4 players: {tt_example_4_formatted}"
                        )
                        entry.setToolTip(str(tooltip_text))
                    elif key == 'boss_posture_scaling':
                        tt_example_1 = 105  # Godrick The Grafted Poise Example
                        # Calculate Poise for 2, 3, and 4 players
                        tt_example_2 = tt_example_1 * (1 + int(value) / 100)
                        tt_example_3 = tt_example_1 * (1 + 2 * int(value) / 100)
                        tt_example_4 = tt_example_1 * (1 + 3 * int(value) / 100)
                        
                        # Format numbers with space as thousand separator and no decimals
                        tt_example_1_formatted = f"{int(tt_example_1):,}".replace(",", " ")
                        tt_example_2_formatted = f"{int(tt_example_2):,}".replace(",", " ")
                        tt_example_3_formatted = f"{int(tt_example_3):,}".replace(",", " ")
                        tt_example_4_formatted = f"{int(tt_example_4):,}".replace(",", " ")
                        
                        tooltip_text = (
                            f"Percentage increase of enemy boss Posture/Poise (stun resistance) per player.\n\n"
                            f"Godrick The Grafted example with a {int(value)}% scaling:\n"
                            f"Boss Poise with 1 player: {tt_example_1_formatted}\n"
                            f"Boss Poise with 2 players: {tt_example_2_formatted}\n"
                            f"Boss Poise with 3 players: {tt_example_3_formatted}\n"
                            f"Boss Poise with 4 players: {tt_example_4_formatted}"
                        )
                        entry.setToolTip(str(tooltip_text))
                row += 1

        layout.addLayout(settings_grid)

        save_button = QPushButton("Save Settings")
        save_button.setToolTip(str("Save your settings"))
        save_button.clicked.connect(save_settings)
        layout.addWidget(save_button)
        settings_window.setLayout(layout)
        settings_window.exec_()
    except Exception as e:
        print(f"Error in open_settings_window: {e}")

def save_settings_to_json(config, config_parser):
    for section in config_parser.sections():
        if section not in config["settings"]:
            config["settings"][section] = {}
        for key, value in config_parser.items(section):
            config["settings"][section][key] = value
    save_config(config)

def verify_settings(config_parser, config):
    temp_config = {}
    for section in config_parser.sections():
        temp_config[section] = {}
        for key, value in config_parser.items(section):
            temp_config[section][key] = value
    save_settings_to_json(temp_config, config_parser)

    # Re-read the JSON and INI to compare
    reloaded_config = load_config()
    reloaded_config_parser = configparser.ConfigParser()
    reloaded_config_parser.read(os.path.join(config["mod_path"], INI_FILE))

    for section in config_parser.sections():
        for key in config_parser.options(section):
            ini_value = reloaded_config_parser.get(section, key)
            json_value = reloaded_config["settings"].get(section, {}).get(key, "")
            if ini_value != config_parser.get(section, key) or json_value != config_parser.get(section, key):
                QMessageBox.warning(None, "Warning", f"Failed to save {key} in {section}")
                return

def apply_saved_settings_to_ini(mod_path):
    config = load_config()
    ini_path = os.path.join(mod_path, INI_FILE)
    config_parser = configparser.ConfigParser()
    config_parser.read(ini_path)

    for section, entries in config["settings"].items():
        if section not in config_parser:
            config_parser.add_section(section)
        for key, value in entries.items():
            config_parser.set(section, key, value)

    with open(ini_path, 'w') as configfile:
        config_parser.write(configfile)

def update_password():
    config = load_config()
    ini_path = os.path.join(config["mod_path"], INI_FILE)
    password = read_password_from_ini(ini_path)
    if password:
        password_entry.setText(password)

def show_info():
    config = load_config()
    installed_version = config.get('installed_version', 'Unknown')
    last_updated = config.get('last_updated', 'Unknown')
    launcher_path = os.path.join(os.path.dirname(config["mod_path"]), config['launcher_name'])
    wdir = PERSISTENT_DIR
    QMessageBox.information(None, "Info", f"Current Version: {installed_version}\nLast Updated: {last_updated}\nLauncher Path: {launcher_path}\nWorking Directory: {wdir}\nERSCMU Version: {PROGRAM_VERSION}\nLauncher Version: {LAUNCHER_VERSION}\n\nChangelog (last 5 versions):\n{get_changelog(5)}")

def show_about():
    about_text = f"""
MIT License

Copyright (c) 2024 FreemoX

"Elden Ring Seamless Coop Mod Updater" is in no ways affiliated with the creators of Elden Ring or the creator of the Seamless Coop mod.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

ERSCMU Version: {PROGRAM_VERSION}
Launcher Version: {LAUNCHER_VERSION}
    """
    QMessageBox.information(None, "About", about_text)

def initial_update_check():
    global FIRST_RUN
    check_for_updates()
    FIRST_RUN = 0

def create_gui():
    global mod_path_entry, info_text, password_entry, toggle_button

    app = QApplication([])

    main_window = QMainWindow()
    main_window.setWindowTitle("Elden Ring Seamless Coop Mod Updater")

    central_widget = QWidget()
    main_layout = QVBoxLayout(central_widget)

    # Set application icon
    #app.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.ico')))
    app.setWindowIcon(QtGui.QIcon(LOGO_PATH))

    menu_bar = main_window.menuBar()

    settings_action = QtWidgets.QAction("Settings", main_window)
    settings_action.triggered.connect(open_settings_window)
    menu_bar.addAction(settings_action)

    check_updates_action = QtWidgets.QAction("Check for Updates", main_window)
    check_updates_action.setToolTip(str("Manually check for new mod updates"))
    check_updates_action.triggered.connect(check_for_updates)
    menu_bar.addAction(check_updates_action)

    info_action = QtWidgets.QAction("Info", main_window)
    info_action.setToolTip(str("Check some basic application info"))
    info_action.triggered.connect(show_info)
    menu_bar.addAction(info_action)

    about_action = QtWidgets.QAction("About", main_window)
    about_action.setToolTip(str("Disclaimer and license"))
    about_action.triggered.connect(show_about)
    menu_bar.addAction(about_action)

    # Add version label to the menu bar
    version_label = QLabel(f"ERSCMU Version: {PROGRAM_VERSION}")
    version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    version_label.setStyleSheet("padding-right: 10px;")  # Optional: add some padding to the right
    menu_bar.setCornerWidget(version_label, Qt.TopRightCorner)
    version_label_tooltip_text = f"ERSCMU version.\nThis is the version of this program you're currently running.\nLauncher Version: {LAUNCHER_VERSION}\n\nChangelog:\n{get_changelog()}"
    version_label.setToolTip(str(version_label_tooltip_text))

    mod_path_label = QLabel("Mod Folder:")
    mod_path_entry = QLineEdit()
    mod_path_entry.setFixedWidth(400)
    browse_button = QPushButton("Browse")
    browse_button.setToolTip(str("Manually select the Seamless Coop mod folder"))
    browse_button.clicked.connect(browse_folder)
    auto_button = QPushButton("Auto")
    auto_button.setToolTip(str("Automatically discover the Seamless Coop mod folder"))
    auto_button.clicked.connect(auto_discover_mod_path)

    config = load_config()
    mod_path_entry.setText(config["mod_path"])

    mod_path_layout = QHBoxLayout()
    mod_path_layout.addWidget(mod_path_label)
    mod_path_layout.addWidget(mod_path_entry)
    mod_path_layout.addWidget(browse_button)
    mod_path_layout.addWidget(auto_button)

    check_updates_button = QPushButton("Check for Updates")
    check_updates_button.setToolTip(str("Manually check for new mod updates"))
    check_updates_button.clicked.connect(check_for_updates)

    password_label = QLabel("Session Password:")
    password_entry = QLineEdit()
    password_entry.setToolTip(str("Define your session password.\nNote that all players must have the same password!"))
    password_entry.setEchoMode(QLineEdit.Password)
    toggle_button = QPushButton("Show")
    toggle_button.clicked.connect(toggle_password)
    save_password_button = QPushButton("Save Password")
    save_password_button.clicked.connect(save_password)

    password_layout = QHBoxLayout()
    password_layout.addWidget(password_label)
    password_layout.addWidget(password_entry)
    password_layout.addWidget(toggle_button)
    password_layout.addWidget(save_password_button)

    launch_button = QPushButton("Launch Seamless Coop")
    launch_button.setToolTip(str("Start Elden Ring Seamless Coop"))
    launch_button.clicked.connect(launch_mod)

    info_text = QLabel()
    info_text.setToolTip(str("Seamless Coop version and install date"))
    update_info_text()

    main_layout.addLayout(mod_path_layout)
    main_layout.addWidget(check_updates_button)
    main_layout.addLayout(password_layout)
    main_layout.addWidget(launch_button)
    main_layout.addWidget(info_text)

    central_widget.setLayout(main_layout)
    main_window.setCentralWidget(central_widget)

    update_password()
    initial_update_check()

    main_window.show()
    app.exec_()

if __name__ == "__main__":
    check_logo()
    create_gui()