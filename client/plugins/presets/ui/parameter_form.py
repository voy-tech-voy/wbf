"""
Presets Plugin - Parameter Form

Dynamically generates UI widgets from preset parameter definitions.
Supports visibility rules evaluated via Jinja2.
"""
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QSlider, QComboBox, QPushButton,
    QButtonGroup, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from jinja2 import Environment, StrictUndefined

from client.plugins.presets.logic.models import ParameterDefinition, ParameterType


class SegmentedPill(QWidget):
    """Segmented button group for multi-option selection"""
    
    value_changed = pyqtSignal(str)
    
    def __init__(self, options: List[str], default: str = None, parent=None):
        super().__init__(parent)
        self._options = options
        self._current_value = default or (options[0] if options else "")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._buttons: Dict[str, QPushButton] = {}
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        
        for i, opt in enumerate(options):
            btn = QPushButton(opt)
            btn.setCheckable(True)
            btn.setChecked(opt == self._current_value)
            btn.clicked.connect(lambda checked, o=opt: self._on_button_clicked(o))
            
            # Styling
            btn.setMinimumWidth(60)
            btn.setMinimumHeight(32)
            
            self._buttons[opt] = btn
            self._button_group.addButton(btn, i)
            layout.addWidget(btn)
        
        self._apply_styles()
    
    def _on_button_clicked(self, option: str):
        self._current_value = option
        self.value_changed.emit(option)
        self._apply_styles()
    
    def _apply_styles(self):
        for opt, btn in self._buttons.items():
            if opt == self._current_value:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #00E0FF;
                        color: #000000;
                        border: none;
                        font-weight: bold;
                        border-radius: 4px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2a2a2a;
                        color: #888888;
                        border: 1px solid #444444;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #3a3a3a;
                        color: #ffffff;
                    }
                """)
    
    def value(self) -> str:
        return self._current_value
    
    def setValue(self, val: str):
        if val in self._buttons:
            self._current_value = val
            self._buttons[val].setChecked(True)
            self._apply_styles()


class ParameterForm(QWidget):
    """
    Dynamic form that renders preset parameters as Qt widgets.
    
    Supports:
    - toggle → QCheckBox
    - slider → QSlider + QLabel
    - segmented_pill → SegmentedPill
    - dropdown → QComboBox
    
    Visibility rules are evaluated via Jinja2 expressions.
    """
    
    values_changed = pyqtSignal(dict)  # Emits current param values
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parameters: List[ParameterDefinition] = []
        self._meta: Dict[str, Any] = {}
        self._widgets: Dict[str, QWidget] = {}
        self._containers: Dict[str, QWidget] = {}  # For visibility control
        self._jinja_env = Environment(undefined=StrictUndefined)
        
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(12)
        
        self.setStyleSheet("""
            QLabel { color: #F5F5F7; font-size: 12px; }
            QCheckBox { color: #F5F5F7; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """)
    
    def set_parameters(self, params: List[ParameterDefinition], meta: Dict[str, Any] = None):
        """
        Build the form from parameter definitions.
        
        Args:
            params: List of ParameterDefinition from preset
            meta: Media metadata for visibility rule evaluation
        """
        self._parameters = params
        self._meta = meta or {}
        self._clear_form()
        
        for param in params:
            container = self._create_parameter_widget(param)
            self._containers[param.id] = container
            self._layout.addWidget(container)
        
        # Spacer
        self._layout.addStretch()
        
        # Initial visibility evaluation
        self._update_visibility()
    
    def _clear_form(self):
        """Remove all widgets from the form."""
        self._widgets.clear()
        self._containers.clear()
        
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _create_parameter_widget(self, param: ParameterDefinition) -> QWidget:
        """Create a widget container for a parameter."""
        container = QFrame()
        container.setObjectName(f"param_{param.id}")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Label
        label = QLabel(param.label)
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        # Tooltip
        if param.tooltip:
            label.setToolTip(param.tooltip)
        
        # Widget based on type
        widget = None
        
        if param.type == ParameterType.TOGGLE:
            widget = QCheckBox()
            widget.setChecked(bool(param.default))
            widget.stateChanged.connect(lambda: self._on_value_changed())
            
        elif param.type == ParameterType.SLIDER:
            row = QHBoxLayout()
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(int(param.min_value or 0))
            slider.setMaximum(int(param.max_value or 100))
            slider.setValue(int(param.default or 50))
            
            value_label = QLabel(str(slider.value()))
            value_label.setMinimumWidth(30)
            slider.valueChanged.connect(lambda v: value_label.setText(str(v)))
            slider.valueChanged.connect(lambda: self._on_value_changed())
            
            row.addWidget(slider, 1)
            row.addWidget(value_label)
            
            row_widget = QWidget()
            row_widget.setLayout(row)
            widget = row_widget
            # Store slider for value retrieval
            widget._slider = slider
            
        elif param.type == ParameterType.SEGMENTED_PILL:
            widget = SegmentedPill(param.options, str(param.default))
            widget.value_changed.connect(lambda: self._on_value_changed())
            
        elif param.type == ParameterType.DROPDOWN:
            widget = QComboBox()
            widget.addItems(param.options)
            if param.default in param.options:
                widget.setCurrentText(str(param.default))
            widget.currentTextChanged.connect(lambda: self._on_value_changed())
        
        if widget:
            layout.addWidget(widget)
            self._widgets[param.id] = widget
        
        return container
    
    def _on_value_changed(self):
        """Handle any parameter value change."""
        self._update_visibility()
        self.values_changed.emit(self.get_values())
    
    def _update_visibility(self):
        """Evaluate visibility rules for all parameters."""
        current_values = self.get_values()
        context = {**current_values, 'meta': self._meta}
        
        for param in self._parameters:
            if param.visibility_rule and param.id in self._containers:
                visible = self._evaluate_visibility_rule(param.visibility_rule, context)
                self._containers[param.id].setVisible(visible)
    
    def _evaluate_visibility_rule(self, rule: str, context: Dict) -> bool:
        """
        Evaluate a visibility rule using Jinja2.
        
        Args:
            rule: Jinja2 boolean expression (e.g., "not (allow_rotate and meta.is_landscape)")
            context: Variables for evaluation
        """
        try:
            template_str = f"{{% if {rule} %}}1{{% else %}}0{{% endif %}}"
            template = self._jinja_env.from_string(template_str)
            result = template.render(context)
            return result.strip() == "1"
        except Exception as e:
            print(f"[ParameterForm] Visibility rule error: {e}")
            return True  # Default to visible on error
    
    def get_values(self) -> Dict[str, Any]:
        """Get current values of all parameters."""
        values = {}
        
        for param in self._parameters:
            widget = self._widgets.get(param.id)
            if not widget:
                values[param.id] = param.default
                continue
            
            if param.type == ParameterType.TOGGLE:
                values[param.id] = widget.isChecked()
            elif param.type == ParameterType.SLIDER:
                values[param.id] = widget._slider.value() if hasattr(widget, '_slider') else param.default
            elif param.type == ParameterType.SEGMENTED_PILL:
                values[param.id] = widget.value()
            elif param.type == ParameterType.DROPDOWN:
                values[param.id] = widget.currentText()
            else:
                values[param.id] = param.default
        
        return values
    
    def set_meta(self, meta: Dict[str, Any]):
        """Update meta context and re-evaluate visibility."""
        self._meta = meta
        self._update_visibility()
