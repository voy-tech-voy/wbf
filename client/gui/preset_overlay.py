from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                             QPushButton, QFrame, QGridLayout, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPalette

from client.core.preset_registry import PresetRegistry
from client.gui.preset_card import PresetCard
from client.gui.theme_variables import ThemeVariables

class PresetOverlay(QWidget):
    """
    Full-window overlay displayed during Drag & Drop operations.
    Contains filtering tabs and a grid of PresetCards.
    """
    preset_selected = pyqtSignal(object) # Emits PresetObject on drop
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PresetOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False) # Must catch mouse events
        self.setAcceptDrops(True) # It accepts drops physically
        
        # Styles
        self.setStyleSheet("""
            QWidget#PresetOverlay {
                background-color: rgba(18, 18, 18, 0.95); /* High opacity matte */
            }
            QPushButton.FilterTab {
                background: transparent;
                border: none;
                color: #888;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 16px;
                border-bottom: 2px solid transparent;
            }
            QPushButton.FilterTab:hover {
                color: #BBB;
            }
            QPushButton.FilterTab[active="true"] {
                color: #FFF;
                border-bottom: 2px solid #00E0FF;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)

        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 60, 40, 40)
        self.main_layout.setSpacing(20)
        
        # 1. Header (Filter Tabs)
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        self.tabs = {}
        for category in ["ALL", "SOCIAL", "WEB", "UTILS"]:
            btn = QPushButton(category)
            btn.setProperty("class", "FilterTab")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=category: self.set_filter(c))
            header_layout.addWidget(btn)
            self.tabs[category] = btn
            
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)
        
        # 2. Grid Container (Scrollable)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(20)
        self.scroll.setWidget(self.scroll_content)
        
        self.main_layout.addWidget(self.scroll)
        
        # Initialize
        self.cards = [] # List of (card_widget, preset_obj)
        self.current_filter = "ALL"
        self.populate_grid()
        self.set_filter("ALL")
        
        # Animation setup
        self.opacity_effect = None # To be implemented if using QGraphicsOpacityEffect, or just use window opacity if possible? 
        # Since this is a child widget, we can't easily animate opacity of the whole widget tree without GraphicsEffect.
        # For MVP, we toggle visibility.
        self.hide()

    def populate_grid(self):
        """Create cards for all presets"""
        presets = PresetRegistry.get_all_presets()
        for p in presets:
            card = PresetCard(p)
            self.cards.append(card)
            # Layout is handled in set_filter logic to allow re-flow
            
    def set_filter(self, category):
        """Filter visible cards and re-flow grid"""
        self.current_filter = category
        
        # Update Tab Styles
        for name, btn in self.tabs.items():
            btn.setProperty("active", name == category)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
        # Clear Grid Layout
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        # Re-add matching cards
        row, col = 0, 0
        cols = 5 # Fixed columns for now, or dynamic calculation based on width?
        # For MVP, let's settle on a wide grid.
        
        visible_cards = [c for c in self.cards if category == "ALL" or c.preset.category == category]
        
        for card in visible_cards:
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1
                
    def hit_test(self, global_pos):
        """
        Check if global_pos (from drag) is over any card.
        Highlight the card if found.
        Return the card or None.
        """
        # Convert global to overlay logic
        # We need to find which card widget is under the mouse.
        # Since overlay covers everything, mapFromGlobal works.
        overlay_pos = self.mapFromGlobal(global_pos)
        start_widget = self.childAt(overlay_pos)
        
        # Traverse up to find PresetCard
        target_card = None
        curr = start_widget
        while curr:
            if isinstance(curr, PresetCard):
                target_card = curr
                break
            curr = curr.parent()
            if curr == self: break
            
        # Update states
        for card in self.cards:
            if card == target_card:
                card.set_active_state(True)
            else:
                card.set_active_state(False)
                
        return target_card
