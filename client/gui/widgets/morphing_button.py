"""
MorphingButton - Button that transitions between icon and expanded menu.
Extracted from custom_widgets.py.
"""

import os
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, pyqtProperty, QPropertyAnimation, QRect, QSize
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QIcon, QPixmap

from client.gui.animators.animation_driver import AnimationDriver
from client.utils.resource_path import get_resource_path


class MorphingButton(QPushButton):
    """
    Button that morphs between icon-only and expanded menu.
    """
    # Signals
    toggled_state = pyqtSignal(bool)
    expanded = pyqtSignal(bool)
    styleChanged = pyqtSignal(bool)  # Emitted when solid/ghost style changes
    itemClicked = pyqtSignal(object)  # Emits item ID
    
    # Constants
    COLLAPSED_SIZE = 48
    EXPAND_DELAY_MS = 75
    ANIMATION_DURATION = 429  # Luxurious weighted motion: 650ms
    EXPANDED_WIDTH = 200
    STAGGER_DELAY = 200 # ms between items
    
    # Debug flag for alignment visualization
    DEBUG_ALIGNMENT = False
    
    # Expansion directions (currently supports LEFT expansion as per spec)
    LEFT = 'left'
    
    def __init__(self, main_icon_path=None, parent=None):
        super().__init__(parent)
        
        # State
        self._is_expanded = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Allow key events for debug toggles
        self._is_hovered = False
        self._is_solid_style = False # False = Ghost, True = Solid
        self._active_item_id = None
        self._items = [] # List of item widgets
        self._item_animations = [] # Keep animations alive to prevent GC
        self._main_icon_path = main_icon_path
        self._is_dark = True
        self._current_pixmap = None
        self._current_icon = None
        self._current_icon_grey = None  # Grey-tinted icon for inactive state
        
        # UI Setup
        self._setup_ui()
        
        # Timers
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(self.EXPAND_DELAY_MS)
        self._hover_timer.timeout.connect(self._expand)
        
        self._collapse_timer = QTimer(self)
        self._collapse_timer.setSingleShot(True)
        self._collapse_timer.setInterval(100)
        self._collapse_timer.timeout.connect(self._collapse)
        
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.setInterval(150)
        self._flash_timer.timeout.connect(self._reset_flash)
        self._is_flashing = False

        # Base Styling
        self.setFixedHeight(self.COLLAPSED_SIZE)
        self.setMinimumWidth(self.COLLAPSED_SIZE)
        self.setMaximumWidth(self.COLLAPSED_SIZE)
        
        # Animation Config
        self.anim_easing = 'InOutCirc'
        self.anim_amplitude = 0.00  # Used as overshoot for OutBack
        self.anim_period = 0.00
        
        # Width animation
        self._width_anim = QPropertyAnimation(self, b"animWidth", self)
        self._width_driver = AnimationDriver(self._width_anim, duration=self.ANIMATION_DURATION, easing=self.anim_easing)
        self._width_driver.overshoot = self.anim_amplitude
        self._width_driver.period = self.anim_period
        
        self._update_main_icon()

    @pyqtProperty(int)
    def animWidth(self):
        return self.width()

    @animWidth.setter
    def animWidth(self, w):
        self.setFixedWidth(w)
        self.update()


            
    def toggle_dev_panel(self):
        if not hasattr(self, '_param_panel'):
            from client.gui.effects.dev_panel import DevPanel
            
            easing_styles = [
                'OutBack', 'OutElastic', 'OutBounce', 
                'InOutQuad', 'OutCubic', 'Linear', 
                'OutExpo', 'InOutElastic'
            ]
            
            params_layout = {
                'COLLAPSED_SIZE': (20, 100, 2),
                'EXPANDED_WIDTH': (100, 400, 10),
                'EXPAND_DELAY_MS': (0, 1000, 50),
                'STAGGER_DELAY': (0, 200, 10),
            }

            params_anim = {
                'anim_easing': (list(AnimationDriver.EASING_MAP.keys()),), 
                'anim_amplitude': (0.0, 5.0, 0.1), # Controls Overshoot/Elasticity
                'anim_period': (0.0, 2.0, 0.05),   # Controls Elastic Period
                'ANIMATION_DURATION': (100, 2000, 50),
            }
            
            # Helper to update dependent timers/state
            def on_change():
                self.setFixedHeight(self.COLLAPSED_SIZE)
                self.setMinimumWidth(self.COLLAPSED_SIZE)
                self._hover_timer.setInterval(self.EXPAND_DELAY_MS)
                
                # Push changes to driver
                self._width_driver.duration = self.ANIMATION_DURATION
                self._width_driver.easing_type = self.anim_easing
                self._width_driver.overshoot = self.anim_amplitude
                self._width_driver.amplitude = self.anim_amplitude # For Bounce/Elastic
                self._width_driver.period = self.anim_period
                
                self.update()
            
            source_file = r"v:\_MY_APPS\ImgApp_1\client\gui\custom_widgets.py"
            
            self._param_panel = DevPanel(title="Inspector - Morphing Button")
            self._param_panel.add_section(
                self, params_layout, "Layout & Timing", source_file, on_change
            )
            self._param_panel.add_section(
                self, params_anim, "Animation Control", source_file, on_change
            )
            
        if self._param_panel.isVisible():
            self._param_panel.hide()
        else:
            self._param_panel.show()
            self._param_panel.raise_()
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F12:
            self.toggle_dev_panel()
            return
        super().keyPressEvent(event)
        
    def _setup_ui(self):
        # Menu Container
        self._menu_container = QWidget(self)
        self._menu_container.setVisible(False)
        self._menu_layout = QHBoxLayout(self._menu_container)
        self._menu_layout.setContentsMargins(8, 0, 48, 0) # Right margin to avoid overlap with icon pos
        self._menu_layout.setSpacing(8)
        
        self._menu_container.setParent(self)
        self._icon_opacity_val = 1.0
        
    @pyqtProperty(float)
    def iconOpacity(self):
        return self._icon_opacity_val

    @iconOpacity.setter
    def iconOpacity(self, val):
        self._icon_opacity_val = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        curr_width = self.width()
        curr_height = self.height()
        radius = curr_height / 2
        
        # Background color
        bg_color = QColor("#2196F3") if self._is_solid_style else QColor(255, 255, 255, 12)
        
        # Border
        border_color = QColor(255, 255, 255, 25)
        if self._is_flashing:
            border_color = QColor(255, 255, 255, 255)
        elif not self._is_solid_style:
            border_color = QColor(255, 255, 255, 75)
            
        painter.setPen(QPen(border_color, 1.5 if self._is_flashing else 1))
        painter.setBrush(QBrush(bg_color))
        
        # Use integer coordinates to be absolutely safe with PyQt6 overloads.
        # This fixes the TypeError: argument 1 has unexpected type 'float'
        # Fix clipping: inset by 1px so border stroke (width 1-1.5) is inside bounds
        painter.drawRoundedRect(1, 1, int(curr_width)-2, int(curr_height)-2, int(radius), int(radius))

        # DEBUG: Draw red dot at center to verify alignment
        if self.DEBUG_ALIGNMENT:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("red"))
            cx = int(curr_width / 2)
            cy = int(curr_height / 2)
            # Draw ellipse centered on (cx, cy) - need to offset by radius
            painter.drawEllipse(cx - 3, cy - 3, 6, 6)
        
        
        # Draw Main Icon using QIcon.paint() for sharp, centered rendering
        if self._current_icon and not self._current_icon.isNull() and self._icon_opacity_val > 0:
            painter.setOpacity(self._icon_opacity_val)
            
            # Calculate icon area - anchored to right when expanded
            icon_x = 0
            if self._is_expanded or self.width() > self.COLLAPSED_SIZE:
                icon_x = self.width() - self.COLLAPSED_SIZE
            
            # The target rect for the icon - matches the visible circle area (1px border inset)
            # The circle is drawn at (1,1) with size (COLLAPSED_SIZE-2, COLLAPSED_SIZE-2)
            # so we center the icon within that same visible area
            target_rect = QRect(icon_x + 1, 1, self.COLLAPSED_SIZE - 2, self.COLLAPSED_SIZE - 2)
            
            # Calculate icon size as 66% of button
            icon_size = int(self.COLLAPSED_SIZE * 0.66)
            if icon_size % 2 == 1:
                icon_size += 1
            
            # Center the icon rect within target_rect
            icon_rect = QRect(
                target_rect.x() + (target_rect.width() - icon_size) // 2,
                target_rect.y() + (target_rect.height() - icon_size) // 2,
                icon_size,
                icon_size
            )
            
            # DEBUG: Draw semi-transparent blue background for icon area
            if self.DEBUG_ALIGNMENT:
                painter.setBrush(QColor(0, 0, 255, 150))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(icon_rect)
            
            # Draw icon using pixmap at explicit coordinates for perfect centering
            # ALWAYS use original SVG-based icon to get pixmap (preserves proper scaling)
            # Apply grey tint at paint time if in ghost/inactive state
            
            apply_grey_tint = not self._is_solid_style
            
            # Get pixmap from ORIGINAL icon (not the pre-created grey one)
            pixmap = self._current_icon.pixmap(icon_size, icon_size)
            if not pixmap.isNull():
                # Apply grey tinting at paint time if needed
                if apply_grey_tint:
                    # Create a grey-tinted copy of the pixmap
                    # CRITICAL: Preserve devicePixelRatio for proper DPI scaling
                    grey_pixmap = QPixmap(pixmap.size())
                    grey_pixmap.setDevicePixelRatio(pixmap.devicePixelRatio())
                    grey_pixmap.fill(Qt.GlobalColor.transparent)
                    tint_painter = QPainter(grey_pixmap)
                    tint_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    tint_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    tint_painter.drawPixmap(0, 0, pixmap)
                    tint_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                    tint_painter.fillRect(grey_pixmap.rect(), QColor(136, 136, 136))
                    tint_painter.end()
                    pixmap = grey_pixmap
                
                # Draw pixmap scaled to icon_rect - this handles DPI scaling properly
                # The pixmap may be larger due to devicePixelRatio, but drawPixmap with QRect scales it
                painter.drawPixmap(icon_rect, pixmap)
            
            painter.setOpacity(1.0)
            
    def set_main_icon(self, icon_path):
        self._main_icon_path = icon_path
        self._update_main_icon()
        
    def _update_main_icon(self):
        if self._main_icon_path:
            abs_path = get_resource_path(self._main_icon_path)
            if os.path.exists(abs_path):
                # Store the icon for direct painting (same method as menu buttons)
                self._current_icon = QIcon(abs_path)
                self._current_pixmap = None  # Clear pixmap, we'll use icon directly
                
                # Create grey-tinted icon for inactive/ghost state
                icon_size = int(self.COLLAPSED_SIZE * 0.66)
                if icon_size % 2 == 1:
                    icon_size += 1
                pixmap = self._current_icon.pixmap(icon_size, icon_size)
                if not pixmap.isNull():
                    grey_pixmap = QPixmap(pixmap.size())
                    grey_pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(grey_pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    painter.drawPixmap(0, 0, pixmap)
                    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                    # Use a medium grey (#888888) for inactive state
                    painter.fillRect(grey_pixmap.rect(), QColor(136, 136, 136))
                    painter.end()
                    self._current_icon_grey = QIcon(grey_pixmap)
                else:
                    self._current_icon_grey = None
                    
                self.update()
            
    def add_menu_item(self, item_id, icon_path, tooltip=""):
        """Add an icon-based item to the expansion menu"""
        btn = QPushButton()
        btn.setFixedSize(32, 32)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Icon
        if icon_path:
            abs_path = get_resource_path(icon_path)
            if os.path.exists(abs_path):
                btn.setIcon(QIcon(abs_path))
                btn.setIconSize(QSize(20, 20))
        
        # Styling for icon buttons
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        
        # IMPORTANT: Use default arg to capture item_id by VALUE, not reference
        # This fixes the closure bug where all buttons would emit the last item_id
        btn.clicked.connect(lambda checked=False, iid=item_id: self._on_item_clicked(iid))
        self._menu_layout.addWidget(btn)
        self._items.append(btn)
        
        op = QGraphicsOpacityEffect(btn)
        btn.setGraphicsEffect(op)
        op.setOpacity(0)
        
    def set_style_solid(self, is_solid):
        if self._is_solid_style != is_solid:
            self._is_solid_style = is_solid
            self._update_main_icon()
            self.update()
            self.styleChanged.emit(is_solid)
            
    @property
    def is_solid(self):
        return self._is_solid_style
        
    def flash_border(self):
        self._is_flashing = True
        self.update()
        self._flash_timer.start()
        
    def _reset_flash(self):
        self._is_flashing = False
        self.update()

    def update_theme(self, is_dark):
        self._is_dark = is_dark
        self._update_main_icon()
        self.update()

    def _on_item_clicked(self, item_id):
        type_map = {0: "IMAGE", 1: "VIDEO", 2: "LOOP"}
        print(f"[DEBUG_INTERNAL] MorphingButton item clicked. ID={item_id} ({type_map.get(item_id, 'UNKNOWN')})")
        self._active_item_id = item_id
        self.itemClicked.emit(item_id)
        self._collapse()
        self.flash_border()
        
    def enterEvent(self, event):
        super().enterEvent(event)
        self._is_hovered = True
        self._collapse_timer.stop()
        if not self._is_expanded:
            self._hover_timer.start()
            
    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._is_hovered = False
        self._hover_timer.stop()
        if self._is_expanded:
            self._collapse_timer.start()
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Icon positioning handled in paintEvent now
        
        self._menu_container.resize(self.width(), self.height())
            
    def _expand(self):
        if self._is_expanded: return
        self._is_expanded = True
        self.raise_() # Ensure button is on top of siblings when expanding
        
        # 1. Expand Width
        menu_width = self._menu_layout.sizeHint().width()
        target_width = max(160, menu_width + 48) # 48 space for the status icon at the end
        
        self._width_anim.setStartValue(self.COLLAPSED_SIZE)
        self._width_anim.setEndValue(target_width)
        self._width_anim.start()
        
        # 2. Main Icon Shift (Fade slightly or just stay at right)
        self.icon_anim_op = QPropertyAnimation(self, b"iconOpacity")
        self.icon_anim_op.setDuration(300)
        self.icon_anim_op.setStartValue(1.0)
        self.icon_anim_op.setEndValue(0.4) # Keep it visible but faded
        self.icon_anim_op.start()
        
        # 3. Menu Items In
        self._menu_container.setVisible(True)
        self._item_animations.clear()  # Clear previous animations
        for i, btn in enumerate(self._items):
            anim = QPropertyAnimation(btn.graphicsEffect(), b"opacity")
            anim.setDuration(250)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            self._item_animations.append(anim)  # Keep reference to prevent GC
            QTimer.singleShot(i * self.STAGGER_DELAY, anim.start)
            
        self.expanded.emit(True)
        
    def _collapse(self):
        if not self._is_expanded: return
        if self._is_hovered: return
        self._is_expanded = False
        
        # 1. Collapse Width
        self._width_anim.setStartValue(self.width())
        self._width_anim.setEndValue(self.COLLAPSED_SIZE)
        self._width_anim.finished.connect(self._on_collapse_finished)
        self._width_anim.start()
        
        # 2. Main Icon Back
        self.icon_anim_op.setStartValue(0.4)
        self.icon_anim_op.setEndValue(1.0)
        self.icon_anim_op.start()
        
        # 3. Hide Menu
        self._menu_container.setVisible(False)
        for btn in self._items:
            btn.graphicsEffect().setOpacity(0)
            
        self.expanded.emit(False)

    def _on_collapse_finished(self):
        try:
            self._width_anim.finished.disconnect(self._on_collapse_finished)
        except: pass
        if not self._is_expanded:
            self.setFixedWidth(self.COLLAPSED_SIZE)
            self.update()









