
# DebianSetupSuite

DebianSetupSuite is a modular, configuration-driven collection of utilities for installing, configuring, managing, and maintaining Debian-based Linux systems.

The suite uses a shared Python loader, JSON configuration files, reusable utility modules, and a state-machine execution framework.

It supports package installation, application deployment, system services, firewall configuration, networking, backups, downloads, Docker management, desktop launchers, and unattended setup workflows.

## Design Goals

- Keep individual utilities modular.
- Reuse shared functionality across tools.
- Separate configuration from execution logic.
- Validate configuration before executing operations.
- Provide consistent interactive menus.
- Display planned operations before execution where applicable.
- Support both standard-user and root-level workflows.
- Allow different machine profiles to use different configurations.
- Support automated and unattended system setup.

## Available Utilities

`DebianLoader.py` registers 24 utilities.

| Utility | Purpose |
|---|---|
| Package Installer | Install and remove APT packages |
| Deb Installer | Install and remove local or downloaded `.deb` packages |
| Flatpak Installer | Install and remove Flatpak applications |
| ThirdParty Installer | Manage third-party APT repositories and packages |
| Archive Installer | Install applications distributed as archives |
| Binary Installer | Install standalone binary applications |
| Docker Manager | Download, build, start, stop, test, and remove Docker resources |
| Backup | Copy files, copy directories, and create ZIP archives |
| Download | Download missing files and generate links JSON |
| YouTube | Open YouTube and download playlists |
| Function | Analyse and display Python functions |
| Unattended Standard | Run configured standard-user setup operations |
| Arcade | Manage arcade application setup |
| DOSLoader | Manage DOS application setup |
| Launcher | Manage application launchers and kiosk configuration |
| IPCam | Manage IP camera-related installation and services |
| Startup Services | Install, remove, and restart startup services |
| Shutdown Services | Install, remove, and restart shutdown services |
| Schedule Services | Install, remove, and restart scheduled services and timers |
| AutoStart | Manage automatic startup configuration |
| Firewall | Configure and manage UFW |
| RDP | Install and manage remote desktop services |
| Network | Apply configured network setup |
| Unattended Root | Run configured root-level setup operations |

Each utility uses a constants module to integrate with the shared loader.

## Requirements

### Operating System

DebianSetupSuite is designed for Debian-based Linux distributions.

The suite uses Debian-specific package management and system administration tools, including APT and systemd-related operations.

Some utilities also depend on desktop environments, network services, or application-specific software.

### Python

The main loader is written in Python 3.

Run the suite from the project directory so relative paths to configuration files, documentation, and supporting modules can be resolved.

### Dependencies

Dependencies vary by utility.

Examples declared in the project include:

| Utility | Dependencies |
|---|---|
| Deb Installer | `wget`, `dpkg` |
| Flatpak Installer | `flatpak` |
| Binary Installer | `curl` |
| ThirdParty Installer | Repository and package-management utilities |
| Firewall | `ufw` |
| Backup | `rsync`, `zip` |
| Download | `wget`, `unzip`, `p7zip-full` |
| YouTube | `firefox-esr`, `ffmpeg` |
| DOSLoader | `dosbox`, `wget`, `unzip`, `tar`, `unrar-free`, `p7zip-full` |
| Startup Services | `logrotate` |
| Shutdown Services | `logrotate` |
| Schedule Services | `logrotate` |
| IPCam | `wget`, `unzip` |

Additional dependencies may be installed or used by individual processing functions.

The loader checks the selected utility's declared dependencies and can attempt to install missing packages.

## Running DebianSetupSuite

### Interactive Mode

From the project directory, run:

```bash
python3 DebianLoader.py
```

For utilities requiring root permissions:

```bash
sudo python3 DebianLoader.py
```

The loader provides interactive selection of registered utilities.

The selected utility determines the required account level.

### User Permissions

Utilities declare their required account level through `REQUIRED_USER` in their constants modules.

The suite distinguishes between standard-user and root-level operations.

Standard-user utilities include:

- Package Installer
- Deb Installer
- Flatpak Installer
- ThirdParty Installer
- Archive Installer
- Binary Installer
- Docker Manager
- Backup
- Download
- YouTube
- Function
- Unattended Standard

Root-level utilities include:

- Arcade
- DOSLoader
- Launcher
- IPCam
- Startup Services
- Shutdown Services
- Schedule Services
- AutoStart
- Firewall
- RDP
- Network
- Unattended Root

Run the loader with the appropriate permissions for the selected utility.

## Configuration System

DebianSetupSuite uses JSON configuration files to define machine profiles, installation jobs, paths, settings, and supported operations.

### Main Configuration Mapping

The main configuration mapping is stored in:

```text
config/AppConfigSettings.json
```

This file maps utilities to their configuration files.

The mapping supports multiple machine profiles, including a default configuration.

The supplied configuration includes profile sections such as:

```text
YOUR DESKTOP MODEL
YOUR MEDIACENTRE MODEL
YOUR LAPTOP MODEL
Default
```

The model-specific names are placeholders that can be customised for the target machines.

### Default Configuration

The `Default` profile maps utilities to configuration files under:

```text
config/Default/
```

For example:

```json
{
  "Default": {
    "Packages": "config/Default/DefaultPackages.json",
    "DEB": "config/Default/DefaultDEB.json",
    "Flatpak": "config/Default/DefaultFlatpak.json",
    "Firewall": "config/Default/DefaultFW.json",
    "Docker": "config/Default/DefaultDocker.json"
  }
}
```

This is an abbreviated example of the mapping.

The actual configuration contains entries for all registered utility categories.

### Default Configuration Files

The project includes:

```text
config/Default/
├── DefaultPackages.json
├── DefaultDEB.json
├── DefaultThirdParty.json
├── DefaultFW.json
├── DefaultFlatpak.json
├── DefaultNetwork.json
├── DefaultArchive.json
├── DefaultBinary.json
├── DefaultDocker.json
├── DefaultRDP.json
├── DefaultIPCam.json
├── DefaultMSDOS.json
├── DefaultArcade.json
├── DefaultLauncher.json
├── DefaultBackup.json
├── DefaultDownload.json
├── DefaultFunctions.json
├── DefaultAutostart.json
├── DefaultStartupServices.json
├── DefaultShutdownServices.json
├── DefaultScheduleServices.json
├── DefaultYouTube.json
├── DefaultUnattendedStandard.json
└── DefaultUnattendedRoot.json
```

These files define the jobs and settings used by their respective utilities.

### Configuration Validation

Each utility declares validation rules in its constants module.

The loader supports:

- Required configuration fields.
- Secondary validation of nested configuration data.
- Detection of machine identity.
- Configuration selection.
- Verification of required settings.
- Job selection and status checks.

Validation requirements differ between utilities.

Consult the corresponding documentation JSON for supported configuration fields.

## Package Installation Utilities

### Package Installer

**Constants:** `constants/PackageConstants.py`

**Default configuration:** `config/Default/DefaultPackages.json`

Provides APT package installation and removal.

The utility supports installation jobs defined in JSON and uses package status checks to determine whether selected packages are installed.

### Deb Installer

**Constants:** `constants/DebConstants.py`

**Default configuration:** `config/Default/DefaultDEB.json`

Handles installation and removal of Debian package files.

Declared dependencies include:

```text
wget
dpkg
```

### Flatpak Installer

**Constants:** `constants/FlatpakConstants.py`

**Default configuration:** `config/Default/DefaultFlatpak.json`

Supports:

- Installing Flatpak applications.
- Removing Flatpak applications.
- Ensuring the Flathub remote is configured.
- Displaying configuration help.

### ThirdParty Installer

**Constants:** `constants/ThirdPartyConstants.py`

**Default configuration:** `config/Default/DefaultThirdParty.json`

Manages third-party application installation using configured repositories and package information.

Supports:

- Installing configured third-party applications.
- Uninstalling applications.
- Removing repository and keyring configuration.
- Displaying configuration help.

### Archive Installer

**Constants:** `constants/ArchiveConstants.py`

**Default configuration:** `config/Default/DefaultArchive.json`

Handles installation and removal of software distributed through supported archive formats.

Archive processing is implemented through reusable functions in `modules/archive_utils.py`.

### Binary Installer

**Constants:** `constants/BinaryConstants.py`

**Default configuration:** `config/Default/DefaultBinary.json`

Handles installation and removal of standalone binary applications.

The utility declares `curl` as a dependency.

## Docker Manager

**Constants:** `constants/DockerConstants.py`

**Default configuration:** `config/Default/DefaultDocker.json`

**Module:** `modules/docker_utils.py`

The Docker Manager provides configured operations for managing Docker resources.

### Operations

- Download.
- Start.
- Check status.
- Build.
- Test.
- Stop.
- Remove.

The exact Docker resources and settings are determined by the selected configuration jobs.

Docker availability and permissions depend on the target system.

## Backup Utility

**Constants:** `constants/BackupConstants.py`

**Default configuration:** `config/Default/DefaultBackup.json`

### Operations

- Copy Folders.
- Copy Files.
- Create Zip Archive.
- Run All Tasks.
- Show config help.

### Dependencies

```text
rsync
zip
```

The utility supports separate backup operations as well as a combined workflow.

Source paths, destination paths, and backup jobs are controlled by the configuration.

Before executing backup tasks, verify that the destination has sufficient space and that source and destination paths are correct.

## Download Utility

**Constants:** `constants/DownloadConstants.py`

**Default configuration:** `config/Default/DefaultDownload.json`

**Module:** `modules/download_utils.py`

### Operations

- Download Missing Files.
- Generate Links JSON.
- Show config help.

### Dependencies

```text
wget
unzip
p7zip-full
```

The utility uses configured download jobs and can generate JSON containing download links.

## YouTube Utility

**Constants:** `constants/YouTubeConstants.py`

**Default configuration:** `config/Default/DefaultYouTube.json`

**Module:** `modules/ytdlp_utils.py`

### Operations

- Open YouTube / Login.
- Download playlist.
- Show config help.

### Dependencies

```text
firefox-esr
ffmpeg
```

The utility uses the configured browser and download-processing functions.

Downloaded content should comply with applicable copyright requirements and service terms.

## Function Utility

**Constants:** `constants/FunctionConstants.py`

**Default configuration:** `config/Default/DefaultFunctions.json`

**Module:** `modules/function_utils.py`

### Operations

- Analyse Python functions.
- Show functions.
- Display configuration help.

This utility provides inspection of Python functions using the configured module paths.

It is useful for examining reusable functions within the project.

## Arcade Utility

**Constants:** `constants/ArcadeConstants.py`

**Default configuration:** `config/Default/DefaultArcade.json`

The Arcade utility manages configured arcade setup operations.

### Operations

- Install.
- Update settings.
- Reset.
- Uninstall.
- Show configuration help.

The utility requires root-level execution.

The actual application settings and resources are determined by the configured jobs.

## DOSLoader Utility

**Constants:** `constants/DOSLoaderConstants.py`

**Default configuration:** `config/Default/DefaultMSDOS.json`

### Operations

- Install.
- Update permissions.
- Create shortcut.
- Remove shortcut.
- Show configuration help.

### Dependencies

```text
dosbox
wget
unzip
tar
unrar-free
p7zip-full
```

DOSLoader supports configured DOS application setup and desktop shortcut management.

## Launcher Utility

**Constants:** `constants/LauncherConstants.py`

**Default configuration:** `config/Default/DefaultLauncher.json`

The Launcher utility manages application launchers and kiosk-related settings.

### Operations

- Install.
- Update settings.
- Reset.
- Uninstall.
- Enable Kiosk (Openbox autologin).
- Disable Kiosk (restore normal login).
- Show configuration help.

### Kiosk Mode

The kiosk operations manage configured Openbox autologin behaviour.

Changing kiosk settings can affect the system's normal graphical login process.

Ensure an alternative administrative access method is available before enabling kiosk mode.

## IPCam Utility

**Constants:** `constants/IPCamConstants.py`

**Default configuration:** `config/Default/DefaultIPCam.json`

**Module:** `modules/camera_utils.py`

### Operations

- Install.
- Uninstall.
- Restart services.
- Show configuration help.

### Dependencies

```text
wget
unzip
```

The utility uses configured camera-related installation resources and service definitions.

## System Service Utilities

DebianSetupSuite includes separate utilities for startup services, shutdown services, scheduled services, and application autostart.

### Startup Services

**Constants:** `constants/StartupServicesConstants.py`

**Default configuration:** `config/Default/DefaultStartupServices.json`

Supports:

- Installing configured services.
- Uninstalling services.
- Restarting services.
- Displaying configuration help.

The implementation includes operations for copying files, folders, scripts, and service definitions.

### Shutdown Services

**Constants:** `constants/ShutdownServicesConstants.py`

**Default configuration:** `config/Default/DefaultShutdownServices.json`

Supports:

- Installing configured shutdown services.
- Uninstalling services.
- Restarting services.
- Displaying configuration help.

### Schedule Services

**Constants:** `constants/ScheduleServicesConstants.py`

**Default configuration:** `config/Default/DefaultScheduleServices.json`

Supports:

- Installing scheduled services and timers.
- Uninstalling scheduled services and timers.
- Restarting timers.
- Displaying configuration help.

The implementation includes processing of systemd service and timer files.

### AutoStart

**Constants:** `constants/AutoStartConstants.py`

**Default configuration:** `config/Default/DefaultAutostart.json`

**Module:** `modules/autostart_utils.py`

Supports configured application or script autostart operations.

The pipeline includes installation, removal, and execution-related states.

### Service Management Precautions

Service changes may affect system startup, shutdown, network access, and scheduled operations.

Before applying changes:

- Review the configured service or timer files.
- Verify source and destination paths.
- Confirm that scripts have the required permissions.
- Avoid disabling services required for remote access.
- Review the execution plan before confirmation.

## Firewall Utility

**Constants:** `constants/FirewallConstants.py`

**Default configuration:** `config/Default/DefaultFW.json`

**Module:** `modules/firewall_utils.py`

### Operations

- Apply firewall rules.
- Show UFW status.
- Enable UFW.
- Disable UFW.
- Reset UFW (flush rules).
- Show configuration help.

### Dependency

```text
ufw
```

### Firewall Safety

Firewall operations can interrupt network connectivity.

This is especially important when working through SSH or another remote management connection.

Verify that required management ports are permitted before enabling or resetting firewall rules.

## RDP Utility

**Constants:** `constants/RDPConstants.py`

**Default configuration:** `config/Default/DefaultRDP.json`

**Module:** `modules/rdp_utils.py`

### Operations

- Install.
- Uninstall.
- Regenerate XRDP keys/certs.
- Show configuration help.

The utility provides remote desktop installation and configuration operations.

RDP configuration should be reviewed alongside the firewall and network settings.

## Network Utility

**Constants:** `constants/NetworkConstants.py`

**Default configuration:** `config/Default/DefaultNetwork.json`

**Module:** `modules/network_utils.py`

The Network utility applies configured network installation and removal operations.

### Operations

- Install.
- Uninstall.
- Show configuration help.

Network configuration changes can interrupt existing connections.

Use caution when executing network changes remotely.

## Unattended Setup

DebianSetupSuite provides separate unattended workflows for standard-user and root-level operations.

### Unattended Standard

**Constants:** `constants/UnattendedStandardConstants.py`

**Default configuration:** `config/Default/DefaultUnattendedStandard.json`

### Operations

- Run unattended standard.
- Show configuration help.

This utility coordinates configured standard-user setup operations.

### Unattended Root

**Constants:** `constants/UnattendedRootConstants.py`

**Default configuration:** `config/Default/DefaultUnattendedRoot.json`

### Operations

- Run unattended root.
- Show configuration help.

This utility coordinates configured root-level setup operations.

### Unattended Execution Precautions

Unattended workflows may execute multiple configured changes.

Before running:

- Review the selected machine profile.
- Verify the referenced configuration files.
- Check required permissions.
- Confirm that installation sources are trusted.
- Review operations that modify networking, services, or firewall settings.

## Architecture

DebianSetupSuite separates the loader, utility definitions, processing modules, and JSON configuration.

### General Architecture

```text
DebianLoader.py
       |
       v
Utility Selection
       |
       v
Constants Module
       |
       v
Configuration Selection
       |
       v
Validation and Dependency Checks
       |
       v
Action Selection
       |
       v
Pipeline Execution
       |
       v
Reusable Module Functions
       |
       v
Result and Logging
```

### DebianLoader.py

`DebianLoader.py` is the main application entry point.

It provides:

- Utility registration.
- Utility selection.
- Dependency checking.
- User-account verification.
- Machine identity detection.
- Configuration selection.
- JSON validation.
- Status checks.
- Action menus.
- Pipeline execution.
- Logging.
- Final execution results.

### Constants Modules

Each utility has a corresponding module under:

```text
constants/
```

These modules define utility-specific settings and behaviour.

Common definitions include:

- `PRIMARY_CONFIG`
- `JOBS_KEY`
- `VALIDATION_CONFIG`
- `SECONDARY_VALIDATION`
- `DETECTION_CONFIG`
- `LOG_DIR`
- `LOG_PREFIX`
- `LOGS_TO_KEEP`
- `ROTATE_LOG_NAME`
- `REQUIRED_USER`
- `ACTIONS`
- `STATUS_FN_CONFIG`
- `SUB_MENU`
- `DEPENDENCIES`
- `INSTALLED_LABEL`
- `UNINSTALLED_LABEL`
- `PLAN_COLUMN_ORDER`
- `OPTIONAL_PLAN_COLUMNS`
- `PIPELINE_STATES`
- `CONFIG_DOC`

These are part of the shared interface expected by the loader.

### State Machine

The loader uses an execution state machine.

Defined states include:

```text
INITIAL
DEP_CHECK
DEP_INSTALL
IDENTITY_DETECTION
JSON_TOPLEVEL_CHECK
JSON_REQUIRED_KEYS_CHECK
SECONDARY_VALIDATION
DISPLAY_VERIFICATION
CONFIG_LOADING
PACKAGE_STATUS
BUILD_ACTIONS
MENU_SELECTION
SUB_SELECT
PREPARE_PLAN
CONFIRM
EXECUTE
FINALIZE
```

Not every operation uses every state.

Actions can specify different execution and confirmation behaviour.

### Pipeline Processing

Utility constants define pipeline operations.

Pipeline steps specify:

- The function to execute.
- Arguments to pass.
- Conditions controlling execution.
- Context keys used to store results.

The loader evaluates the configured pipeline for selected jobs.

Results are reported using the pipeline's success key and completion label.

### Shared Modules

Reusable functionality is implemented under:

```text
modules/
```

The project includes:

| Module | Responsibility |
|---|---|
| `apt_repo_utils.py` | APT repository management |
| `archive_utils.py` | Archive processing |
| `autostart_utils.py` | Autostart operations |
| `binary_utils.py` | Binary installation |
| `browser_utils.py` | Browser operations |
| `camera_utils.py` | Camera-related setup |
| `desktop_utils.py` | Desktop integration |
| `display_utils.py` | Terminal menus, prompts, and displays |
| `docker_utils.py` | Docker operations |
| `download_utils.py` | Download handling |
| `firewall_utils.py` | Firewall management |
| `flatpak_utils.py` | Flatpak operations |
| `function_utils.py` | Function inspection |
| `json_utils.py` | JSON loading and validation |
| `logger_utils.py` | Logging |
| `network_utils.py` | Network configuration |
| `package_utils.py` | Package management |
| `rdp_utils.py` | Remote desktop configuration |
| `service_utils.py` | Service management |
| `state_machine_utils.py` | State-machine support |
| `system_utils.py` | System information and operations |
| `test_utils.py` | Test-related helpers |
| `ytdlp_utils.py` | YouTube download processing |

### Documentation Files

Each utility has a JSON documentation file under:

```text
doc/
```

These files describe the supported configuration structure and fields.

The loader can display configuration help through the relevant utility menu.

## Project Structure

```text
DebianSetupSuite/
├── DebianLoader.py
├── README.md
├── LICENSE
├── .gitignore
├── .gitattributes
├── config/
│   ├── AppConfigSettings.json
│   └── Default/
│       ├── DefaultPackages.json
│       ├── DefaultDEB.json
│       ├── DefaultThirdParty.json
│       ├── DefaultFW.json
│       ├── DefaultFlatpak.json
│       ├── DefaultNetwork.json
│       ├── DefaultArchive.json
│       ├── DefaultBinary.json
│       ├── DefaultDocker.json
│       ├── DefaultRDP.json
│       ├── DefaultIPCam.json
│       ├── DefaultMSDOS.json
│       ├── DefaultArcade.json
│       ├── DefaultLauncher.json
│       ├── DefaultBackup.json
│       ├── DefaultDownload.json
│       ├── DefaultFunctions.json
│       ├── DefaultAutostart.json
│       ├── DefaultStartupServices.json
│       ├── DefaultShutdownServices.json
│       ├── DefaultScheduleServices.json
│       ├── DefaultYouTube.json
│       ├── DefaultUnattendedStandard.json
│       └── DefaultUnattendedRoot.json
├── constants/
├── doc/
├── modules/
├── autoStart/
├── services/
└── settings/
```

## Logging

The loader supports per-utility logging.

Logging settings are declared in the utility constants modules.

These include:

- Log directory.
- Log filename prefix.
- Number of logs to retain.
- Log rotation settings.

The loader creates timestamped log files and uses the shared logging functions for execution output.

When running with elevated privileges, the loader contains logic to place logs under the invoking user's home directory when that user can be determined.

## Security and Safety

DebianSetupSuite can modify important operating system settings.

Potentially sensitive operations include:

- Package installation and removal.
- Firewall configuration.
- Network changes.
- System service installation.
- Scheduled task configuration.
- Remote desktop setup.
- Kiosk and autologin configuration.
- Application downloads.
- File and directory copying.
- Unattended system configuration.

Review configuration files before executing operations.

Use trusted installation sources and keep credentials, private configuration, and machine-specific secrets out of public repositories.

## Extending DebianSetupSuite

To add a new utility:

1. Create a processing module under `modules/` if new processing functions are required.
2. Create a constants module under `constants/`.
3. Define the required loader constants.
4. Create a JSON configuration file.
5. Create a documentation JSON file under `doc/`.
6. Add the utility's configuration mapping to `config/AppConfigSettings.json`.
7. Register the constants module in `AVAILABLE_CONSTANTS` inside `DebianLoader.py`.
8. Define menu actions and pipeline states.
9. Test validation, dependencies, permissions, execution, and error handling.
10. Update this README.

Prefer shared helpers when adding functionality used by multiple utilities.

Keep utility-specific processing logic separate from the shared loader whenever possible.

## License

See the `LICENSE` file for the project's licensing terms.
