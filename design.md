# Auto Key Presser - Feature & UI Elements

## Features & UI Elements

### 1. Key Sets

**Description:** Configurable sets of keys to be pressed automatically. Each key set has: trigger key, keys list, delay, repeat mode. Supports both keyboard keys and mouse buttons (M4, M5).

**UI Elements:**

- **Checkbox** - Enable/Disable key set
- **Button** - ✕ Delete key set
- **Display Button** - Trigger key display (disabled)
- **Button** - CHG - Change trigger key
- **Button** - ONCE - Set repeat mode to once
- **Button** - INFINITY - Set repeat mode to infinity
- **Checkbox** - Use - Enable repeat interval
- **Spinbox** - Repeat interval (seconds)
- **Spinbox** - Delay (ms)
- **Button** - PRESS KEY TO ADD - Capture and add a new key
- **Button** - M4 - Add mouse button 4
- **Button** - M5 - Add mouse button 5
- **Chip** - Key name (e.g., "4", "5", "space")
- **Button (in Chip)** - X - Remove individual key from set
- **Button** - START AUTO PRESSER - Start/stop key pressing

---

### 2. Random Move

**Description:** Mouse movement and automated click mapping. Supports single points or rectangular click zones with configurable per-location names, delays, and selection weights.

**UI Elements:**

- **Display Button** - Trigger key display (disabled)
- **Button** - CHG - Change trigger key
- **Button** - ORD - Set mode to Order (sequential path)
- **Button** - RND - Set mode to Random (weighted choice)
- **Spinbox** - Delay (ms) - Global fallback delay
- **Button** - CLEAR ALL - Clear all recorded locations
- **Chip** - Location description (e.g. "Zone 1 (100,200)-(300,400) 250ms w:2")
- **Double-Click (on Chip)** - Open modal to customize Name, Delay, and Weight
- **Button (in Chip)** - X - Remove individual location
- **Button** - POINT - Select point recording mode
- **Button** - ZONE - Select zone recording mode (click twice for corner boundaries)
- **Checkbox** - Bulk Record Mode - Continuously record multiple locations
- **Button** - RECORD POSITIONS - Start/stop location recording
- **Canvas** - Visual Map displaying dots/rectangles and Order mode paths
- **Button** - START RANDOM MOVE - Start/stop click automation

---

### 3. Active Window

**Description:** Filter automation by active window title. Only presses keys/clicks when target window is active. Real-time status indicator.

**UI Elements:**

- **Checkbox** - Active Window Only - Enable/Disable active window
- **Button** - ▼ - Show process dropdown menu
- **Input** - Window Title/Process Name query text
- **Label** - Status indicator (Checking... / Matched / Not Matched)
- **Button** - Window Title - Select window title mode
- **Button** - Process Name - Select process name mode

---

## Global UI Elements

### Tab Navigation

- **Button** - Key Sets - Switch to key sets tab
- **Button** - Random Move - Switch to random move tab

### Footer

- **Button** - SAVE ALL SETTINGS - Save configuration
- **Button** - CLEAR CONFIG - Reset to default config

### Overlay

- **Label** - ◱ - Show main window
- **Label** - ■ STOP - Stop running feature

---

### 4. Emergency Panic Abort (Global Stop)

**Description:** An instant global emergency panic button to immediately abort all running automations if mouse clicks or keystrokes loop out of control.

**Shortcut Hotkeys:**

- **Pause** (Break Key) - Ultimate emergency stop on desktop keyboards.
- **F12** - Emergency stop shortcut for laptops/compact keyboards.

**Confirmation Feedback:**

- Plays a high-to-low confirmation auditory alert (`800Hz` -> `500Hz`).
- Instantly changes the central status indicator to red: **EMERGENCY ABORTED - ALL STOPPED**.

---

## UI Element Consistency Rules

**UI elements of the same type will always have:**

- Same properties (padding, font, border, etc.)
- Same state colors (normal, hover, active, disabled)
- Same background colors per state

**Example:**

- All **Buttons** use the same hover/active colors and padding
- All **Chips** use the same styling and remove button style
- All **Checkboxes** use the same color scheme
- All **Spinboxes** use the same styling
