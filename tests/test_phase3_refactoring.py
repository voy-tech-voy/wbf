"""
Unit Tests for Phase 3+ Refactoring Components
===============================================
Tests for new extracted components:
- Tab components (BaseTab, ImageTab, VideoTab, LoopTab)
- ConversionParams and Builder
- ThemeCoordinator
"""

import sys
import pytest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, 'V:/_MY_APPS/ImgApp_1')


class TestBaseTab:
    """Tests for the BaseTab abstract class."""
    
    def test_base_tab_import(self):
        """Test BaseTab can be imported."""
        from client.gui.tabs.base_tab import BaseTab
        assert BaseTab is not None
    
    def test_base_tab_has_required_abstract_methods(self):
        """Test BaseTab defines required abstract methods."""
        from client.gui.tabs.base_tab import BaseTab
        import inspect
        
        # Check abstract methods exist
        assert hasattr(BaseTab, 'setup_ui')
        assert hasattr(BaseTab, 'get_params')
        assert hasattr(BaseTab, 'update_theme')
    
    def test_base_tab_has_params_changed_signal(self):
        """Test BaseTab has params_changed signal."""
        from client.gui.tabs.base_tab import BaseTab
        
        assert hasattr(BaseTab, 'params_changed')


class TestImageTab:
    """Tests for the ImageTab component."""
    
    def test_image_tab_import(self):
        """Test ImageTab can be imported."""
        from client.gui.tabs.image_tab import ImageTab
        assert ImageTab is not None
    
    def test_image_tab_inherits_base_tab(self):
        """Test ImageTab inherits from BaseTab."""
        from client.gui.tabs.image_tab import ImageTab
        from client.gui.tabs.base_tab import BaseTab
        
        assert issubclass(ImageTab, BaseTab)
    
    @patch('client.gui.tabs.image_tab.CommandGroup')
    @patch('client.gui.tabs.image_tab.FormatButtonRow')
    @patch('client.gui.tabs.image_tab.RotationButtonRow')
    def test_image_tab_get_params_returns_dict(self, *mocks):
        """Test get_params returns a dictionary."""
        from client.gui.tabs.image_tab import ImageTab
        
        with patch.object(ImageTab, 'setup_ui'):
            tab = ImageTab.__new__(ImageTab)
            tab._layout = MagicMock()
            tab._is_dark_theme = True
            tab._focus_callback = lambda: None
            
            # Mock required attributes
            tab.format = MagicMock()
            tab.format.currentFormat.return_value = 'WebP'
            tab.quality = MagicMock()
            tab.quality.value.return_value = 80
            tab.multiple_qualities = MagicMock()
            tab.multiple_qualities.isChecked.return_value = False
            tab.quality_variants = MagicMock()
            tab.quality_variants.text.return_value = ''
            tab.max_size_spinbox = MagicMock()
            tab.max_size_spinbox.value.return_value = 0.2
            tab.max_size_spinbox.isVisible.return_value = False
            tab.auto_resize_checkbox = MagicMock()
            tab.auto_resize_checkbox.isChecked.return_value = True
            tab.resize_mode = MagicMock()
            tab.resize_mode.currentText.return_value = 'No resize'
            tab.resize_value = MagicMock()
            tab.resize_value.value.return_value = 720
            tab.multiple_resize = MagicMock()
            tab.multiple_resize.isChecked.return_value = False
            tab.resize_variants = MagicMock()
            tab.resize_variants.text.return_value = ''
            tab.rotation_angle = MagicMock()
            tab.rotation_angle.currentAngle.return_value = 'No rotation'
            
            params = tab.get_params()
            
            assert isinstance(params, dict)
            assert params['type'] == 'image'
            assert params['format'] == 'WebP'


class TestVideoTab:
    """Tests for the VideoTab component."""
    
    def test_video_tab_import(self):
        """Test VideoTab can be imported."""
        from client.gui.tabs.video_tab import VideoTab
        assert VideoTab is not None
    
    def test_video_tab_inherits_base_tab(self):
        """Test VideoTab inherits from BaseTab."""
        from client.gui.tabs.video_tab import VideoTab
        from client.gui.tabs.base_tab import BaseTab
        
        assert issubclass(VideoTab, BaseTab)


class TestLoopTab:
    """Tests for the LoopTab component."""
    
    def test_loop_tab_import(self):
        """Test LoopTab can be imported."""
        from client.gui.tabs.loop_tab import LoopTab
        assert LoopTab is not None
    
    def test_loop_tab_inherits_base_tab(self):
        """Test LoopTab inherits from BaseTab."""
        from client.gui.tabs.loop_tab import LoopTab
        from client.gui.tabs.base_tab import BaseTab
        
        assert issubclass(LoopTab, BaseTab)
    
    def test_loop_tab_has_format_changed_signal(self):
        """Test LoopTab has format_changed signal for GIF/WebM switching."""
        from client.gui.tabs.loop_tab import LoopTab
        
        assert hasattr(LoopTab, 'format_changed')


class TestConversionParams:
    """Tests for the ConversionParams dataclass."""
    
    def test_conversion_params_import(self):
        """Test ConversionParams can be imported."""
        from client.gui.builders.conversion_params import ConversionParams
        assert ConversionParams is not None
    
    def test_conversion_type_enum(self):
        """Test ConversionType enum has correct values."""
        from client.gui.builders.conversion_params import ConversionType
        
        assert ConversionType.IMAGE.value == 'image'
        assert ConversionType.VIDEO.value == 'video'
        assert ConversionType.LOOP.value == 'loop'
    
    def test_resize_mode_enum(self):
        """Test ResizeMode enum has correct values."""
        from client.gui.builders.conversion_params import ResizeMode
        
        assert ResizeMode.NONE.value == 'No resize'
        assert ResizeMode.BY_WIDTH.value == 'By width (pixels)'
    
    def test_conversion_params_to_dict(self):
        """Test ConversionParams.to_dict() returns valid dictionary."""
        from client.gui.builders.conversion_params import ConversionParams, ConversionType
        
        params = ConversionParams(conversion_type=ConversionType.IMAGE)
        result = params.to_dict()
        
        assert isinstance(result, dict)
        assert result['type'] == 'image'
    
    def test_conversion_params_immutable(self):
        """Test ConversionParams is immutable (frozen dataclass)."""
        from client.gui.builders.conversion_params import ConversionParams, ConversionType
        
        params = ConversionParams(conversion_type=ConversionType.IMAGE)
        
        with pytest.raises(Exception):  # FrozenInstanceError
            params.quality = 50


class TestConversionParamsBuilder:
    """Tests for the ConversionParamsBuilder class."""
    
    def test_builder_import(self):
        """Test ConversionParamsBuilder can be imported."""
        from client.gui.builders.conversion_params import ConversionParamsBuilder
        assert ConversionParamsBuilder is not None
    
    def test_builder_fluent_interface(self):
        """Test builder supports fluent interface (method chaining)."""
        from client.gui.builders.conversion_params import ConversionParamsBuilder, ConversionType
        
        builder = ConversionParamsBuilder()
        result = builder.set_type(ConversionType.IMAGE)
        
        assert result is builder  # Returns self for chaining
    
    def test_builder_builds_params(self):
        """Test builder creates valid ConversionParams."""
        from client.gui.builders.conversion_params import (
            ConversionParamsBuilder, ConversionParams, ConversionType
        )
        
        params = (ConversionParamsBuilder()
            .set_type(ConversionType.IMAGE)
            .set_image_format('WebP')
            .set_quality(80)
            .build())
        
        assert isinstance(params, ConversionParams)
        assert params.conversion_type == ConversionType.IMAGE
        assert params.image_format == 'WebP'
        assert params.quality == 80
    
    def test_builder_requires_type(self):
        """Test builder raises error if type not set."""
        from client.gui.builders.conversion_params import ConversionParamsBuilder
        
        builder = ConversionParamsBuilder()
        
        with pytest.raises(ValueError, match="conversion_type is required"):
            builder.build()
    
    def test_builder_build_dict(self):
        """Test builder can output dictionary for backward compatibility."""
        from client.gui.builders.conversion_params import ConversionParamsBuilder, ConversionType
        
        result = (ConversionParamsBuilder()
            .set_type(ConversionType.VIDEO)
            .set_video_codec('MP4 (H.264)')
            .build_dict())
        
        assert isinstance(result, dict)
        assert result['type'] == 'video'


class TestThemeCoordinator:
    """Tests for the ThemeCoordinator class."""
    
    def test_coordinator_import(self):
        """Test ThemeCoordinator can be imported."""
        from client.gui.utils.theme_coordinator import ThemeCoordinator
        assert ThemeCoordinator is not None
    
    def test_coordinator_initialization(self):
        """Test coordinator initializes with correct defaults."""
        from client.gui.utils.theme_coordinator import ThemeCoordinator
        
        coord = ThemeCoordinator()
        assert coord.is_dark_mode == True
        assert coord.component_count == 0
    
    def test_coordinator_register_component(self):
        """Test registering a component."""
        from client.gui.utils.theme_coordinator import ThemeCoordinator
        
        coord = ThemeCoordinator()
        mock_component = MagicMock()
        
        coord.register(mock_component)
        
        assert coord.component_count == 1
    
    def test_coordinator_unregister_component(self):
        """Test unregistering a component."""
        from client.gui.utils.theme_coordinator import ThemeCoordinator
        
        coord = ThemeCoordinator()
        mock_component = MagicMock()
        
        coord.register(mock_component)
        coord.unregister(mock_component)
        
        assert coord.component_count == 0
    
    def test_coordinator_set_dark_mode_updates_components(self):
        """Test set_dark_mode updates all registered components."""
        from client.gui.utils.theme_coordinator import ThemeCoordinator
        
        coord = ThemeCoordinator(is_dark=True)
        mock_component = MagicMock()
        mock_component.update_theme = MagicMock()
        
        coord.register(mock_component)
        coord.set_dark_mode(False)
        
        mock_component.update_theme.assert_called_once_with(False)
    
    def test_coordinator_toggle_theme(self):
        """Test toggle_theme switches between modes."""
        from client.gui.utils.theme_coordinator import ThemeCoordinator
        
        coord = ThemeCoordinator(is_dark=True)
        
        result = coord.toggle_theme()
        assert result == False
        assert coord.is_dark_mode == False
        
        result = coord.toggle_theme()
        assert result == True
        assert coord.is_dark_mode == True
    
    def test_coordinator_repr(self):
        """Test coordinator has readable repr."""
        from client.gui.utils.theme_coordinator import ThemeCoordinator
        
        coord = ThemeCoordinator(is_dark=True)
        coord.register(MagicMock())
        
        repr_str = repr(coord)
        assert 'dark' in repr_str
        assert 'components=1' in repr_str


class TestTabsPackageExports:
    """Tests for the tabs package exports."""
    
    def test_all_tabs_exported_from_package(self):
        """Test all tab classes are exported from package."""
        from client.gui.tabs import BaseTab, ImageTab, VideoTab, LoopTab
        
        assert BaseTab is not None
        assert ImageTab is not None
        assert VideoTab is not None
        assert LoopTab is not None


class TestBuildersPackageExports:
    """Tests for the builders package exports."""
    
    def test_builders_exported_from_package(self):
        """Test builder classes are exported from package."""
        from client.gui.builders import ConversionParams, ConversionParamsBuilder
        
        assert ConversionParams is not None
        assert ConversionParamsBuilder is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
